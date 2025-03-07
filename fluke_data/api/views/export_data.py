"""
Views for data export functionality.
This module provides endpoints for exporting measurement data to various formats,
currently supporting CSV exports with filtering by date range and sensor.
"""

import csv

from django.http import HttpResponse
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import viewsets
from rest_framework.authentication import (BasicAuthentication,
                                           SessionAuthentication)
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.versioning import URLPathVersioning

from fluke_data.models import MeasuresModel, SensorModel


class ExportDataViewSet(viewsets.ViewSet):
    authentication_classes = [SessionAuthentication, BasicAuthentication]
    permission_classes = [IsAuthenticated]
    versioning_class = URLPathVersioning

    def get_versioned_response(self, request, data):
        if request.version == 'v1':
            return data
        return data

    @swagger_auto_schema(
        operation_description="Exporta dados para CSV",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['sensor_id', 'start_date',
                      'start_time', 'end_date', 'end_time'],
            properties={
                'sensor_id': openapi.Schema(type=openapi.TYPE_INTEGER),
                'start_date': openapi.Schema(type=openapi.TYPE_STRING, format='date'),
                'start_time': openapi.Schema(type=openapi.TYPE_STRING, format='time'),
                'end_date': openapi.Schema(type=openapi.TYPE_STRING, format='date'),
                'end_time': openapi.Schema(type=openapi.TYPE_STRING, format='time'),
            }
        ),
        responses={
            200: openapi.Response(description="Arquivo CSV"),
            400: 'Parâmetros inválidos'
        }
    )
    @action(detail=False, methods=['post'], url_path='export-to-csv')
    def export_to_csv(self, request):
        try:
            sensor_id = request.data.get('sensor_id')
            start_date = request.data.get('start_date')
            start_time = request.data.get('start_time')
            end_date = request.data.get('end_date')
            end_time = request.data.get('end_time')

            if not all([sensor_id, start_date, start_time, end_date, end_time]):
                return Response(
                    self.get_versioned_response(
                        request, {'error': 'Missing required parameters'}),
                    status=400
                )

            selected_sensor = SensorModel.objects.get(id=sensor_id)
            start_datetime = f"{start_date} {start_time}"
            end_datetime = f"{end_date} {end_time}"

            # Query data by sensor directly
            data = MeasuresModel.objects.filter(
                sensor=selected_sensor,
                date__range=[start_datetime, end_datetime]
            ).order_by('-date')

            # Create filename based on sensor info
            filename = f"measured_data_{selected_sensor.sensor_name}_{start_date}_{end_date}.csv"

            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = f'attachment; filename="{filename}"'

            writer = csv.writer(response)
            writer.writerow([
                'Date',
                'Temperature (°C)', 
                'Corrected Temperature (°C)',
                'Humidity (%)', 
                'Corrected Humidity (%)'
            ])

            for measure in data:
                writer.writerow([
                    measure.date.strftime("%d/%m/%Y %H:%M"),
                    measure.temperature,
                    measure.corrected_temperature,
                    measure.humidity,
                    measure.corrected_humidity
                ])

            return response
        except SensorModel.DoesNotExist:
            return Response(
                self.get_versioned_response(
                    request, {'error': 'Sensor not found'}),
                status=404
            )
        except Exception as e:
            return Response(
                self.get_versioned_response(request, {'error': str(e)}),
                status=400
            )
