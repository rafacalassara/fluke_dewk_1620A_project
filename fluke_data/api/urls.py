from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    CertificateViewSet,
    ExportDataViewSet,
    EnvironmentalAnalysisViewSet,
    ThermohygrometerViewSet
)

router = DefaultRouter()
router.register(
    r'thermohygrometers',
    ThermohygrometerViewSet,
    basename='api-thermohygrometer'
)
router.register(
    r'environmental-analysis',
    EnvironmentalAnalysisViewSet,
    basename='api-environmental-analysis'
)
router.register(
    r'export',
    ExportDataViewSet,
    basename='api-export'
)
router.register(
    r'certificates',
    CertificateViewSet,
    basename='api-certificate'
)

urlpatterns = [
    path('', include(router.urls)),
]
