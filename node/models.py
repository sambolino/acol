import re
from django.db import models
from polymorphic.models import PolymorphicModel
from django.utils import timezone

class Species(PolymorphicModel):
    """Base chemical species shared by atom and molecule specializations."""
    name = models.CharField(max_length=128, db_index=True)
    inchi = models.CharField(max_length=256)
    inchikey = models.CharField(max_length=128)
    chemical_formula = models.CharField(max_length=128)
    stoichiometric_formula = models.CharField(max_length=128, null=True, blank=True)
    ion_charge = models.IntegerField(default=0)
    cas = models.CharField(max_length=128, null=True, blank=True)
    nuclear_charge = models.CharField(max_length=32, null=True, blank=True)
    molecular_weight = models.FloatField(null=True, blank=True, error_messages={'invalid':"Please enter a valid float number"})
    def __str__(self):
        return "%s: %s" % (self.name, self.stoichiometric_formula or self.chemical_formula)
    def __unicode__(self):
        return "%s: %s" % (self.name, self.stoichiometric_formula or self.chemical_formula)
    class Meta:
        db_table = u'species'

class Molecule(Species):
    """Molecular species with helper for XSAMS-friendly formula rendering."""

    #code taken from wadis node
    def getLatexFormula(self):
        # See http://www.physicsforums.com/misc/howtolatex.pdf
        # See http://vamdc.org/documents/standards/dataModel/vamdcxsams/speciesMolecules.html#molecule

        if self.chemical_formula is None:
            return None


        def setSubSup(matchObj):
            str = ''
            if matchObj.group(2):
                s = matchObj.group(2)
                if int(s) > 1:
                    str += "^" + ("{%s}" % s if len(s) > 1 else s)
            str += matchObj.group(3)
            if matchObj.group(4):
                s = matchObj.group(4)
                if int(s) > 1:
                    str += "_" + ("{%s}" % s if len(s) > 1 else s)
            return str


        def setPlusMinus(matchObj):
            str = ''
            if matchObj.group(1):
                s = matchObj.group(1)
                if int(s) > 1:
                    str += s
            if matchObj.group(2):
                s = matchObj.group(2)
                if s == 'plus':
                    str += '+'
                elif s == 'minus':
                    str += '-'
            str = "^" + ("{%s}" % str if len(str) > 1 else str)
            return str


        latexFormula = self.chemical_formula
        latexFormula = re.sub(r"(_(\d+))?([A-Z][a-z]*)(\d*)", setSubSup, latexFormula)
        latexFormula = re.sub(r"_(\d*)(plus|minus)", setPlusMinus, latexFormula)
        return "$" + latexFormula + "$"

    class Meta:
        db_table = u'molecules'
        verbose_name_plural = 'Molecules'

