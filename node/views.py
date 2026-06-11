import os.path
import json
import uuid
import math
import matplotlib
import logging
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from django.template import RequestContext
from django.shortcuts import render_to_response,get_object_or_404
from django.template.loader import get_template
from django.http import HttpResponse
from node.models import *
from node.forms import *

logger = logging.getLogger()

def json_response(data):
    return HttpResponse(json.dumps(data), content_type='application/json')

def index(request):
    """Render main UI page with search and plotting forms."""
    t = get_template('main.html')
    title = 'Search'
    f = Search_form()
    p = Plot_form()
    html = t.render ({'f':f,'p':p,})
    return HttpResponse(html)

def get_products(request, coll_iaea_code):
    """Return products for a collision type as inchikey->name JSON."""
    collType = CollisionType.objects.get(iaea_code=coll_iaea_code)
    products = Species.objects.filter(speciesstate__products__collision_type=collType).distinct()
    products_dict = {}
    for p in products:
        products_dict[p.inchikey] = p.name
    return HttpResponse(json.dumps(products_dict))

def get_reactants(request, coll_iaea_code):
    """Return reactants for a collision type as inchikey->name JSON."""
    collType = CollisionType.objects.get(iaea_code=coll_iaea_code)
    reactants = Species.objects.filter(speciesstate__reactants__collision_type=collType).distinct()
    reactants_dict = {}
    for r in reactants:
        reactants_dict[r.inchikey] = r.name
    return HttpResponse(json.dumps(reactants_dict))

def get_atoms(request, coll_iaea_code):
    """Return atoms (reactants or products) for a collision type."""
    collType = CollisionType.objects.get(iaea_code=coll_iaea_code)
    atoms = Atom.objects.filter(speciesstate__products__collision_type=collType) | \
            Atom.objects.filter(speciesstate__reactants__collision_type=collType)
    atoms_dict = {}
    for a in atoms:
        atoms_dict[a.inchikey] = a.name
    #return HttpResponse(json.dumps(species_dict), mimetype="application/json")
    return HttpResponse(json.dumps(atoms_dict))

def get_atoms_no_ions(request, coll_iaea_code):
    """Return neutral atoms only for a collision type."""
    collType = CollisionType.objects.get(iaea_code=coll_iaea_code)
    atoms = Atom.objects.filter(ion_charge=0, speciesstate__products__collision_type=collType) | \
            Atom.objects.filter(ion_charge=0, speciesstate__reactants__collision_type=collType)
    atoms_dict = {}
    for a in atoms:
        atoms_dict[a.inchikey] = a.name
    return HttpResponse(json.dumps(atoms_dict))

def get_temps(request, coll_iaea_code, atom_inchi):
    """Return indexed temperature axis values for plot UI."""
    from django.db.models import Q
    TabData = TabulatedData.objects.filter((Q(collision__reactants__species__inchikey=atom_inchi) |
        Q(collision__products__species__inchikey=atom_inchi)) &
        Q(collision__collision_type__iaea_code=coll_iaea_code))
    temps = TabData.all()[0].x.all()[0].data_values.split()
    temps_dict = {}
    for i, t in enumerate(temps):
        temps_dict[i] = t
    #return HttpResponse(json.dumps(species_dict), mimetype="application/json")
    return HttpResponse(json.dumps(temps_dict))

def source_to_dict(source):
    return {
        "id": source.id,
        "source_id": source.source_id or "",
        "acol_id": source.acol_id(),
        "text": str(source),
        "year": source.year or "",
        "doi": source.digital_object_id or "",
        "uri": source.uri or "",
        "title": source.title or "",
    }


def sources_for_collision(collision):
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


def tabdata_to_explore_row(tabdata, include_values=False):
    collision = tabdata.collision
    x_axis = tabdata.first_x()
    y_axis = tabdata.first_y()

    sources = sources_for_collision(collision) if collision else []

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

        "sources": [source_to_dict(source) for source in sources],
    }

    if include_values:
        row.update({
            "x_values": x_axis.values_as_floats() if x_axis else [],
            "y_values": y_axis.values_as_floats() if y_axis else [],
        })

    return row


