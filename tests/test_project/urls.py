try:
    from django.conf.urls.defaults import *
except ImportError:
    from django.conf.urls import *


urlpatterns = patterns('',
    url(r'/', include('test_app.urls'))
)
