from django.conf.urls import include, url
from django.contrib import admin
from node.views import index

admin.autodiscover()

urlpatterns = [

    url(r'^admin/', admin.site.urls),
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
    url(r'^tap/', include('vamdctap.urls')),
    #(r'^accuracy/(?P<year>\d{4})/$', 'accuracytype_model'),
    url(r'', include('node.urls')),
    url(r'^xsams/$', index, name='index'),
]

handler500 = 'vamdctap.views.tapServerError'
#handler404 = 'vamdctap.views.tapNotFoundError'
