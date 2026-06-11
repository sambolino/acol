# encoding: utf-8
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
    molecular_weight = models.FloatField(null=True, blank=True, error_messages={'invalid': "Please enter a valid float number"})

    def formula(self):
        return self.stoichiometric_formula or self.chemical_formula or self.name

    def __str__(self):
        return "%s" % self.formula()

    def __unicode__(self):
        return self.__str__()

    class Meta:
        db_table = u'species'

class Molecule(Species):
    """Molecular species with helper for XSAMS-friendly formula rendering."""

    # code taken from wadis node
    def getLatexFormula(self):
        # See http://www.physicsforums.com/misc/howtolatex.pdf
        # See http://vamdc.org/documents/standards/dataModel/vamdcxsams/speciesMolecules.html#molecule

        if self.chemical_formula is None:
            return None

        def setSubSup(matchObj):
            str_ = ''
            if matchObj.group(2):
                s = matchObj.group(2)
                if int(s) > 1:
                    str_ += "^" + ("{%s}" % s if len(s) > 1 else s)
            str_ += matchObj.group(3)
            if matchObj.group(4):
                s = matchObj.group(4)
                if int(s) > 1:
                    str_ += "_" + ("{%s}" % s if len(s) > 1 else s)
            return str_

        def setPlusMinus(matchObj):
            str_ = ''
            if matchObj.group(1):
                s = matchObj.group(1)
                if int(s) > 1:
                    str_ += s
            if matchObj.group(2):
                s = matchObj.group(2)
                if s == 'plus':
                    str_ += '+'
                elif s == 'minus':
                    str_ += '-'
            str_ = "^" + ("{%s}" % str_ if len(str_) > 1 else str_)
            return str_

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

    def _get_description(self):
        return self.description or ""

    def __str__(self):
        species_text = str(self.species)
        description = self._get_description()

        if description:
            return "%s (%s)" % (species_text, description)

        return species_text

    def __unicode__(self):
        return self.__str__()

    class Meta:
        db_table = u'speciesstates'


class AtomicState(SpeciesState):
    """Atomic electronic state identified here by principal quantum number."""
    qn = models.PositiveSmallIntegerField(null=True, blank=True)

    def _get_description(self):
        if self.description:
            desc = self.description.strip()

            # Ground state is usually noise in compact reaction tables.
            if desc.lower() == "ground state":
                return ""

            return desc

        if self.qn is not None:
            return "n=%s" % self.qn

        return ""

    class Meta:
        db_table = u'atomicstates'


class MolecularState(SpeciesState):
    """Molecular state placeholder (description is currently the key field)."""

    def _get_description(self):
        if not self.description:
            return ""

        desc = self.description.strip()

        # Again, ground state is mostly visual noise.
        if desc.lower() == "ground state":
            return ""

        return desc

    class Meta:
        db_table = u'molecularstates'


class CollisionType(models.Model):
    name = models.CharField(max_length=64)
    iaea_code = models.CharField(max_length=64, null=True, unique=True, error_messages={'unique': "This code is already associated with another collision type"})
    vamdc_code = models.CharField(max_length=64, null=True, blank=True)
    has_electron_reactant = models.BooleanField(default=False)
    has_electron_product = models.BooleanField(default=False)
    description = models.TextField(null=True, blank=True)

    def __str__(self):
        if self.iaea_code:
            return "%s — %s" % (self.iaea_code, self.name)

        return "%s" % self.name

    def __unicode__(self):
        return self.__str__()

    class Meta:
        db_table = u'collisiontypes'


class Collision(models.Model):
    reactants = models.ManyToManyField(SpeciesState, related_name="reactants")
    products = models.ManyToManyField(SpeciesState, related_name="products")
    collision_type = models.ForeignKey(CollisionType, on_delete=models.CASCADE)
    description = models.TextField(null=True, blank=True)
    lastmodified = models.DateTimeField(default=timezone.now)

    def reactant_strings(self):
        reactants = [str(reactant) for reactant in self.reactants.all()]

        if self.collision_type and self.collision_type.has_electron_reactant:
            reactants.append("e-")

        return reactants


    def product_strings(self):
        products = [str(product) for product in self.products.all()]

        if self.collision_type and self.collision_type.has_electron_product:
            products.append("e-")

        return products

    def reaction_string(self):
        return "%s → %s" % (
            " + ".join(self.reactant_strings()),
            " + ".join(self.product_strings())
        )


    def __str__(self):
        if self.description:
            return self.description

        return "%s [%s]" % (
            self.reaction_string(),
            str(self.collision_type)
        )

    def __unicode__(self):
        return self.__str__()

    class Meta:
        db_table = u'collisions'


