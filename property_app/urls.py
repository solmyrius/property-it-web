from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('api/<str:section>', views.api_section, name="api_section"),
    path('sintesi', views.ui_section, name="ui_sintesi", kwargs={'section': 'sintesi'}),
    path('amenities', views.ui_section, name="ui_amenities", kwargs={'section': 'amenities'}),
    path('demography', views.ui_section, name="ui_demography", kwargs={'section': 'demography'}),
    path('scuole', views.ui_section, name="ui_scuole", kwargs={'section': 'scuole'}),
    path('scuola/<str:school_id>', views.ui_school, name="ui_school"),
    path('price', views.ui_section, name="ui_price", kwargs={'section': 'price'}),
]
