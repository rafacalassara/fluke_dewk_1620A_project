from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ThermohygrometerViewSet,
    EnvironmentalAnalysisViewSet,
    ExportDataViewSet,
    CertificateViewSet
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
