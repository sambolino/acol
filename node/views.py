import os.path
import json
import uuid
import math
import matplotlib
import logging

matplotlib.use('Agg')

import matplotlib.pyplot as plt

from django.db.models import Q
from django.conf import settings
from django.template.loader import get_template
from django.http import FileResponse, Http404, HttpResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse

from node.models import *
from node.forms import *
from node.gpr import predict as predict_with_gpr


logger = logging.getLogger()


# ----------------------------------------------------------------------
# Private generic helpers
# ----------------------------------------------------------------------

def _json_response(data, status=200):
    return HttpResponse(json.dumps(data), content_type='application/json', status=status)


def _get_collision_type(coll_iaea_code):
    return CollisionType.objects.get(iaea_code=coll_iaea_code)


def _species_dict(species_queryset):
    data = {}

    for species in species_queryset:
        data[species.inchikey] = str(species)

    return data


def _first_queryset_item(queryset):
    try:
        return queryset[0]
    except IndexError:
        return None


# ----------------------------------------------------------------------
# Private search/combo helpers
# ----------------------------------------------------------------------

def _products_for_collision_type(coll_type):
    return Species.objects.filter(
        speciesstate__products__collision_type=coll_type
    ).distinct()


def _reactants_for_collision_type(coll_type):
    return Species.objects.filter(
        speciesstate__reactants__collision_type=coll_type
    ).distinct()


def _atoms_for_collision_type(coll_type, neutral_only=False):
    products = Atom.objects.filter(
        speciesstate__products__collision_type=coll_type
    )

    reactants = Atom.objects.filter(
        speciesstate__reactants__collision_type=coll_type
    )

    if neutral_only:
        products = products.filter(ion_charge=0)
        reactants = reactants.filter(ion_charge=0)

    return (products | reactants).distinct()


def _tabdata_for_collision_and_species(coll_iaea_code, species_inchikey):
    return TabulatedData.objects.filter(
        (
            Q(collision__reactants__species__inchikey=species_inchikey) |
            Q(collision__products__species__inchikey=species_inchikey)
        ) &
        Q(collision__collision_type__iaea_code=coll_iaea_code)
    )


def _tabdata_first_x_values(tabdata):
    x_axis = tabdata.first_x()

    if not x_axis or not x_axis.data_values:
        return []

    return x_axis.data_values.split()

def _state_species_name(state):
    if state and state.species:
        return state.species.name or ""

    return ""


def _collision_species_names(collision):
    names = []

    if not collision:
        return names

    for reactant in collision.reactants.all():
        name = _state_species_name(reactant)
        if name:
            names.append(name)

    for product in collision.products.all():
        name = _state_species_name(product)
        if name:
            names.append(name)

    return names


# ----------------------------------------------------------------------
# Private Explore helpers
# ----------------------------------------------------------------------

def _shorten_text(value, max_length=72):
    value = (value or "").strip()

    if len(value) <= max_length:
        return value

    return "%s..." % value[:max_length - 3].rstrip()


def _normalize_doi(doi):
    doi = (doi or "").strip()

    if doi.lower().startswith("doi:"):
        doi = doi[4:].strip()

    for prefix in (
        "https://doi.org/",
        "http://doi.org/",
        "https://dx.doi.org/",
        "http://dx.doi.org/",
    ):
        if doi.lower().startswith(prefix):
            doi = doi[len(prefix):].strip()
            break

    return doi


def _doi_display(doi):
    doi = _normalize_doi(doi)

    if not doi:
        return ""

    return "doi:%s" % doi


def _doi_url(doi):
    doi = _normalize_doi(doi)

    if not doi:
        return ""

    return "https://doi.org/%s" % doi


def _source_to_dict(source):
    raw_doi = source.digital_object_id or ""
    doi = _normalize_doi(raw_doi)
    title = source.title or ""
    year = source.year or ""
    title_short = _shorten_text(title)

    if title_short and year:
        display = "%s (%s)" % (title_short, year)
    elif title_short:
        display = title_short
    else:
        display = source.acol_id()

    return {
        "id": source.id,
        "source_id": source.source_id or "",
        "acol_id": source.acol_id(),
        "text": str(source),
        "display": display,
        "table_display": display,
        "year": year,
        "doi": raw_doi,
        "doi_display": _doi_display(doi),
        "doi_url": _doi_url(doi),
        "uri": source.uri or "",
        "title": title,
        "title_short": title_short,
    }

