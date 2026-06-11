import os.path
import json
import uuid
import math
import matplotlib
import logging

matplotlib.use('Agg')

import matplotlib.pyplot as plt

from django.db.models import Q
from django.template.loader import get_template
from django.http import HttpResponse
from django.shortcuts import get_object_or_404

from node.models import *
from node.forms import *


logger = logging.getLogger()


# ----------------------------------------------------------------------
# Private generic helpers
# ----------------------------------------------------------------------

def _json_response(data):
    return HttpResponse(json.dumps(data), content_type='application/json')


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

def _source_to_dict(source):
    doi = source.digital_object_id or ""
    title = source.title or ""
    year = source.year or ""

    if doi:
        display = doi
    elif title and year:
        display = "%s (%s)" % (title, year)
    elif title:
        display = title
    else:
        display = source.acol_id()

    return {
        "id": source.id,
        "source_id": source.source_id or "",
        "acol_id": source.acol_id(),
        "text": str(source),
        "display": display,
        "year": year,
        "doi": doi,
        "uri": source.uri or "",
        "title": title,
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

    row = {
        "id": tabdata.id,
        "title": str(tabdata),

        "collision_id": collision.id if collision else None,
        "collision": str(collision) if collision else "",

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
            source_text = source.acol_id()
            source_dataset_counts[source_text] = source_dataset_counts.get(source_text, 0) + 1

    for collision_type, collision_ids in seen_collision_ids_by_type.items():
        collisions_by_collision_type[collision_type] = len(collision_ids)

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
        "top_species": _counter_to_sorted_rows(
            species_occurrences,
            "species",
            "count"
        )[:15],
        "sources_by_dataset_count": _counter_to_sorted_rows(
            source_dataset_counts,
            "source",
            "count"
        ),
    }


# ----------------------------------------------------------------------
# Private plot helpers
# ----------------------------------------------------------------------

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

    html = template.render({
        'f': f,
        'p': p,
    })

    return HttpResponse(html)


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