class Author(models.Model):
    name = models.CharField(max_length=128)
    institution = models.CharField(max_length=256, null=True, blank=True)

    def __str__(self):
        return "%s" % self.name

    def __unicode__(self):
        return self.__str__()

    class Meta:
        db_table = u'authors'
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

    def acol_id(self):
        if self.source_id:
            return "BAcol-%s" % self.source_id

        return "Source %s" % self.id

    def __str__(self):
        parts = [self.acol_id()]

        if self.year:
            parts.append("(%s)" % self.year)

        if self.title:
            parts.append(self.title)
        elif self.comments:
            parts.append(self.comments)

        if self.digital_object_id:
            parts.append(self.digital_object_id)

        return " ".join(parts)

    def __unicode__(self):
        return self.__str__()

    class Meta:
        db_table = u'sources'


class DataSource(models.Model):
    sources = models.ManyToManyField(Source, related_name="data_sources")
    collisions = models.ManyToManyField(Collision, related_name="data_sources")
    description = models.TextField(null=True, blank=True)

    def __str__(self):
        if self.description:
            return self.description

        source_text = ", ".join([str(source) for source in self.sources.all()])

        if source_text:
            return "DataSource %s: %s" % (self.id, source_text)

        return "DataSource %s" % self.id

    def __unicode__(self):
        return self.__str__()

    class Meta:
        db_table = u'datasources'


class DataList(models.Model):
    count = models.IntegerField(null=True, blank=True)
    data_values = models.TextField(null=True, blank=True, help_text="""Space delimited values""")
    unit = models.CharField(max_length=16, null=True, blank=True)
    parameter = models.CharField(max_length=32, null=True, blank=True)
    description = models.CharField(max_length=256, null=True, blank=True)

    def values_as_floats(self):
        if not self.data_values:
            return []

        values = []

        for value in self.data_values.split():
            try:
                values.append(float(value))
            except ValueError:
                # Some legacy datasets may contain non-float tokens.
                # Ignore them for plotting/ranges.
                pass

        return values

    def endpoint_string(self):
        """
        First → last value, preserving original data order.

        This is appropriate for x-axes such as temperature or energy.
        Do NOT use min/max here, because some axes may be descending or
        intentionally ordered.
        """
        values = self.values_as_floats()

        if not values:
            return ""

        if len(values) == 1:
            return "%g" % values[0]

        return "%g – %g" % (values[0], values[-1])

    def minmax_string(self):
        """
        Numeric min/max range.

        Useful for y-values, but not for the default human representation.
        """
        values = self.values_as_floats()

        if not values:
            return ""

        if len(values) == 1:
            return "%g" % values[0]

        return "%g – %g" % (min(values), max(values))

    def axis_string(self):
        parts = []

        if self.parameter:
            parts.append(self.parameter)

        if self.unit:
            parts.append("[%s]" % self.unit)

        if parts:
            return " ".join(parts)

        if self.description:
            return self.description

        return "DataList %s" % self.id

    def __str__(self):
        return self.axis_string()

    def __unicode__(self):
        return self.__str__()

    class Meta:
        db_table = u'datalists'


class TabulatedData(models.Model):
    collision = models.ForeignKey(Collision, null=True, blank=True, on_delete=models.CASCADE)
    y = models.ManyToManyField(DataList, related_name="tabulated_data_y", help_text="")
    x = models.ManyToManyField(DataList, related_name="tabulated_data_x", help_text="")
    description = models.CharField(max_length=256, null=True, blank=True)

    def first_x(self):
        try:
            return self.x.all()[0]
        except IndexError:
            return None

    def first_y(self):
        try:
            return self.y.all()[0]
        except IndexError:
            return None

    def __str__(self):
        if self.description:
            return self.description

        if self.collision:
            return "%s" % str(self.collision)

        return "TabulatedData %s" % self.id

    def __unicode__(self):
        return self.__str__()

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
        db_table = u'tabulateddata'
