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
        operation_description="Recupera informações de um sensor específico",
        responses={
            200: openapi.Response(
                description="Detalhes do sensor",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'sensor_name': openapi.Schema(type=openapi.TYPE_STRING),
                        'location': openapi.Schema(type=openapi.TYPE_STRING),
                        'channel': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'min_temperature': openapi.Schema(type=openapi.TYPE_NUMBER, nullable=True),
                        'max_temperature': openapi.Schema(type=openapi.TYPE_NUMBER, nullable=True),
                        'min_humidity': openapi.Schema(type=openapi.TYPE_NUMBER, nullable=True),
                        'max_humidity': openapi.Schema(type=openapi.TYPE_NUMBER, nullable=True),
                        'thermohygrometer_id': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'thermohygrometer_name': openapi.Schema(type=openapi.TYPE_STRING),
                    }
                )
            ),
            404: "Sensor não encontrado"
        }
    )
    def retrieve(self, request, pk=None):
        try:
            sensor = SensorModel.objects.get(id=pk)
            data = {
                'id': sensor.id,
                'sensor_name': sensor.sensor_name,
                'location': sensor.location,
                'channel': sensor.channel,
                'min_temperature': sensor.min_temperature,
                'max_temperature': sensor.max_temperature,
                'min_humidity': sensor.min_humidity,
                'max_humidity': sensor.max_humidity,
                'sensor_sn': sensor.sensor_sn,
                'sensor_pn': sensor.sensor_pn,
                'thermohygrometer_id': sensor.instrument.id,
                'thermohygrometer_name': sensor.instrument.instrument_name,
                'calibration_certificate_id': sensor.calibration_certificate.id if sensor.calibration_certificate else None,
            }
            return Response(self.get_versioned_response(request, data))
        except SensorModel.DoesNotExist:
            return Response(
                self.get_versioned_response(request, {'error': 'Sensor not found'}),
                status=status.HTTP_404_NOT_FOUND
            )
    
    @swagger_auto_schema(
        operation_description="Cria um novo sensor",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['thermohygrometer_id', 'sensor_name', 'channel'],
            properties={
                'thermohygrometer_id': openapi.Schema(type=openapi.TYPE_INTEGER),
                'sensor_name': openapi.Schema(type=openapi.TYPE_STRING),
                'location': openapi.Schema(type=openapi.TYPE_STRING),
                'channel': openapi.Schema(type=openapi.TYPE_INTEGER),
                'min_temperature': openapi.Schema(type=openapi.TYPE_NUMBER, nullable=True),
                'max_temperature': openapi.Schema(type=openapi.TYPE_NUMBER, nullable=True),
                'min_humidity': openapi.Schema(type=openapi.TYPE_NUMBER, nullable=True),
                'max_humidity': openapi.Schema(type=openapi.TYPE_NUMBER, nullable=True),
                'sensor_sn': openapi.Schema(type=openapi.TYPE_STRING, nullable=True),
                'sensor_pn': openapi.Schema(type=openapi.TYPE_STRING, nullable=True),
                'calibration_certificate_id': openapi.Schema(type=openapi.TYPE_INTEGER, nullable=True),
            }
        ),
        responses={
            201: "Sensor criado com sucesso",
            400: "Dados inválidos",
            404: "Termohigrômetro não encontrado"
        }
    )
    def create(self, request):
        try:
            thermohygrometer_id = request.data.get('thermohygrometer_id')
            thermohygrometer = ThermohygrometerModel.objects.get(id=thermohygrometer_id)
            
            # Check if channel is already in use for this thermohygrometer
            channel = request.data.get('channel')
            if SensorModel.objects.filter(instrument=thermohygrometer, channel=channel).exists():
                return Response(
                    self.get_versioned_response(request, {'error': 'Channel already in use for this thermohygrometer'}),
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Create new sensor
            sensor = SensorModel.objects.create(
                instrument=thermohygrometer,
                sensor_name=request.data.get('sensor_name'),
                location=request.data.get('location'),
                channel=channel,
                min_temperature=request.data.get('min_temperature'),
                max_temperature=request.data.get('max_temperature'),
                min_humidity=request.data.get('min_humidity'),
                max_humidity=request.data.get('max_humidity'),
                sensor_sn=request.data.get('sensor_sn'),
                sensor_pn=request.data.get('sensor_pn'),
            )
            
            # Add calibration certificate if provided
            calibration_certificate_id = request.data.get('calibration_certificate_id')
            if calibration_certificate_id:
                from fluke_data.models import CalibrationCertificateModel
                try:
                    certificate = CalibrationCertificateModel.objects.get(id=calibration_certificate_id)
                    sensor.calibration_certificate = certificate
                    sensor.save()
                except CalibrationCertificateModel.DoesNotExist:
                    pass  # Ignore if certificate doesn't exist
            
            return Response(
                self.get_versioned_response(request, {'id': sensor.id, 'message': 'Sensor created successfully'}),
                status=status.HTTP_201_CREATED
            )
        except ThermohygrometerModel.DoesNotExist:
            return Response(
                self.get_versioned_response(request, {'error': 'Thermohygrometer not found'}),
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                self.get_versioned_response(request, {'error': str(e)}),
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @swagger_auto_schema(
        operation_description="Atualiza um sensor existente",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'sensor_name': openapi.Schema(type=openapi.TYPE_STRING),
                'location': openapi.Schema(type=openapi.TYPE_STRING),
                'min_temperature': openapi.Schema(type=openapi.TYPE_NUMBER, nullable=True),
                'max_temperature': openapi.Schema(type=openapi.TYPE_NUMBER, nullable=True),
                'min_humidity': openapi.Schema(type=openapi.TYPE_NUMBER, nullable=True),
                'max_humidity': openapi.Schema(type=openapi.TYPE_NUMBER, nullable=True),
                'sensor_sn': openapi.Schema(type=openapi.TYPE_STRING, nullable=True),
                'sensor_pn': openapi.Schema(type=openapi.TYPE_STRING, nullable=True),
                'calibration_certificate_id': openapi.Schema(type=openapi.TYPE_INTEGER, nullable=True),
            }
        ),
        responses={
            200: "Sensor atualizado com sucesso",
            400: "Dados inválidos",
            404: "Sensor não encontrado"
        }
    )
    def update(self, request, pk=None):
        try:
            sensor = SensorModel.objects.get(id=pk)
            
            # Update fields
            if 'sensor_name' in request.data:
                sensor.sensor_name = request.data.get('sensor_name')
            if 'location' in request.data:
                sensor.location = request.data.get('location')
            if 'min_temperature' in request.data:
                sensor.min_temperature = request.data.get('min_temperature')
            if 'max_temperature' in request.data:
                sensor.max_temperature = request.data.get('max_temperature')
            if 'min_humidity' in request.data:
                sensor.min_humidity = request.data.get('min_humidity')
            if 'max_humidity' in request.data:
                sensor.max_humidity = request.data.get('max_humidity')
            if 'sensor_sn' in request.data:
                sensor.sensor_sn = request.data.get('sensor_sn')
            if 'sensor_pn' in request.data:
                sensor.sensor_pn = request.data.get('sensor_pn')
            
            # Update calibration certificate if provided
            if 'calibration_certificate_id' in request.data:
                calibration_certificate_id = request.data.get('calibration_certificate_id')
                if calibration_certificate_id:
                    from fluke_data.models import CalibrationCertificateModel
                    try:
                        certificate = CalibrationCertificateModel.objects.get(id=calibration_certificate_id)
                        sensor.calibration_certificate = certificate
                    except CalibrationCertificateModel.DoesNotExist:
                        pass  # Ignore if certificate doesn't exist
                else:
                    sensor.calibration_certificate = None
            
            sensor.save()
            return Response(
                self.get_versioned_response(request, {'message': 'Sensor updated successfully'}),
                status=status.HTTP_200_OK
            )
        except SensorModel.DoesNotExist:
            return Response(
                self.get_versioned_response(request, {'error': 'Sensor not found'}),
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                self.get_versioned_response(request, {'error': str(e)}),
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @swagger_auto_schema(
        operation_description="Remove um sensor",
        responses={
            200: "Sensor removido com sucesso",
            404: "Sensor não encontrado"
        }
    )
    def destroy(self, request, pk=None):
        try:
            sensor = SensorModel.objects.get(id=pk)
            sensor.delete()
            # Return a JSON response instead of empty 204
            return Response(
                self.get_versioned_response(request, {'success': True, 'message': 'Sensor deleted successfully'}),
                status=status.HTTP_200_OK
            )
        except SensorModel.DoesNotExist:
            return Response(
                self.get_versioned_response(request, {'error': 'Sensor not found'}),
                status=status.HTTP_404_NOT_FOUND
            )
        
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