class Atom(Species):
    """Atomic species with local XSAMS XML override for ion/state hierarchy."""

    def XML(self):
        from vamdctap.generators import (
            NODEID,
            GetValue,
            checkXML,
            makePrimaryType,
            makeSourceRefs,
            makeOptionalTag,
            makeDataType,
            makeRepeatedDataType,
            makeAtomStateComponents,
            parityLabel,
        )

        def atom_state_xml(atom_state):
            cont, ret = checkXML(atom_state)
            if cont:
                return ret

            G = lambda name: GetValue(name, AtomState=atom_state)

            xml = []

            xml.append(
                makePrimaryType(
                    "AtomicState",
                    "AtomicState",
                    G,
                    extraAttr={
                        "stateID": "S%s-%s" % (G("NodeID"), G("AtomStateID")),
                        "auxillary": G("AtomStateAuxillary"),
                    },
                )
            )

            xml.append(makeSourceRefs(G("AtomStateRef")))
            xml.append(makeOptionalTag("Description", "AtomStateDescription", G))

            xml.append("<AtomicNumericalData>")
            xml.append(makeDataType("StateEnergy", "AtomStateEnergy", G))
            xml.append(makeDataType("IonizationEnergy", "AtomStateIonizationEnergy", G))
            xml.append(makeDataType("LandeFactor", "AtomStateLandeFactor", G))
            xml.append(makeDataType("QuantumDefect", "AtomStateQuantumDefect", G))
            xml.append(
                makeRepeatedDataType(
                    "LifeTime",
                    "AtomStateLifeTime",
                    G,
                    extraAttr={"decay": G("AtomStateLifeTimeDecay")},
                )
            )
            xml.append(makeDataType("Polarizability", "AtomStatePolarizability", G))

            statweig = G("AtomStateStatisticalWeight")
            if statweig:
                xml.append("<StatisticalWeight>%s</StatisticalWeight>" % statweig)

            xml.append(makeDataType("HyperfineConstantA", "AtomStateHyperfineConstantA", G))
            xml.append(makeDataType("HyperfineConstantB", "AtomStateHyperfineConstantB", G))
            xml.append("</AtomicNumericalData>")

            xml.append("<AtomicQuantumNumbers>")
            p = G("AtomStateParity")
            j = G("AtomStateTotalAngMom")
            k = G("AtomStateKappa")
            hfm = G("AtomStateHyperfineMomentum")
            mqn = G("AtomStateMagneticQuantumNumber")

            if p:
                xml.append("<Parity>%s</Parity>" % parityLabel(p))
            if j:
                xml.append("<TotalAngularMomentum>%s</TotalAngularMomentum>" % j)
            if k:
                xml.append("<Kappa>%s</Kappa>" % k)
            if hfm:
                xml.append("<HyperfineMomentum>%s</HyperfineMomentum>" % hfm)
            if mqn:
                xml.append("<MagneticQuantumNumber>%s</MagneticQuantumNumber>" % mqn)

            xml.append("</AtomicQuantumNumbers>")

            cont, ret = checkXML(atom_state, "CompositionXML")
            if cont:
                xml.append(ret)
            else:
                if hasattr(atom_state, "Components"):
                    xml.append(makePrimaryType("AtomicComposition", "AtomicStateComposition", G))
                    xml.append(makeAtomStateComponents(atom_state))
                    xml.append("</AtomicComposition>")

            xml.append("</AtomicState>")
            return "".join(xml)

        def ion_xml(ion):
            G = lambda name: GetValue(name, Atom=ion)

            xml = []
            xml.append(
                '<Ion speciesID="X%s-%s"><IonCharge>%s</IonCharge>'
                % (NODEID, G("AtomSpeciesID"), G("AtomIonCharge"))
            )
            xml.append(makeOptionalTag("IsoelectronicSequence", "AtomIsoelectronicSequence", G))

            for atom_state in getattr(ion, "States", []):
                xml.append(atom_state_xml(atom_state))

            xml.append("<InChI>%s</InChI>" % G("AtomInchi"))
            xml.append("<InChIKey>%s</InChIKey>" % G("AtomInchiKey"))
            xml.append("</Ion>")
            return "".join(xml)

        G = lambda name: GetValue(name, Atom=self)

        xml = []
        xml.append("<Atom>")
        xml.append("<ChemicalElement>")
        xml.append("<NuclearCharge>%s</NuclearCharge>" % G("AtomNuclearCharge"))
        xml.append("<ElementSymbol>%s</ElementSymbol>" % G("AtomSymbol"))
        xml.append("</ChemicalElement>")

        xml.append("<Isotope>")

        #amn = G("AtomMassNumber")
        has_mass_data = getattr(self, "HasMassData", False)

        if has_mass_data:
            xml.append("<IsotopeParameters>")

            xml.append("<MassNumber>%s</MassNumber>" % self.MassNumber)

            xml.append('<Mass><Value units="%s">%s</Value></Mass>' % (
                getattr(self, "MassUnit", "amu"),
                getattr(self, "MassValue", "")
            ))

            xml.append(makeOptionalTag("NuclearSpin", "AtomNuclearSpin", G))
            xml.append("</IsotopeParameters>")

        for ion in getattr(self, "Ions", []):
            xml.append(ion_xml(ion))

        xml.append("</Isotope>")
        xml.append("</Atom>")

        return "".join(xml)

    class Meta:
        db_table = u'atoms'
        verbose_name_plural = 'Atoms'