def _sources_for_collision(collision):
    sources = []

    for datasource in collision.data_sources.all():
        for source in datasource.sources.all():
            sources.append(source)

    seen = set()
    result = []

    for source in sources:
        if source.id not in seen:
            seen.add(source.id)
            result.append(source)

    return result


def _tabdata_to_explore_row(tabdata, include_values=False):
    collision = tabdata.collision
    x_axis = tabdata.first_x()
    y_axis = tabdata.first_y()

    sources = _sources_for_collision(collision) if collision else []

    artifact_plot_url = ''
    artifact_plots = []

    if collision and collision.collision_type and collision.collision_type.iaea_code:
        collision_type = collision.collision_type.iaea_code

        if _artifact_plot_path(collision_type, collision.id):
            artifact_plot_url = reverse(
                'artifact_plot',
                kwargs={
                    'coll_iaea_code': collision_type,
                    'collision_id': collision.id,
                }
            )
            for model_name in ('gpr', 'pchip'):
                if _artifact_plot_path(collision_type, collision.id, model_name):
                    artifact_plots.append({
                        'model': model_name.upper(),
                        'url': artifact_plot_url + '?model=' + model_name,
                    })

    row = {
        "id": tabdata.id,
        "title": str(tabdata),

        "collision_id": collision.id if collision else None,
        "collision": str(collision) if collision else "",
        "artifact_plot_url": artifact_plot_url,
        "artifact_plots": artifact_plots,

        "collision_type": collision.collision_type.iaea_code if collision else "",
        "collision_type_name": str(collision.collision_type) if collision else "",

        "reaction": collision.reaction_string() if collision else "",
        "reactants": collision.reactant_strings() if collision else [],
        "products": collision.product_strings() if collision else [],
        "species_names": _collision_species_names(collision),

        "x": str(x_axis) if x_axis else "",
        "x_parameter": x_axis.parameter if x_axis else "",
        "x_unit": x_axis.unit if x_axis else "",
        "x_range": x_axis.endpoint_string() if x_axis else "",
        "x_axis": x_axis.axis_string() if x_axis else "",

        "y": str(y_axis) if y_axis else "",
        "y_parameter": y_axis.parameter if y_axis else "",
        "y_unit": y_axis.unit if y_axis else "",
        "y_range": y_axis.minmax_string() if y_axis else "",
        "y_axis": y_axis.axis_string() if y_axis else "",

        "sources": [_source_to_dict(source) for source in sources],
    }

    if include_values:
        row.update({
            "x_values": x_axis.values_as_floats() if x_axis else [],
            "y_values": y_axis.values_as_floats() if y_axis else [],
        })

    return row


def _explore_queryset():
    return TabulatedData.objects.all().select_related(
        'collision',
        'collision__collision_type'
    ).prefetch_related(
        'x',
        'y',
        'collision__reactants',
        'collision__reactants__species',
        'collision__products',
        'collision__products__species',
        'collision__data_sources',
        'collision__data_sources__sources'
    )

def _counter_to_sorted_rows(counter, key_name, value_name):
    rows = []

    for key, value in counter.items():
        rows.append({
            key_name: key,
            value_name: value,
        })

    rows.sort(key=lambda row: row[value_name], reverse=True)
    return rows



def _shorten_overview_label(text, max_len=70):
    text = (text or "").strip()

    if len(text) <= max_len:
        return text

    return "%s…" % text[:max_len - 1].rstrip()


def _source_overview_label(source):
    title = (source.title or "").strip()

    if title:
        return _shorten_overview_label(title, 70)

    doi = (source.digital_object_id or "").strip()

    if doi:
        return doi

    return source.acol_id()


def _source_overview_full_label(source):
    title = (source.title or "").strip()

    if title:
        return title

    doi = (source.digital_object_id or "").strip()

    if doi:
        return doi

    return source.acol_id()


