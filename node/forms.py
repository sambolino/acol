#from django import forms
import floppyforms as forms
from node.models import *

class NumberInput(forms.TextInput):
    input_type = 'number'

class Search_form(forms.Form):
    #AtomsSearch = forms.ModelChoiceField(queryset = Atom.objects.filter(ion_charge=0), label='Atom', to_field_name='inchikey')
    CollTypesXsams = forms.ModelChoiceField(queryset = CollisionType.objects.all(),
            label="Collision Type", to_field_name='iaea_code')
    SpeciesXsams = forms.ModelChoiceField(queryset = Species.objects.all(),
            label='Species (as product)', to_field_name='inchikey',
            widget = forms.Select(attrs={'disabled':'disabled'}))

class Plot_form(forms.Form):
    CollTypesPlot = forms.ModelChoiceField(queryset = CollisionType.objects.all(),
            label="Collision Type", to_field_name='iaea_code')
    AtomsPlot = forms.ModelChoiceField(queryset = Atom.objects.filter(ion_charge=0),
            label='Atom', to_field_name='inchikey', widget = forms.Select(attrs={'disabled':'disabled'}))
    TemperaturesPlot = forms.TypedChoiceField(label='Temperature',
            widget = forms.Select(attrs={'disabled':'disabled'}))
    #TemperaturesPlot = forms.TypedChoiceField(label='Temperature', choices = [], widget = forms.Select(attrs={'disabled':'disabled'}))
