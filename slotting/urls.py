from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^$', views.tool_home, name='tool_home'),
]