def _source_count_rows(source_counts):
    rows = []

    for data in source_counts.values():
        rows.append({
            "source": data["source"],
            "source_full": data["source_full"],
            "title": data["title"],
            "title_short": data["source"],
            "doi": data["doi"],
            "doi_display": data["doi_display"],
            "doi_url": data["doi_url"],
            "acol_id": data["acol_id"],
            "count": data["count"],
        })

    rows.sort(key=lambda row: row["count"], reverse=True)
    return rows

def _overview_stats():
    dataset_count = TabulatedData.objects.count()
    collision_count = Collision.objects.count()
    collision_type_count = CollisionType.objects.count()
    species_count = Species.objects.count()
    species_state_count = SpeciesState.objects.count()
    source_count = Source.objects.count()

    datasets_by_collision_type = {}
    collisions_by_collision_type = {}
    species_occurrences = {}
    source_dataset_counts = {}

    tabdatas = TabulatedData.objects.all().select_related(
        'collision',
        'collision__collision_type'
    ).prefetch_related(
        'collision__reactants',
        'collision__reactants__species',
        'collision__products',
        'collision__products__species',
        'collision__data_sources',
        'collision__data_sources__sources'
    )

    seen_collision_ids_by_type = {}

    for tabdata in tabdatas:
        collision = tabdata.collision

        if not collision:
            continue

        collision_type = str(collision.collision_type)

        datasets_by_collision_type[collision_type] = (
            datasets_by_collision_type.get(collision_type, 0) + 1
        )

        if collision_type not in seen_collision_ids_by_type:
            seen_collision_ids_by_type[collision_type] = set()

        seen_collision_ids_by_type[collision_type].add(collision.id)

        for reactant in collision.reactants.all():
            species_text = str(reactant)
            species_occurrences[species_text] = species_occurrences.get(species_text, 0) + 1

        for product in collision.products.all():
            species_text = str(product)
            species_occurrences[species_text] = species_occurrences.get(species_text, 0) + 1

        sources = _sources_for_collision(collision)

        for source in sources:
            source_data = _source_to_dict(source)
            source_key = source.id

            if source_key not in source_dataset_counts:
                source_dataset_counts[source_key] = {
                    "count": 0,
                    "source": _source_overview_label(source),
                    "source_full": _source_overview_full_label(source),
                    "title": source_data["title"],
                    "doi": source_data["doi"],
                    "doi_display": source_data["doi_display"],
                    "doi_url": source_data["doi_url"],
                    "acol_id": source_data["acol_id"],
                }

            source_dataset_counts[source_key]["count"] += 1

    for collision_type, collision_ids in seen_collision_ids_by_type.items():
        collisions_by_collision_type[collision_type] = len(collision_ids)

    species_state_occurrences = _counter_to_sorted_rows(
        species_occurrences,
        "species",
        "count"
    )
    papers_contributing_collision_data = _source_count_rows(source_dataset_counts)

    return {
        "summary": {
            "datasets": dataset_count,
            "collisions": collision_count,
            "collision_types": collision_type_count,
            "species": species_count,
            "species_states": species_state_count,
            "sources": source_count,
        },
        "datasets_by_collision_type": _counter_to_sorted_rows(
            datasets_by_collision_type,
            "collision_type",
            "count"
        ),
        "collisions_by_collision_type": _counter_to_sorted_rows(
            collisions_by_collision_type,
            "collision_type",
            "count"
        ),
        "species_state_occurrences": species_state_occurrences,
        "top_species": species_state_occurrences,
        "papers_contributing_collision_data": papers_contributing_collision_data,
        "sources_by_dataset_count": papers_contributing_collision_data,
    }


# ----------------------------------------------------------------------
# Private plot helpers
# ----------------------------------------------------------------------

def _artifact_plot_path(coll_iaea_code, collision_id, model_name=None):
    """Find the generated reaction plot using the artifact naming convention."""
    collision_type = (coll_iaea_code or '').strip().lower()

    if not collision_type or collision_id is None:
        return None

    filename = 'reaction_%03d.png' % int(collision_id)
    artifacts_dir = getattr(settings, 'ACOL_ARTIFACTS_DIR', '')

    if model_name is not None and model_name not in ('gpr', 'pchip'):
        return None

    for model_name in (model_name,) if model_name is not None else ('gpr', 'pchip'):
        candidate = os.path.join(
            artifacts_dir,
            '%s_%s_global' % (model_name, collision_type),
            'images',
            filename,
        )

        if os.path.isfile(candidate):
            return candidate

    return None


