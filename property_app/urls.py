from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('api/<str:section>', views.api_section, name="api_section"),
    path('amenities', views.ui_section, name="ui_amenities", kwargs={'section': 'amenities'})
]
