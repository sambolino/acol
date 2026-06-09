"""VAMDC keyword mappings for ACol.

`RETURNABLES` maps standardized VAMDC returnable keys to object attributes or
methods available during XSAMS generation.

`RESTRICTABLES` maps standardized query constraints to Django ORM filter paths
used by `sql2Q` conversion in `queryfunc.py`.
"""

from vamdctap.unitconv import *

# The returnable dictionary is used internally by the node and defines
# all the ways the VAMDC standard keywords (left-hand side) maps to
# the internal database representation queryset (right-hand side)
#
# When writing this, it helps to remember that dictionary is applied
# in a loop to every matching *instance* of the queryset variables
# returned from queryfunc.py. So in the example below, all 'AtomStates'
# will be looped over by the node software, using the name 'AtomState'
# (singular). 'AtomState' will be one single instance of a matching
# database object, from which we extract everything we need by parsing
# the VAMDC_standard LHS of this dictionary to how it maps to our specific
# database on the RHS. So, when looping through all AtomState objects
# matching the given query, the generator will for example know that
# to get the AtomStateEnergy VAMDC value, it will need to look at
# the AtomState.energy, i.e. the "energy" property of the current
# database object being worked on.
#
# (if you look at queryfuncs.py, you'll see 'AtomStates' being
#  assigned)

RETURNABLES = {\
'NodeID' : 'Acol', # required
############################################################
'MethodID' : 'Method.id',
'MethodCategory' : 'Method.category',
############################################################

'AtomSpeciesId':'Atom.id',
'AtomInchi':'Atom.inchi',
'AtomInchiKey':'Atom.inchikey',
'AtomSymbol':'Atom.chemical_formula',
'AtomIonCharge':'Atom.ion_charge',
'AtomNuclearCharge':'Atom.nuclear_charge',

'MoleculeSpeciesId':'Molecule.id',
'MoleculeInchi':'Molecule.inchi',
'MoleculeInchiKey':'Molecule.inchikey',
'MoleculeChemicalName':'Molecule.name',
'MoleculeOrdinaryStructuralFormula':'Molecule.getLatexFormula()',
'MoleculeStoichiometricFormula':'Molecule.chemical_formula',
'MoleculeMolecularWeight':'Molecule.molecular_weight',
'MoleculeMolecularWeightUnit': 'amu',
'MoleculeIonCharge':'Molecule.ion_charge',

'AtomStateId':'AtomicState.id',
'AtomStateDescription':'AtomicState.description',
#'AtomStateSuperShellPrincipalQN':'Component.qn',
#'AtomStateSuperShellNumberOfElectrons':'1',
#'AtomStateShellOrbitalAngMomSymbol':'1',
'AtomStateShellNumberOfElectrons':'Shell.number_of_electrons',
#'AtomStateShellPrincipalQN':'Component.qn',
'AtomStateShellPrincipalQN':'Shell.qn',
'AtomStateShellOrbitalAngMom':'0',
#'AtomStateShellPrincipalQN':'3',
#'AtomStateCompositionComment':'',
#'AtomStateComponentComment':'',
#'AtomStateShellID':'Shell.id',
#'AtomStateMagneticQuantumNumber':'AtomicState.qn',
#'AtomStateCoreTotalAngMom':'AtomicState.qn',

'MoleculeStateId':'MolecularState.id',
'MoleculeStateDescription': 'MolecularState.description',
#'MoleculeStateDescription':'MoleculeState.term',
#'MoleculeStateEnergy':'MoleculeState.treshold',
#'MoleculeStateEnergyUnit':'MoleculeState.treshold_unit',


'ParticleName':'Particle.name',
'ParticleSpeciesID':'Particle.speciesid',
'ParticleCharge':'Particle.charge',
'ParticleComment':'Particle.comment',
'CollisionID':'CollTran.id',
'CollisionReactantState':'Reactant.stateref',
'CollisionReactantSpecies':'Reactant.speciesref',
'CollisionProductState':'Product.stateref',
'CollisionProductSpecies':'Product.speciesref',
'CollisionRef':'CollTran.sourcerefs',
'CollisionCode':'CollTran.collision_type.vamdc_code',
'CollisionIAEACode':'CollTran.collision_type.iaea_code',
'CollisionUserDefinition':'CollTran.collision_type.name',

#couldn't find the path to DataSet.description so hard coded here
#'CollisionDataSetDescription':'rateCoefficient',
'CollisionDataSetDescription': 'CollisionDataSet.description',

'SourceID':'Source.source_id',
'SourceCategory':'Source.category',
'SourceArticleNumber':'Source.article_number',
'SourceDOI':'Source.digital_object_id',
'SourcePageBegin':'Source.page_begin',
'SourcePageEnd':'Source.page_end',
'SourceTitle':'Source.title',
'SourceAuthorName':'Source.authnames',
'SourceURI':'Source.uri',
'SourceVolume':'Source.volume',
'SourceYear':'Source.year',
'SourceComments':'Source.comments',
}

# The restrictable dictionary defines limitations to the search.
# The left-hand side is standardized, the righ-hand size should
# be defined in Django query-language style, where e.g. a search
# for the Species.atomic field  would be written as species__atomic.

RESTRICTABLES = {\
#general
'CollisionIAEACode' : 'collision_type__iaea_code',
#'CollisionCode' : 'collision_type__vamdc_code',
#'SourceDOI' : 'dataset_set__sources__digital_object_id',
#'SourceYear' : 'source__year',
#'SourceCategory' : 'source__category',

#general
'AtomSymbol' : 'products__species__chemical_formula',
'MoleculeChemicalName' : 'products__species__chemical_formula',
'InchiKey' : 'products__species__inchikey',
'Inchi' : 'products_species__inchi',
'IonCharge': 'products_species__ion_charge',

#only search for reactants
'reactant0.AtomSymbol' : 'reactants__species__chemical_formula',
'reactant0.MoleculeChemicalName' : 'products__species__chemical_formula',
'reactant0.InchiKey' : 'reactants__species__inchikey',
'reactant0.Inchi' : 'reactants__species__inchi',
'reactant0.AtomStateShellPrincipalQN' : 'reactants__qn',
'reactant1.AtomSymbol' : 'reactants__species__chemical_formula',
'reactant1.MoleculeChemicalName' : 'products__species__chemical_formula',
'reactant1.InchiKey' : 'reactants__species__inchikey',
'reactant1.Inchi' : 'reactants__species__inchi',
'reactant1.AtomStateShellPrincipalQN' : 'reactants__qn',

# collider is always an electron:
#
#'collider.ParticleName':test_constant(['electron']),

# target could also be an origin_species
'target.AtomSymbol' : 'reactant__species__chemical_formula',
'target.MoleculeChemicalName' : 'products__species__chemical_formula',
'target.InchiKey' : 'reactant__species__inchikey',
'target.Inchi' : 'reactant__species__inchi',

# only search for products
'product0.AtomSymbol' : 'product__species__chemical_formula',
'product0.MoleculeChemicalName' : 'products__species__chemical_formula',
'product0.InchiKey' : 'product__species__inchikey',
'product0.Inchi' : 'product__species__inchi',
#'product0.AtomStateShellPrincipalQN' : 'product__qn',
'product1.AtomSymbol' : 'product__species__chemical_formula',
'product1.MoleculeChemicalName' : 'products__species__chemical_formula',
'product1.InchiKey' : 'product__species__inchikey',
'product1.Inchi' : 'product__species__inchi',
#'product1.AtomStateShellPrincipalQN' : 'product__qn',

}