def artifact_plot(request, coll_iaea_code, collision_id):
    """Serve a generated ML plot for one collision reaction."""
    path = _artifact_plot_path(coll_iaea_code, collision_id, request.GET.get('model'))

    if not path:
        raise Http404

    return FileResponse(open(path, 'rb'), content_type='image/png')

def _plot_rate_for_temperature(tabdata, temperature_index):
    y_axis = tabdata.first_y()

    if not y_axis or not y_axis.data_values:
        return None, ""

    values = y_axis.data_values.split()
    index = int(temperature_index)

    if index >= len(values):
        return None, y_axis.unit or ""

    return float(values[index]), y_axis.unit or ""


def _state_quantum_number(state):
    if isinstance(state, AtomicState):
        return state.qn

    return None


def _state_quantum_numbers(states):
    return sorted(
        state.qn for state in states
        if isinstance(state, AtomicState) and state.qn is not None
    )


def _gpr_state_pair(process, collision):
    reactant_n = _state_quantum_numbers(collision.reactants.all())
    product_n = _state_quantum_numbers(collision.products.all())

    if process == 'EEX' and reactant_n and product_n:
        return max(reactant_n), max(product_n)

    if process in ('HAS', 'HPN') and len(reactant_n) >= 2:
        return min(reactant_n), max(reactant_n)

    if process == 'EDR' and len(product_n) >= 2:
        return min(product_n), max(product_n)

    if process == 'ERO' and reactant_n and product_n:
        return max(reactant_n), max(product_n)

    return None


def _gpr_state_pairs(process, atom_inchikey):
    if process == 'EDR':
        role_filter = Q(products__species__inchikey=atom_inchikey)
    else:
        role_filter = Q(reactants__species__inchikey=atom_inchikey)

    collisions = Collision.objects.filter(
        role_filter,
        collision_type__iaea_code=process,
    ).prefetch_related('reactants', 'reactants__species', 'products', 'products__species').distinct()

    pairs = set()

    for collision in collisions:
        pair = _gpr_state_pair(process, collision)

        if pair:
            pairs.add(pair)

    return sorted(pairs)


def _gpr_prediction_data(process, atom, initial_n, result_n, temperature):
    element = atom.chemical_formula
    data = {'temperature': temperature}

    if process == 'EEX':
        data.update({
            'element': element,
            'initial_n': initial_n,
            'delta_n': str(int(result_n) - int(initial_n)),
        })
    elif process in ('HAS', 'HPN'):
        data.update({
            'element': element,
            'lower_initial_n': initial_n,
            'upper_initial_n': result_n,
        })
    elif process == 'EDR':
        data.update({
            'species': element,
            'lower_final_n': initial_n,
            'upper_final_n': result_n,
            'vibrational_level': '0',
        })
    elif process == 'ERO':
        data.update({
            'element': element,
            'ion_n': str(max(1, int(initial_n) - 1)),
            'initial_neutral_n': initial_n,
            'final_neutral_n': initial_n,
            'final_excited_n': result_n,
        })

    return data


def _second_item(queryset):
    try:
        return queryset[1]
    except IndexError:
        return None


def _plot_rows_for_hpn_has(coll_iaea_code, atom_inchi, temperature_index):
    tabdatas = TabulatedData.objects.filter(
        collision__reactants__species__inchikey=atom_inchi,
        collision__collision_type__iaea_code=coll_iaea_code
    )

    n_values = []
    rc_values = []
    ylabel = ""

    for tabdata in tabdatas:
        rc, ylabel = _plot_rate_for_temperature(tabdata, temperature_index)

        if rc is None:
            continue

        reactant_state = _second_item(tabdata.collision.reactants.all())
        n = _state_quantum_number(reactant_state)

        if n is not None:
            n_values.append(n)
            rc_values.append(rc)

    return n_values, rc_values, ylabel


