"""
Views for calibration certificate management.
This module provides endpoints for managing calibration certificates,
including CRUD operations and association with thermohygrometers.
"""


from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status, viewsets
from rest_framework.authentication import (BasicAuthentication,
                                           SessionAuthentication)
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.versioning import URLPathVersioning

from fluke_data.models import (CalibrationCertificateModel,
                              SensorModel,
                              ThermohygrometerModel)


class CertificateViewSet(viewsets.ViewSet):
    authentication_classes = [SessionAuthentication, BasicAuthentication]
    permission_classes = [IsAuthenticated]
    versioning_class = URLPathVersioning

    def get_versioned_response(self, request, data):
        if request.version == 'v1':
            return data
        return data

    @swagger_auto_schema(
        operation_description="Lista todos os certificados de calibração",
        responses={
            200: openapi.Response(
                description="Lista de certificados",
                schema=openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                            'certificate_number': openapi.Schema(type=openapi.TYPE_STRING),
                            'calibration_date': openapi.Schema(type=openapi.TYPE_STRING, format='date'),
                            'next_calibration_date': openapi.Schema(type=openapi.TYPE_STRING, format='date'),
                            'associated_instrument': openapi.Schema(type=openapi.TYPE_STRING),
                            'associated_sensor': openapi.Schema(type=openapi.TYPE_STRING)
                        }
                    )
                )
            )
        }
    )
    def list(self, request):
        certificates = CalibrationCertificateModel.objects.all().order_by('-calibration_date')
        data = []
        
        for cert in certificates:
            sensor = cert.sensormodel_set.first() if hasattr(cert, 'sensormodel_set') else None
            
            cert_data = {
                'id': cert.id,
                'certificate_number': cert.certificate_number,
                'calibration_date': cert.calibration_date,
                'next_calibration_date': cert.next_calibration_date,
                'associated_sensor': sensor.sensor_name if sensor else None,
                'associated_instrument': sensor.instrument.instrument_name if sensor else None
            }
            data.append(cert_data)
            
        return Response(self.get_versioned_response(request, data))

    @swagger_auto_schema(
        operation_description="Cria um novo certificado de calibração",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=[
                'calibration_date', 'next_calibration_date', 'certificate_number',
                'temp_indication_point_1', 'temp_correction_1',
                'temp_indication_point_2', 'temp_correction_2',
                'temp_indication_point_3', 'temp_correction_3',
                'humidity_indication_point_1', 'humidity_correction_1',
                'humidity_indication_point_2', 'humidity_correction_2',
                'humidity_indication_point_3', 'humidity_correction_3',
                'temp_uncertainty', 'humidity_uncertainty'
            ],
            properties={
                'calibration_date': openapi.Schema(type=openapi.TYPE_STRING, format='date'),
                'next_calibration_date': openapi.Schema(type=openapi.TYPE_STRING, format='date'),
                'certificate_number': openapi.Schema(type=openapi.TYPE_STRING),
                'temp_indication_point_1': openapi.Schema(type=openapi.TYPE_NUMBER),
                'temp_correction_1': openapi.Schema(type=openapi.TYPE_NUMBER),
                'temp_indication_point_2': openapi.Schema(type=openapi.TYPE_NUMBER),
                'temp_correction_2': openapi.Schema(type=openapi.TYPE_NUMBER),
                'temp_indication_point_3': openapi.Schema(type=openapi.TYPE_NUMBER),
                'temp_correction_3': openapi.Schema(type=openapi.TYPE_NUMBER),
                'humidity_indication_point_1': openapi.Schema(type=openapi.TYPE_NUMBER),
                'humidity_correction_1': openapi.Schema(type=openapi.TYPE_NUMBER),
                'humidity_indication_point_2': openapi.Schema(type=openapi.TYPE_NUMBER),
                'humidity_correction_2': openapi.Schema(type=openapi.TYPE_NUMBER),
                'humidity_indication_point_3': openapi.Schema(type=openapi.TYPE_NUMBER),
                'humidity_correction_3': openapi.Schema(type=openapi.TYPE_NUMBER),
                'temp_uncertainty': openapi.Schema(type=openapi.TYPE_NUMBER),
                'humidity_uncertainty': openapi.Schema(type=openapi.TYPE_NUMBER),
            }
        ),
        responses={
            201: 'Certificado criado com sucesso',
            400: 'Dados inválidos'
        }
    )
    def create(self, request):
        try:
            certificate = CalibrationCertificateModel.objects.create(
                **request.data)
            return Response(
                self.get_versioned_response(
                    request, {'success': True, 'id': certificate.id}),
                status=status.HTTP_201_CREATED
            )
        except Exception as e:
            return Response(
                self.get_versioned_response(request, {'error': str(e)}),
                status=status.HTTP_400_BAD_REQUEST
            )

    @swagger_auto_schema(
        operation_description="Exclui um certificado de calibração",
        responses={
            200: 'Certificado excluído com sucesso',
            404: 'Certificado não encontrado'
        }
    )
    def destroy(self, request, pk=None):
        try:
            certificate = CalibrationCertificateModel.objects.get(id=pk)

            # Remove reference of the certificate from sensors
            sensors = SensorModel.objects.filter(calibration_certificate=certificate)
            for sensor in sensors:
                sensor.calibration_certificate = None
                sensor.save()

            certificate.delete()
            return Response(self.get_versioned_response(request, {'success': True}))
        except CalibrationCertificateModel.DoesNotExist:
            return Response(
                self.get_versioned_response(
                    request, {'error': 'Certificate not found'}),
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                self.get_versioned_response(request, {'error': str(e)}),
                status=status.HTTP_400_BAD_REQUEST
            )