class SpeciesState(PolymorphicModel):
    """Base state model linked to a species instance."""
    description = models.CharField(max_length=256, null=True, blank=True)
    species = models.ForeignKey(Species, on_delete=models.CASCADE)
    def __str__(self):
        return "%s - %s" % (self.species.name, self._get_description() )
    def __unicode__(self):
        return "%s - %s" % (self.species.name, self._get_description() )
    class Meta:
        db_table = u'speciesstates'

class AtomicState(SpeciesState):
    """Atomic electronic state identified here by principal quantum number."""
    qn = models.PositiveSmallIntegerField(null=True, blank=True)
    def _get_description(self):
        if (self.description==None or self.description==''):
            return "qn: %s" % (self.qn)
        else:
            return self.description
    class Meta:
        db_table = u'atomicstates'

class MolecularState(SpeciesState):
    """Molecular state placeholder (description is currently the key field)."""
    def _get_description(self):
        #if (self.description==None or self.description==''):
        #    return "r: %s, v: %s" % (self.n, self.l)
        #else:
        return self.description
    class Meta:
        db_table = u'molecularstates'

class CollisionType(models.Model):
    name = models.CharField(max_length=64)
    iaea_code = models.CharField(max_length=64, null=True, unique=True, error_messages={'unique':"This code is already associated with another collision type"})
    vamdc_code = models.CharField(max_length=64, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    def __str__(self):
        return "%s" % (self.name, )
    def __unicode__(self):
        return "%s" % (self.name, )
    class Meta:
        db_table = u'collisiontypes'

class Collision(models.Model):
    reactants = models.ManyToManyField(SpeciesState, related_name="reactants")
    products = models.ManyToManyField(SpeciesState, related_name="products")
    collision_type = models.ForeignKey(CollisionType, on_delete=models.CASCADE)
    description = models.TextField(null=True, blank=True)
    lastmodified = models.DateTimeField(default=timezone.now)
    def __str__(self):
        return "id: %s %s" % (self.id, self._get_description() )
    def __unicode__(self):
        return "id: %s %s" % (self.id, self._get_description() )
    def _get_description(self):
        if (self.description==None or self.description==''):
            return "reactants: %s; products: %s; process: %s" % \
                    ([r.species.stoichiometric_formula or r.species.chemical_formula + " " +
                        str(r._get_description()) for r in self.reactants.all()],
                        [p.species.stoichiometric_formula or p.species.chemical_formula + " " +
                            str(p._get_description()) for p in self.products.all()],
                        self.collision_type.name)
        else:
            return self.description
    class Meta:
        db_table = u'collisions'

class Author(models.Model):
    name = models.CharField(max_length=128)
    institution = models.CharField(max_length=256, null=True, blank=True)
    def __str__(self):
        return "%s" % (self.name)
    def __unicode__(self):
        return "%s" % (self.name)
    class Meta:
        db_table= u'authors'
        ordering = ['name']

class Source(models.Model):
    CATEGORY_CHOICES = (
            ('book', 'book'),
            ('database', 'database'),
            ('journal', 'journal'),
            ('preprint', 'preprint'),
            ('proceedings', 'proceedings'),
            ('report', 'report'),
            ('thesis', 'thesis'),
            ('private communication', 'private communication'),
            ('vamdc node', 'vamdc node'),
            )
    category = models.CharField(max_length=32, choices=CATEGORY_CHOICES, default='journal')
    article_number = models.CharField(max_length=128, null=True, blank=True, help_text="""Article number, journal-specific article identifier, may contain any string""")
    digital_object_id = models.CharField(max_length=128, null=True, blank=True, help_text="""Digital Object Identifier. Example: doi:10.1016/j.adt.2007.11.003""")
    title = models.CharField(max_length=256, help_text="""Title""")
    source_id = models.CharField(max_length=128, null=True, blank=True)
    publisher = models.CharField(max_length=256, null=True, blank=True, help_text="""Publisher of a bibliographic reference. Example: IOP Publishing Ltd""")
    authors = models.ManyToManyField(Author, related_name="sources")
    uri = models.CharField(max_length=256, null=True, blank=True, help_text="""A Uniform Resource Identifier of a bibliographic reference. Example: http://www.iop.org/EJ/abstract/0953-4075/41/10/105002""")
    page_begin = models.CharField(max_length=16, null=True, blank=True, help_text="""Initial page of a bibliographic reference. Example: 22""")
    page_end = models.CharField(max_length=16, null=True, blank=True, help_text="""Final page of a bibliographic reference. Example: 23""")
    volume = models.CharField(max_length=128, null=True, blank=True, help_text="""Volume of the bibliographic reference. Example: 72A""")
    source_name = models.CharField(max_length=256, null=True, blank=True, help_text="""Bibliographic reference name. Example: Physical Review""")
    bibtex = models.CharField(max_length=1024, null=True, blank=True, help_text="""BibTeX representation of reference, for those who already have it in database""")
    comments = models.CharField(max_length=1024, null=True, blank=True)
    year = models.CharField(max_length=16, null=True, blank=True)

    def __str__(self):
        if len(self.title) > 0 :
            return "%s" % self.title
        return "id: %s %s" % (self.id, self.comments)
    def __unicode__(self):
        if len(self.title) > 0 :
            return "%s" % self.title
        return "id: %s %s" % (self.id, self.comments)
    class Meta:
        db_table= u'sources'

class DataSource(models.Model):
    sources = models.ManyToManyField(Source, related_name="data_sources")
    collisions = models.ManyToManyField(Collision, related_name="data_sources")
    description = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.description or "DataSource %s" % self.id

    class Meta:
        db_table = u'datasources'

class DataList(models.Model):
    count =  models.IntegerField(null=True, blank=True)
    data_values = models.TextField(null=True, blank=True, help_text="""Space delimited values""")
    unit = models.CharField(max_length=16, null=True, blank=True)
    parameter = models.CharField(max_length=32, null=True, blank=True)
    description = models.CharField(max_length=256, null=True, blank=True)
    def __str__(self):
        return "id: %s %s" % (self.id, self.description)
    def __unicode__(self):
        return "id: %s %s" % (self.id, self.description)

    class Meta:
        db_table= u'datalists'

class TabulatedData(models.Model):
    collision = models.ForeignKey(Collision, null=True, blank=True, on_delete=models.CASCADE)
    y = models.ManyToManyField(DataList, related_name="tabulated_data_y", help_text="")
    x = models.ManyToManyField(DataList, related_name="tabulated_data_x", help_text="")
    description = models.CharField(max_length=256, null=True, blank=True)

    def __str__(self):
        return "id: %s %s" % (self.id, self.description)
    def __unicode__(self):
        return "id: %s %s" % (self.id, self.description)
    '''
    def XML(self):
        def axis_structure(axis):
            return '<%s units="%s" parameter="%s">\
                    <DataList count="%s">%s</DataList></%s>' % \
                    (axis, obj_.unit, obj_.parameter, str(obj_.count), obj_.data_values, axis)
        xml = '<TabulatedData>'
        for source in self.dataset.sources.all():
            xml += '<SourceRef>BAcol-%s</SourceRef>' % source.source_id
        for obj_ in self.x.all():
            xml += axis_structure('X')
        for obj_ in self.y.all():
            xml += axis_structure('Y')
        xml += '</TabulatedData>'
        return xml
    '''
    def XML(self):
        def axis_structure(axis):
            return '<%s units="%s" parameter="%s"><DataList count="%s">%s</DataList></%s>' % (
                axis, obj_.unit, obj_.parameter, str(obj_.count), obj_.data_values, axis
            )

        xml = '<TabulatedData>'

        source_ids = set()

        if self.collision:
            for datasource in self.collision.data_sources.all():
                for source in datasource.sources.all():
                    if source.source_id not in source_ids:
                        source_ids.add(source.source_id)
                        xml += '<SourceRef>BAcol-%s</SourceRef>' % source.source_id

        for obj_ in self.x.all():
            xml += axis_structure('X')

        for obj_ in self.y.all():
            xml += axis_structure('Y')

        xml += '</TabulatedData>'
        return xml

    class Meta:
        db_table= u'tabulateddata'
        verbose_name_plural = 'Tabulated data'
