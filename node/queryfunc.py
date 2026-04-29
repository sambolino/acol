"""Query-time data shaping for VAMDC-TAP requests.

This module is called by NodeSoftware during request execution. The central
entrypoint is :func:`setupResults`, which receives the parsed TAP SQL object,
runs local ORM lookups, and returns a dictionary containing standardized keys
(`Sources`, `CollTrans`, `Atoms`, `Molecules`, `Particles`, `HeaderInfo`).

Important behavior in this file:
- Build an atom/ion/state hierarchy dynamically at runtime.
- Attach temporary attributes consumed by the XSAMS generators.
- Add synthetic electron participants for specific IAEA process codes.
"""

# library imports

import logging
from itertools import chain

from vamdctap.sqlparse import sql2Q
from .dictionaries import *

from . import models
import datetime

log = logging.getLogger("vamdc.node.queryfu")

LIMIT = 1000

class Particle:
    """Lightweight runtime-only particle object used in generated output."""
    def __init__(self, particletype):
        if particletype == 'electron':
            self.charge = -1
            self.name = particletype
            self.speciesid = 'XElectron'
            self.comment = 'low energy electrons'
    def __eq__(self, other):
        return isinstance(other, Particle) and (self.name == other.name)
    def __hash__(self):
        return hash(self.name)

class Shell:
    """Runtime shell representation used for atomic composition mapping."""
    def __init__(self, qn, number_of_electrons):
        self.qn = qn
        self.number_of_electrons = number_of_electrons

class Component:
    """Runtime wrapper holding a list of shell objects."""
    def __init__(self, shells):
        self.Shells = shells

class ReaProd:
    """Runtime reactant/product reference used by collision serialization."""
    def __init__(self, stateid, speciesid):
        self.stateref = stateid
        self.speciesref = speciesid

class DataSet:
    """Runtime dataset wrapper expected by NodeSoftware collision output."""
    def __init__(self, tabdata):
        self.TabData = [tabdata]

        try:
            y0 = tabdata.y.all()[0]
            self.description = y0.description
        except:
            self.description = "undefined"

#------------------------------------------------------------
# Main function
#------------------------------------------------------------

