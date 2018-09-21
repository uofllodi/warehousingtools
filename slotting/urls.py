from django.urls import path, include
from . import views

urlpatterns = [
    path('', views.tool_home, name='tool_home'),
    path('django-rq/', include('django_rq.urls')),
]
