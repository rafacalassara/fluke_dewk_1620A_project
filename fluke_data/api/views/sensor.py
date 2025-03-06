from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status, viewsets
from rest_framework.authentication import (BasicAuthentication, SessionAuthentication)
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.versioning import URLPathVersioning

from fluke_data.models import ThermohygrometerModel, SensorModel

class SensorViewSet(viewsets.ViewSet):
    authentication_classes = [SessionAuthentication, BasicAuthentication]
    permission_classes = [IsAuthenticated]
    versioning_class = URLPathVersioning
    
    def get_versioned_response(self, request, data):
        if request.version == 'v1':
            return data
        return data
        
    @swagger_auto_schema(
        operation_description="Lista todos os sensores",
        responses={
            200: openapi.Response(
                description="Lista de sensores",
                schema=openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                            'sensor_name': openapi.Schema(type=openapi.TYPE_STRING),
                            'location': openapi.Schema(type=openapi.TYPE_STRING),
                            'channel': openapi.Schema(type=openapi.TYPE_INTEGER),
                            'thermohygrometer_id': openapi.Schema(type=openapi.TYPE_INTEGER),
                            'thermohygrometer_name': openapi.Schema(type=openapi.TYPE_STRING),
                        }
                    )
                )
            )
        }
    )
    def list(self, request):
        sensors = SensorModel.objects.all().order_by('instrument__instrument_name', 'channel')
        data = [
            {
                'id': sensor.id,
                'sensor_name': sensor.sensor_name,
                'location': sensor.location,
                'channel': sensor.channel,
                'thermohygrometer_id': sensor.instrument.id,
                'thermohygrometer_name': sensor.instrument.instrument_name,
            }
            for sensor in sensors
        ]
        return Response(self.get_versioned_response(request, data))
        
    @swagger_auto_schema(
        operation_description="Lista sensores de um termohigrômetro específico",
        responses={
            200: openapi.Response(
                description="Lista de sensores do termohigrômetro",
                schema=openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                            'sensor_name': openapi.Schema(type=openapi.TYPE_STRING),
                            'location': openapi.Schema(type=openapi.TYPE_STRING),
                            'channel': openapi.Schema(type=openapi.TYPE_INTEGER),
                        }
                    )
                )
            ),
            404: "Termohigrômetro não encontrado"
        }
    )
    @action(detail=False, methods=['get'], url_path='by-instrument/(?P<thermohygrometer_id>[^/.]+)')
    def by_instrument(self, request, thermohygrometer_id=None):
        try:
            thermohygrometer = ThermohygrometerModel.objects.get(id=thermohygrometer_id)
            sensors = SensorModel.objects.filter(instrument=thermohygrometer).order_by('channel')
            
            data = [
                {
                    'id': sensor.id,
                    'sensor_name': sensor.sensor_name,
                    'location': sensor.location,
                    'channel': sensor.channel,
                }
                for sensor in sensors
            ]
            return Response(self.get_versioned_response(request, data))
        except ThermohygrometerModel.DoesNotExist:
            return Response(
                self.get_versioned_response(request, {'error': 'Thermohygrometer not found'}),
                status=status.HTTP_404_NOT_FOUND
            )
            
    # Adicione aqui mais métodos para criar, atualizar e excluir sensores
