"""
Views for environmental analysis functionality.
This module provides endpoints for analyzing environmental data from thermohygrometers,
including out-of-limits analysis and AI-powered environmental impact analysis.
"""

import json
from collections import defaultdict
from datetime import datetime, timedelta

from django.db.models import Q
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

from fluke_data.models import MeasuresModel, ThermohygrometerModel


class EnvironmentalAnalysisViewSet(viewsets.ViewSet):
    """
    ViewSet para análise de dados ambientais.

    Esta API é o ponto de entrada para o fluxo completo de análise ambiental.
    Os dados coletados aqui são necessários para alimentar as análises especializadas
    realizadas pela API CrewAnalysis.

    Fluxo completo de análise:
    1. Use /out-of-limits-chart/ para coletar dados básicos do ambiente
    2. Use /analyze-with-ai/ para obter análise inicial com IA
    3. Use os resultados para alimentar as análises especializadas em /api/crew-analysis/

    Autenticação:
    - Requer autenticação básica ou por sessão
    - Necessário estar autenticado para acessar os endpoints
    """

    authentication_classes = [SessionAuthentication, BasicAuthentication]
    permission_classes = [IsAuthenticated]
    versioning_class = URLPathVersioning

    def get_versioned_response(self, request, data):
        if request.version == 'v1':
            return data
        return data

    @swagger_auto_schema(
        operation_description="""
        Gera dados para análise de limites ambientais.
        
        Este é o primeiro endpoint que deve ser chamado no fluxo de análise.
        Os dados retornados são necessários para:
        1. Análise com IA (próximo endpoint)
        
        IMPORTANTE:
        - Coleta dados apenas de dias úteis (segunda a sexta)
        - Considera os limites configurados para cada instrumento
        - Retorna dados de temperatura e umidade separadamente
        """,
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['start_date', 'end_date',
                      'start_time', 'end_time', 'instruments'],
            properties={
                'start_date': openapi.Schema(type=openapi.TYPE_STRING, format='date'),
                'end_date': openapi.Schema(type=openapi.TYPE_STRING, format='date'),
                'start_time': openapi.Schema(type=openapi.TYPE_STRING, format='time', default='08:00'),
                'end_time': openapi.Schema(type=openapi.TYPE_STRING, format='time', default='18:00'),
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
            id__in=instrument_ids  # type: ignore
        )

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
                instrument=instrument,  # type: ignore
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
