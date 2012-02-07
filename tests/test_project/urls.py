from django.conf.urls.defaults import *


urlpatterns = patterns('',
    url(r'/', include('test_project.apps.testapp.urls'))
)
