from django.conf.urls import url
from node import views
from django.conf import settings

urlpatterns = [
    url(r'^$', views.index),
    url(r'^get_products/(?P<coll_iaea_code>[\w-]+)/$', views.get_products),
    url(r'^get_atoms/(?P<coll_iaea_code>[\w-]+)/$', views.get_atoms),
    url(r'^get_atoms_no_ions/(?P<coll_iaea_code>[\w-]+)/$', views.get_atoms_no_ions),
    url(r'^get_temps/(?P<coll_iaea_code>[\w-]+)/(?P<atom_inchi>[\w-]+)/$', views.get_temps),
    url(r'^plot/(?P<coll_iaea_code>[\w-]+)/(?P<atom_inchi>[\w-]+)/(?P<temperature_index>[\w.]+)/$', views.plot),
]