def _plot_rows_for_ero_edr(coll_iaea_code, atom_inchi, temperature_index):
    tabdatas = TabulatedData.objects.filter(
        collision__products__species__inchikey=atom_inchi,
        collision__collision_type__iaea_code=coll_iaea_code
    )

    n_values = []
    rc_values = []
    ylabel = ""

    for tabdata in tabdatas:
        rc, ylabel = _plot_rate_for_temperature(tabdata, temperature_index)

        if rc is None:
            continue

        product_state = _second_item(tabdata.collision.products.all())
        n = _state_quantum_number(product_state)

        if n is not None:
            n_values.append(n)
            rc_values.append(rc)

    return n_values, rc_values, ylabel


def _plot_rows_for_eex(coll_iaea_code, atom_inchi, temperature_index):
    tabdatas = TabulatedData.objects.filter(
        collision__reactants__species__inchikey=atom_inchi,
        collision__collision_type__iaea_code=coll_iaea_code
    )

    n_values = []
    rc_values = []
    ylabel = ""
    rc_matrix = [[], [], [], [], []]

    for tabdata in tabdatas:
        reactant_state = _second_item(tabdata.collision.reactants.all())
        product_state = _second_item(tabdata.collision.products.all())

        reactant_n = _state_quantum_number(reactant_state)
        product_n = _state_quantum_number(product_state)

        if reactant_n is None or product_n is None:
            continue

        rc, ylabel = _plot_rate_for_temperature(tabdata, temperature_index)

        if rc is None:
            continue

        n = int(reactant_n)
        delta_n = int(product_n) - n

        n_values.append(n)
        rc_values.append(rc)

        if 1 <= delta_n <= len(rc_matrix):
            rc_matrix[delta_n - 1].append(rc)

    return n_values, rc_values, ylabel


def _plot_rows(coll_iaea_code, atom_inchi, temperature_index):
    if coll_iaea_code in ["HPN", "HAS"]:
        return _plot_rows_for_hpn_has(coll_iaea_code, atom_inchi, temperature_index)

    if coll_iaea_code in ["ERO", "EDR"]:
        return _plot_rows_for_ero_edr(coll_iaea_code, atom_inchi, temperature_index)

    if coll_iaea_code == "EEX":
        return _plot_rows_for_eex(coll_iaea_code, atom_inchi, temperature_index)

    return [], [], ""


def _save_plot(n_values, rc_values, ylabel):
    filename = str(uuid.uuid4()) + '.png'

    plt.clf()
    plt.xticks(n_values)
    plt.plot(n_values, rc_values, 'ro')
    plt.xlabel('quantum number')
    plt.ylabel(ylabel)
    plt.savefig(os.path.dirname(os.path.realpath(__file__)) + '/../static/plots/' + filename)

    return filename


# ----------------------------------------------------------------------
# Public URL views
# ----------------------------------------------------------------------

def index(request):
    """Render main UI page with search and plotting forms."""
    template = get_template('main.html')

    f = Search_form()
    p = Plot_form()
    gpr_collision_types = CollisionType.objects.filter(
        iaea_code__in=('EEX', 'HAS', 'HPN', 'EDR', 'ERO')
    ).order_by('id')

    html = template.render({
        'f': f,
        'p': p,
        'gpr_collision_types': gpr_collision_types,
        'acol_base_url': settings.ACOL_BASE_URL.rstrip('/'),
    }, request)

    return HttpResponse(html)


def gpr_predict(request):
    """Calculate one prediction with the selected saved GPR model."""
    if request.method != 'POST':
        return _json_response({'error': 'Use POST to request a prediction.'}, status=405)

    process = (request.POST.get('process') or '').strip().upper()
    atom_inchikey = (request.POST.get('atom') or '').strip()
    initial_n = request.POST.get('initial_n')
    result_n = request.POST.get('result_n')

    try:
        atom = Atom.objects.filter(inchikey=atom_inchikey, ion_charge=0).first()

        if atom is None:
            raise Atom.DoesNotExist

        try:
            selected_pair = (int(initial_n), int(result_n))
        except (TypeError, ValueError):
            raise ValueError('Choose an available initial and result state.')

        if selected_pair not in _gpr_state_pairs(process, atom_inchikey):
            raise ValueError('Choose an available initial and result state.')

        prediction_data = _gpr_prediction_data(
            process,
            atom,
            initial_n,
            result_n,
            request.POST.get('temperature'),
        )
        result = predict_with_gpr(process, prediction_data)
    except Atom.DoesNotExist:
        return _json_response({'error': 'Choose an available atom.'}, status=400)
    except ValueError as error:
        return _json_response({'error': str(error)}, status=400)
    except RuntimeError as error:
        logger.exception('GPR prediction failed')
        return _json_response({'error': str(error)}, status=503)

    return _json_response(result)