def setupResults(sql):
    """
    Build and return the standardized NodeSoftware response payload.

    Parameters
    ----------
    sql:
        Parsed TAP SQL structure provided by NodeSoftware.

    Returns
    -------
    dict
        Empty dict when no collisions match; otherwise contains the expected
        top-level collections and header counters for XSAMS generation.
    """
    # log the incoming query
    log.debug(sql)

    # convert the incoming sql to a correct django query syntax object
    # (sql2Q is a helper function to do this for us).
    q = sql2Q(sql)

    print(q)

    #from django.db.models.query_utils import Q
    #q = "(AND: ('reactants__atom__chemical_formula__exact', 'K'))"
    #q = Q()
    collisions = set(models.Collision.objects.filter(q))

    stateids = set()
    for coll in collisions:
        for r in coll.reactants.all():
            stateids.add(r.id)
        for p in coll.products.all():
            stateids.add(p.id)


    states = models.SpeciesState.objects.filter(pk__in=stateids)

    atoms = []
    atom_groups = {}
    sourceids = set()
    particles = set()
    molecules = set()

    lastmodifiedheader = datetime.datetime(1970, 1, 1, 1, 1)

    for state in states:
        if isinstance(state, models.AtomicState):
            ion = state.species

            group_key = (
                #ion.name,
                ion.chemical_formula,
                ion.nuclear_charge,
            )

            if group_key not in atom_groups:
                base_atom = ion
                base_atom.Ions = []
                atom_groups[group_key] = base_atom

            base_atom = atom_groups[group_key]

            ion_found = None
            for existing_ion in base_atom.Ions:
                if existing_ion.id == ion.id:
                    ion_found = existing_ion
                    break

            if ion_found is None:
                ion.States = []
                base_atom.Ions.append(ion)
                ion_found = ion

            ion_found.States.append(state)

        elif isinstance(state, models.MolecularState):
            molecules.add(state.species)

    atoms = list(atom_groups.values())

    for atom in atoms:
        atom.HasMassData = False
        atom.MassValue = None

        for ion in atom.Ions:
            mass = getattr(ion, 'molecular_weight', None)
            if mass is not None and mass != '':
                atom.HasMassData = True
                atom.MassValue = mass
                atom.MassNumber = int(round(float(mass)))
                break
        for ion in atom.Ions:
            for state in ion.States:
                if hasattr(state, 'Components'):
                    delattr(state, 'Components')

                if ion.nuclear_charge is not None and state.qn is not None:
                    shell = Shell(state.qn, int(ion.nuclear_charge) - ion.ion_charge)
                    component = Component([shell])
                    state.Components = [component]

        """
        for ion in atom.Ions:
            for state in ion.States:
                state.Components = []

                if ion.nuclear_charge is not None and state.qn:
                #if ion.nuclear_charge is not None:
                    shell = Shell(state.qn, int(ion.nuclear_charge) - ion.ion_charge)
                    component = Component([shell])
                    state.Components = [component]
        """
    for molecule in molecules:
        molecule.States = molecule.speciesstate_set.filter(pk__in=stateids)


    for coll in collisions:

        if coll.lastmodified > lastmodifiedheader:
            lastmodifiedheader = coll.lastmodified
        coll.sourcerefs = []
        rs = coll.reactants.all()
        ps = coll.products.all()
        coll.Reactants = []
        coll.Products = []

        for r in rs:
            coll.Reactants.append(ReaProd(r.id, r.species.id))
        for p in ps:
            coll.Products.append(ReaProd(p.id, p.species.id))

        #manually add electron depending on process type
        processes_with_electron = ('HPN', 'HAS', 'EDR', 'ERO', 'ENI')
        iaea = coll.collision_type.iaea_code
        if iaea in processes_with_electron:
            p = Particle('electron')
            particles.add(p)
            if iaea in ['HPN', 'HAS']: coll.Products.append(ReaProd('', 'XElectron'))
            else: coll.Reactants.append(ReaProd('', 'XElectron'))

        '''
        coll.DataSets = models.DataSet.objects.filter(collision_id=coll.id)

        for dataset in coll.DataSets:
            for sourceid in dataset.sources.values_list('source_id', flat=True):
                sourceids.add(sourceid)
                coll.sourcerefs.append(sourceid)
            dataset.TabData = models.TabulatedData.objects.filter(dataset_id=dataset.id)
        '''

        coll.DataSets = []

        datasources = models.DataSource.objects.filter(collisions=coll)

        for datasource in datasources:
            for sourceid in datasource.sources.values_list('source_id', flat=True):
                sourceids.add(sourceid)
                coll.sourcerefs.append(sourceid)

        tabdatas = models.TabulatedData.objects.filter(collision_id=coll.id)

        for tabdata in tabdatas:
            coll.DataSets.append(DataSet(tabdata))
            #tabdata.TabData = [tabdata]
            #coll.DataSets.append(tabdata)

    sources = models.Source.objects.filter(source_id__in=sourceids)
    for src in sources:
        src.authnames=src.authors.values_list('name', flat=True)

    nsources = len(sources)
    ncoll = len(collisions)
    natoms = len(atoms)
    nmolecules = len(molecules)
    nspecies  = natoms + nmolecules
    nstates = len(stateids)

    #make sure that lastmodifiedheader is not newer than now
    if lastmodifiedheader > datetime.datetime.now():
        lastmodifiedheader = datetime.datetime.now()

    # standardized and shouldn't be changed.
    headerinfo = {'COUNT-SOURCES'    : nsources,
                  'COUNT-SPECIES'    : nspecies,
                  'COUNT-ATOMS'      : natoms,
                  'COUNT-MOLECULES'  : nmolecules,
                  'COUNT-STATES'     : nstates,
		          'COUNT-COLLISIONS' : ncoll,
                  'COUNT-RADIATIVE'  : 0,
                  'LAST-MODIFIED'    : lastmodifiedheader,
                  }

    # Return the data. The keynames are standardized.
    if ncoll > 0:
        return {'Sources'    : sources,
    	        'CollTrans'  : collisions,
	            'Atoms'      : atoms,
                'Molecules'  : molecules,
	            'Particles'  : particles,
	            'HeaderInfo' : headerinfo,
                }
    else:
        return {}
