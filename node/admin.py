from django.contrib import admin
from .models import \
    Atom, \
    Molecule, \
    AtomicState, \
    MolecularState, \
    Collision, \
    CollisionType, \
    DataSource, \
    TabulatedData, \
    DataList, \
    Source, \
    Author \

class SourceAdmin(admin.ModelAdmin):
    filter_horizontal = ("authors",)

admin.site.register(Atom)
admin.site.register(Molecule)
admin.site.register(AtomicState)
admin.site.register(MolecularState)
admin.site.register(Collision)
admin.site.register(CollisionType)
admin.site.register(DataSource)
admin.site.register(TabulatedData)
admin.site.register(DataList)
admin.site.register(Source, SourceAdmin)
admin.site.register(Author)

"""
ne radi - pokusaj da se filtriraju samo molekuli za molecularstates itd
https://books.agiliq.com/projects/django-admin-cookbook/en/latest/filter_fk_dropdown.html
anotacije ne rade u nasoj verziji djanga?
#@admin.register(MolecularState)
class MolecularStateAdmin(admin.ModelAdmin):

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "species":
            kwargs["queryset"] = models.Species.objects.filter(id__in=['1', '2'])
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
"""