def get_gpr_atoms(request, coll_iaea_code):
    """Return neutral atoms in the role used by the selected GPR model."""
    coll_type = _get_collision_type(coll_iaea_code)

    if coll_iaea_code == 'EDR':
        atoms = Atom.objects.filter(
            ion_charge=0,
            speciesstate__products__collision_type=coll_type,
        ).distinct()
    else:
        atoms = Atom.objects.filter(
            ion_charge=0,
            speciesstate__reactants__collision_type=coll_type,
        ).distinct()

    return _json_response(_species_dict(atoms))


def get_gpr_states(request, coll_iaea_code, atom_inchikey):
    """Return the initial/result state pairs available for prediction."""
    results = {}

    for initial_n, result_n in _gpr_state_pairs(coll_iaea_code, atom_inchikey):
        results.setdefault(str(initial_n), []).append(result_n)

    return _json_response({
        'initial': sorted(int(value) for value in results),
        'results': results,
    })


def get_products(request, coll_iaea_code):
    """Return products for a collision type as inchikey -> display string JSON."""
    coll_type = _get_collision_type(coll_iaea_code)
    products = _products_for_collision_type(coll_type)

    return _json_response(_species_dict(products))


def get_reactants(request, coll_iaea_code):
    """Return reactants for a collision type as inchikey -> display string JSON."""
    coll_type = _get_collision_type(coll_iaea_code)
    reactants = _reactants_for_collision_type(coll_type)

    return _json_response(_species_dict(reactants))


def get_atoms(request, coll_iaea_code):
    """Return atoms, reactants or products, for a collision type."""
    coll_type = _get_collision_type(coll_iaea_code)
    atoms = _atoms_for_collision_type(coll_type, neutral_only=False)

    return _json_response(_species_dict(atoms))


def get_atoms_no_ions(request, coll_iaea_code):
    """Return neutral atoms only, reactants or products, for a collision type."""
    coll_type = _get_collision_type(coll_iaea_code)
    atoms = _atoms_for_collision_type(coll_type, neutral_only=True)

    return _json_response(_species_dict(atoms))


def get_temps(request, coll_iaea_code, atom_inchi):
    """Return indexed temperature/energy axis values for plot UI."""
    tabdatas = _tabdata_for_collision_and_species(coll_iaea_code, atom_inchi)
    tabdata = _first_queryset_item(tabdatas)

    values = _tabdata_first_x_values(tabdata) if tabdata else []

    values_dict = {}

    for i, value in enumerate(values):
        values_dict[i] = value

    return _json_response(values_dict)


def explore_processes(request):
    """Return summary rows for the Explore Data tab."""
    rows = []

    for tabdata in _explore_queryset():
        if tabdata.collision:
            rows.append(_tabdata_to_explore_row(tabdata))

    return _json_response({
        "count": len(rows),
        "rows": rows,
    })


def explore_process_data(request, tabdata_id):
    """Return one full Explore Data row, including plottable x/y values."""
    tabdata = get_object_or_404(TabulatedData, pk=tabdata_id)

    return _json_response(
        _tabdata_to_explore_row(tabdata, include_values=True)
    )

def overview_stats(request):
    """Return aggregated database statistics for the Overview tab."""
    return _json_response(_overview_stats())


def plot(request, coll_iaea_code, atom_inchi, temperature_index):
    """Generate a plot image and return filename with plotted arrays as JSON."""
    n_values, rc_values, ylabel = _plot_rows(
        coll_iaea_code,
        atom_inchi,
        temperature_index
    )

    filename = _save_plot(n_values, rc_values, ylabel)

    return _json_response((filename, n_values, rc_values))
