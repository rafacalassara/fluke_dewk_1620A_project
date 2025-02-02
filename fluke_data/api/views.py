import csv
import json
from collections import defaultdict
from datetime import datetime, timedelta

from django.db.models import Q
from django.http import HttpResponse
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status, viewsets
from rest_framework.authentication import (
    BasicAuthentication,
    SessionAuthentication
)
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.versioning import URLPathVersioning

from fluke_data.crews.crew import AnalyticalCrewFlow
from fluke_data.crews.tools.data_analysis_tools import (
    analyze_environmental_impact
)
from fluke_data.models import (
    CalibrationCertificateModel,
    MeasuresModel,
    ThermohygrometerModel
)
from fluke_data.visa_communication import Instrument


class ThermohygrometerViewSet(viewsets.ViewSet):
    authentication_classes = [SessionAuthentication, BasicAuthentication]
    permission_classes = [IsAuthenticated]
    versioning_class = URLPathVersioning

    def get_versioned_response(self, request, data):
        if request.version == 'v1':
            return data
        return data

    @swagger_auto_schema(
        operation_description="Lista todos os termo-higrômetros cadastrados",
        responses={
            200: openapi.Response(
                description="Lista de termo-higrômetros",
                schema=openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                            'pn': openapi.Schema(type=openapi.TYPE_STRING),
                            'sn': openapi.Schema(type=openapi.TYPE_STRING),
                            'instrument_name': openapi.Schema(type=openapi.TYPE_STRING),
                            'group_name': openapi.Schema(type=openapi.TYPE_STRING),
                        }
                    )
                )
            )
        }
    )
    def list(self, request):
        thermohygrometers = ThermohygrometerModel.objects.all().order_by('instrument_name')
        data = [
            {
                'id': thermo.id,
                'pn': thermo.pn,
                'sn': thermo.sn,
                'instrument_name': thermo.instrument_name,
                'group_name': thermo.group_name,
            }
            for thermo in thermohygrometers]
        return Response(self.get_versioned_response(request, data))

    @swagger_auto_schema(
        operation_description="Lista termo-higrômetros conectados",
        responses={
            200: openapi.Response(
                description="Lista de dispositivos conectados",
                schema=openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                            'pn': openapi.Schema(type=openapi.TYPE_STRING),
                            'sn': openapi.Schema(type=openapi.TYPE_STRING),
                            'instrument_name': openapi.Schema(type=openapi.TYPE_STRING),
                            'group_name': openapi.Schema(type=openapi.TYPE_STRING),
                        }
                    )
                )
            )
        }
    )
    @action(detail=False, methods=['get'])
    def connected(self, request):
        thermohygrometers = ThermohygrometerModel.objects.filter(
            is_connected=True).order_by('instrument_name')
        data = [
            {
                'id': thermo.id,
                'pn': thermo.pn,
                'sn': thermo.sn,
                'instrument_name': thermo.instrument_name,
                'group_name': thermo.group_name,
            }
            for thermo in thermohygrometers]
        return Response(self.get_versioned_response(request, data))

    @swagger_auto_schema(
        operation_description="Adiciona um novo termo-higrômetro",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['instrument_ip'],
            properties={
                'instrument_ip': openapi.Schema(type=openapi.TYPE_STRING),
            },
        ),
        responses={
            201: 'Dispositivo criado com sucesso',
            400: 'Dados inválidos'
        }
    )
    def create(self, request):
        instrument_ip = request.data.get('instrument_ip')
        try:
            instrument = Instrument(ip_address=instrument_ip)
            instrument.connect()
        except:
            return Response(
                self.get_versioned_response(
                    request, {'error': 'Instrument not found on given IP address.'}),
                status=status.HTTP_400_BAD_REQUEST
            )

        name = instrument.INSTRUMENT_NAME
        pn = instrument.PN
        sn = instrument.SN
        group_name = f"thermo_{pn}_{sn}"

        try:
            if instrument_ip and pn and sn:
                ThermohygrometerModel.objects.create(
                    ip_address=instrument_ip,
                    instrument_name=name,
                    pn=pn,
                    sn=sn,
                    group_name=group_name
                )
                return Response(
                    self.get_versioned_response(request, {'success': True}),
                    status=status.HTTP_201_CREATED
                )
        except:
            return Response(
                self.get_versioned_response(
                    request, {'error': 'Error adding to database.'}),
                status=status.HTTP_400_BAD_REQUEST
            )

        instrument.disconnect()

    @swagger_auto_schema(
        operation_description="Exclui um termo-higrômetro",
        responses={
            200: 'Dispositivo excluído com sucesso',
            404: 'Dispositivo não encontrado'
        }
    )
    def destroy(self, request, pk=None):
        try:
            thermo = ThermohygrometerModel.objects.get(id=pk)
            thermo.delete()
            return Response(self.get_versioned_response(request, {'success': True}))
        except ThermohygrometerModel.DoesNotExist:
            return Response(
                self.get_versioned_response(
                    request, {'error': 'Thermohygrometer not found'}),
                status=status.HTTP_404_NOT_FOUND
            )