def explore_processes(request):
    tabdatas = TabulatedData.objects.all().select_related(
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

    rows = []

    for tabdata in tabdatas:
        if tabdata.collision:
            rows.append(tabdata_to_explore_row(tabdata))

    return json_response({
        "count": len(rows),
        "rows": rows,
    })


def explore_process_data(request, tabdata_id):
    tabdata = get_object_or_404(TabulatedData, pk=tabdata_id)

    return json_response(
        tabdata_to_explore_row(tabdata, include_values=True)
    )


def plot(request, coll_iaea_code, atom_inchi, temperature_index):
    """Generate a plot image and return filename with plotted arrays as JSON."""

    rc_matrix = [[], [], [], [], []]
    rc_values = []
    n_values = []
    ylabel = []

    if(coll_iaea_code in ["HPN", "HAS"]):
        #processes = Collision.objects.filter(reactants__species=atom)
        #temperatures = [int(i) for i in processes[0]..data_values.split()]
        TabData = TabulatedData.objects.filter(collision__reactants__species__inchikey=atom_inchi,
                collision__collision_type__iaea_code=coll_iaea_code)
        for tabdata in TabData:
            #take the rc value from the Y axis, according to index of the X (temperature) axis
            yaxis = tabdata.y.all()[0]
            rc=float(yaxis.data_values.split()[int(temperature_index)])
            ylabel=yaxis.unit
            rc_values.append(rc)
            reactants = tabdata.collision.reactants.all()
            if isinstance(reactants[1], AtomicState):
                n = reactants[1].qn
                n_values.append(n)
    elif(coll_iaea_code in ["ERO", "EDR"]):
        TabData = TabulatedData.objects.filter(collision__products__species__inchikey=atom_inchi,
                collision__collision_type__iaea_code=coll_iaea_code)
        for tabdata in TabData:
            #take the rc value from the Y axis, according to index of the X (temperature) axis
            yaxis = tabdata.y.all()[0]
            rc=float(yaxis.data_values.split()[int(temperature_index)])
            ylabel=yaxis.unit
            rc_values.append(rc)
            products = tabdata.collision.products.all()
            if isinstance(products[1], AtomicState):
                n = products[1].qn
                n_values.append(n)
    elif(coll_iaea_code=="EEX"):
        TabData = TabulatedData.objects.filter(collision__reactants__species__inchikey=atom_inchi,
                collision__collision_type__iaea_code=coll_iaea_code)
        for tabdata in TabData:
            reactants = tabdata.collision.reactants.all()
            products = tabdata.collision.products.all()
            delta_n = 0
            if(isinstance(reactants[1], AtomicState) and isinstance(products[1], AtomicState)):
                n = int(reactants[1].qn)
                delta_n = int(products[1].qn) - n
                n_values.append(n)
            #take the rc value from the Y axis, according to index of the X (temperature) axis
            yaxis = tabdata.y.all()[0]
            rc=float(yaxis.data_values.split()[int(temperature_index)])
            ylabel=yaxis.unit
            rc_values.append(rc)
            rc_matrix[delta_n-1].append(rc)
            #logger.debug(rc_matrix)

    filename = str(uuid.uuid4()) + '.png'
    plt.clf()
    plt.xticks(n_values)
    if(coll_iaea_code=="EEX"):
        plt.plot(n_values, rc_values, 'ro')
        #plt.plot(n_values, rc_matrix[0], 'ro')
        #plt.plot(n_values, rc_matrix[1], 'bo')
        #plt.plot(n_values, rc_matrix[2], 'ro')
        #plt.plot(n_values, rc_matrix[3], 'ro')
        #plt.plot(n_values, rc_matrix[4], 'ro')
    else: plt.plot(n_values, rc_values, 'ro')
    #plt.plot(n_values, rc_values, 'ro')
    plt.xlabel('quantum number');
    plt.ylabel(ylabel);
    #plt.connect('button_press_event', onclick)
    plt.savefig(os.path.dirname(os.path.realpath(__file__)) + '/../static/plots/'+filename)
#    plt.clear()
    #res = ["{:.3E}".format(result) for result in results]
    t = filename, n_values, rc_values
    #return HttpResponse(json.dumps(t), mimetype="application/json")
    return HttpResponse(json.dumps(t))
