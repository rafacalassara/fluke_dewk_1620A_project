from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    CertificateViewSet,
    ExportDataViewSet,
    EnvironmentalAnalysisViewSet,
    ThermohygrometerViewSet,
    CrewAnalysisViewSet
)
from fluke_data.api.views.sensor import SensorViewSet

# Create a router for v1
router_v1 = DefaultRouter()
router_v1.register(
    r'thermohygrometers',
    ThermohygrometerViewSet,
    basename='api-thermohygrometer'
)
router_v1.register(
    r'environmental-analysis',
    EnvironmentalAnalysisViewSet,
    basename='api-environmental-analysis'
)
router_v1.register(
    r'export',
    ExportDataViewSet,
    basename='api-export'
)
router_v1.register(
    r'certificates',
    CertificateViewSet,
    basename='api-certificate'
)
router_v1.register(
    r'crew-analysis',
    CrewAnalysisViewSet,
    basename='api-crew-analysis'
)
router_v1.register(
    r'sensors',
    SensorViewSet,
    basename='sensors'
)

# API URLs with versioning
urlpatterns = [
    path('v1/', include((router_v1.urls, 'v1'))),
]