class EnvironmentalAnalysisViewSet(viewsets.ViewSet):
    authentication_classes = [SessionAuthentication, BasicAuthentication]
    permission_classes = [IsAuthenticated]
    versioning_class = URLPathVersioning

    def get_versioned_response(self, request, data):
        if request.version == 'v1':
            return data
        return data

    @swagger_auto_schema(
        operation_description="Gera dados para gráfico de limites",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['start_date', 'end_date',
                      'start_time', 'end_time', 'instruments'],
            properties={
                'start_date': openapi.Schema(type=openapi.TYPE_STRING, format='date'),
                'end_date': openapi.Schema(type=openapi.TYPE_STRING, format='date'),
                'start_time': openapi.Schema(type=openapi.TYPE_STRING, format='time'),
                'end_time': openapi.Schema(type=openapi.TYPE_STRING, format='time'),
                'instruments': openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(type=openapi.TYPE_INTEGER)
                )
            }
        ),
        responses={
            200: openapi.Response(
                description="Dados para análise",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'data': openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Schema(
                                type=openapi.TYPE_OBJECT,
                                properties={
                                    'instrument_name': openapi.Schema(type=openapi.TYPE_STRING),
                                    'percent_out_of_limits': openapi.Schema(type=openapi.TYPE_NUMBER)
                                }
                            )
                        ),
                        'total_time_available': openapi.Schema(type=openapi.TYPE_NUMBER),
                        'analysis_period': openapi.Schema(type=openapi.TYPE_STRING),
                        'temperature_data': openapi.Schema(type=openapi.TYPE_OBJECT),
                        'humidity_data': openapi.Schema(type=openapi.TYPE_OBJECT),
                        'timestamps': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_STRING))
                    }
                )
            ),
            400: 'Dados inválidos'
        }
    )
    @action(detail=False, methods=['post'], url_path='out-of-limits-chart')
    def out_of_limits_chart(self, request):
        start_date = datetime.strptime(
            request.data['start_date'], '%Y-%m-%d').date()
        end_date = datetime.strptime(
            request.data['end_date'], '%Y-%m-%d').date()
        start_time = datetime.strptime(
            request.data['start_time'], '%H:%M').time()
        end_time = datetime.strptime(request.data['end_time'], '%H:%M').time()
        instrument_ids = request.data['instruments']

        instruments = ThermohygrometerModel.objects.filter(
            id__in=instrument_ids)

        data = []
        total_time_available = 0
        analysis_period = ""
        temperature_data = defaultdict(list)
        humidity_data = defaultdict(list)
        timestamps = set()

        start_datetime = datetime.combine(start_date, start_time)
        end_datetime = datetime.combine(end_date, end_time)

        analysis_period = f"{start_date.strftime('%d/%m/%Y')} {start_time.strftime('%H:%M')} - {end_date.strftime('%d/%m/%Y')} {end_time.strftime('%H:%M')}"

        delta_days = (end_date - start_date).days + 1
        weekdays = [
            start_date + timedelta(days=i) for i in range(delta_days)
            if (start_date + timedelta(days=i)).weekday() < 5
        ]
        total_time_available = len(
            weekdays) * ((end_time.hour - start_time.hour) + (end_time.minute - start_time.minute) / 60)

        for instrument in instruments:
            measures = MeasuresModel.objects.filter(
                instrument=instrument,
                date__range=(start_datetime, end_datetime),
                date__week_day__gte=2,
                date__week_day__lte=6,
                date__time__gte=start_time,
                date__time__lte=end_time
            ).order_by('date')

            temp_out = measures.filter(
                corrected_temperature__isnull=False
            ).filter(
                Q(corrected_temperature__lt=instrument.min_temperature) |
                Q(corrected_temperature__gt=instrument.max_temperature)
            ).count()

            humidity_out = measures.filter(
                corrected_humidity__isnull=False
            ).filter(
                Q(corrected_humidity__lt=instrument.min_humidity) |
                Q(corrected_humidity__gt=instrument.max_humidity)
            ).count()

            total_time_out = ((temp_out + humidity_out) *
                              instrument.time_interval_to_save_measures) / 60
            percent_out_of_limits = (
                total_time_out / total_time_available) * 100 if total_time_available > 0 else 0

            data.append({
                'instrument_name': instrument.instrument_name,
                'percent_out_of_limits': percent_out_of_limits,
            })

            for measure in measures:
                timestamp = measure.date.strftime('%Y-%m-%d %H:%M')
                timestamps.add(timestamp)

                if measure.corrected_temperature is not None:
                    temperature_data[instrument.instrument_name].append({
                        'timestamp': timestamp,
                        'value': measure.corrected_temperature
                    })

                if measure.corrected_humidity is not None:
                    humidity_data[instrument.instrument_name].append({
                        'timestamp': timestamp,
                        'value': measure.corrected_humidity
                    })

        context = {
            'data': data,
            'total_time_available': total_time_available,
            'analysis_period': analysis_period,
            'temperature_data': dict(temperature_data),
            'humidity_data': dict(humidity_data),
            'timestamps': sorted(timestamps),
        }

        return Response(self.get_versioned_response(request, context))

    @swagger_auto_schema(
        operation_description="Executa análise com IA",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['start_date', 'end_date',
                      'start_time', 'end_time', 'instruments'],
            properties={
                'start_date': openapi.Schema(type=openapi.TYPE_STRING, format='date'),
                'end_date': openapi.Schema(type=openapi.TYPE_STRING, format='date'),
                'start_time': openapi.Schema(type=openapi.TYPE_STRING, format='time'),
                'end_time': openapi.Schema(type=openapi.TYPE_STRING, format='time'),
                'instruments': openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(type=openapi.TYPE_INTEGER)
                )
            }
        ),
        responses={
            200: openapi.Response(
                description="Resultado da análise",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'analysis_report': openapi.Schema(type=openapi.TYPE_STRING),
                        'recommendations': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_STRING)),
                        'risk_assessment': openapi.Schema(type=openapi.TYPE_STRING),
                        'compliance_status': openapi.Schema(type=openapi.TYPE_STRING)
                    }
                )
            ),
            400: 'Erro na análise'
        }
    )
    @action(detail=False, methods=['post'], url_path='analyze-with-ai')
    def analyze_with_ai(self, request):
        try:
            start_date = request.data['start_date']
            end_date = request.data['end_date']
            start_time = request.data['start_time']
            end_time = request.data['end_time']
            instrument_ids = request.data['instruments']

            instruments = ThermohygrometerModel.objects.filter(
                id__in=instrument_ids)
            instruments_data = [
                {'id': inst.id, 'instrument_name': inst.instrument_name}
                for inst in instruments
            ]

            analysis_report = analyze_environmental_impact(
                start_date=start_date,
                end_date=end_date,
                instruments=instruments_data,
                start_time=start_time,
                end_time=end_time
            )
            analysis_crew = AnalyticalCrewFlow(analysis_report=analysis_report)
            response = analysis_crew.kickoff()

            results = json.loads(response.pydantic.model_dump_json())
            return Response(self.get_versioned_response(request, results))

        except Exception as e:
            return Response(
                self.get_versioned_response(request, {'error': str(e)}),
                status=status.HTTP_400_BAD_REQUEST
            )


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
            required=['instrument_id', 'start_date',
                      'start_time', 'end_date', 'end_time'],
            properties={
                'instrument_id': openapi.Schema(type=openapi.TYPE_INTEGER),
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
            instrument_id = request.data.get('instrument_id')
            start_date = request.data.get('start_date')
            start_time = request.data.get('start_time')
            end_date = request.data.get('end_date')
            end_time = request.data.get('end_time')

            if not all([instrument_id, start_date, start_time, end_date, end_time]):
                return Response(
                    self.get_versioned_response(
                        request, {'error': 'Missing required parameters'}),
                    status=400
                )

            selected_instrument = ThermohygrometerModel.objects.get(
                id=instrument_id)
            start_datetime = f"{start_date} {start_time}"
            end_datetime = f"{end_date} {end_time}"

            data = MeasuresModel.objects.filter(
                instrument=selected_instrument,
                date__range=[start_datetime, end_datetime]
            ).order_by('-date')

            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = f'attachment; filename="measured_data_{selected_instrument.instrument_name}_{start_date}_{end_date}.csv"'

            writer = csv.writer(response)
            writer.writerow(['Date', 'Temperature (°C)', 'Corrected Temperature (°C)',
                             'Humidity (%)', 'Corrected Humidity (%)'])

            for measure in data:
                writer.writerow([
                    measure.date.strftime("%d/%m/%Y %H:%M"),
                    measure.temperature,
                    measure.corrected_temperature,
                    measure.humidity,
                    measure.corrected_humidity
                ])

            return response
        except ThermohygrometerModel.DoesNotExist:
            return Response(
                self.get_versioned_response(
                    request, {'error': 'Instrument not found'}),
                status=404
            )
        except Exception as e:
            return Response(
                self.get_versioned_response(request, {'error': str(e)}),
                status=400
            )


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
                            'associated_instrument': openapi.Schema(type=openapi.TYPE_STRING)
                        }
                    )
                )
            )
        }
    )
    def list(self, request):
        certificates = CalibrationCertificateModel.objects.all().order_by('-calibration_date')
        data = [
            {
                'id': cert.id,
                'certificate_number': cert.certificate_number,
                'calibration_date': cert.calibration_date,
                'next_calibration_date': cert.next_calibration_date,
                'associated_instrument': cert.thermohygrometermodel_set.first().instrument_name if cert.thermohygrometermodel_set.exists() else None
            }
            for cert in certificates
        ]
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

            # Remover referência do certificado dos termohigrômetros
            thermohygrometers = ThermohygrometerModel.objects.filter(
                calibration_certificate=certificate
            )
            for thermo in thermohygrometers:
                thermo.calibration_certificate = None
                thermo.save()

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
