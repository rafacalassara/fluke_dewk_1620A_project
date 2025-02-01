# fluke_data/urls.py
from django.urls import path, include
from django.views.generic import TemplateView
from . import views
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from .api import urls as api_urls

# Adicione esta configuração antes das URL patterns
schema_view = get_schema_view(
    openapi.Info(
        title="Fluke Data API",
        default_version='v1',
        description="API documentation for Fluke Data System",
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="contact@fluke.local"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    # Regular views
    path('', views.RealTimeDataView.as_view(), name='real_time_data'),
    path('manage-thermohygrometers/', views.ManageThermohygrometersView.as_view(),
         name='manage_thermohygrometers'),
    path('update-thermohygrometer/<int:pk>/',
         views.UpdateThermohygrometerView.as_view(), name='update_thermohygrometer'),
    path('data-visualization/', views.DataVisualizationView.as_view(),
         name='data_visualization'),
    path('display-measures/', views.DisplayMeasuresView.as_view(),
         name='display_measures'),

    # User management
    path('manage-users/', views.ManageUsersView.as_view(), name='manage_users'),
    path('create-user/', views.CreateUserView.as_view(), name='create_user'),
    path('update-user/<int:pk>/', views.UpdateUserView.as_view(), name='update_user'),
    path('delete-user/<int:pk>/', views.DeleteUserView.as_view(), name='delete_user'),
    path('login/', views.LoginView.as_view(), name='login'),

    # Certificate management (using API)
    path('manage-certificates/', views.ManageCertificatesView.as_view(),
         name='manage_all_certificates'),
    path('create-certificate/', views.CreateCertificateView.as_view(),
         name='create_certificate'),

    # Intelligence
    path('intelligence/', views.IntelligenceView.as_view(), name='intelligence'),

    # API endpoints
    path('api/', include(api_urls)),

    # Swagger/OpenAPI URLs
    path('swagger<format>/', schema_view.without_ui(cache_timeout=0),
         name='schema-json'),
    path('swagger/', schema_view.with_ui('swagger',
         cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc',
         cache_timeout=0), name='schema-redoc'),
]
