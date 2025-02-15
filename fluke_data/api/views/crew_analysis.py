import json
import os

from django.conf import settings
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from fluke_data.crews.crews_definition.humidity_crew import \
    perform_humidity_analysis
from fluke_data.crews.crews_definition.productivity_crew import \
    perform_productivity_analysis
from fluke_data.crews.crews_definition.report_crew import \
    generate_impact_report
from fluke_data.crews.crews_definition.temperature_crew import \
    perform_temperature_analysis


@method_decorator(csrf_exempt, name='dispatch')
class CrewAnalysisViewSet(viewsets.ViewSet):
    """
    ViewSet para análise de dados ambientais usando crews especializadas.

    IMPORTANTE: Antes de usar estes endpoints, é necessário coletar dados usando a API de análise ambiental
    (EnvironmentalAnalysisViewSet). O fluxo correto de uso é:

    1. Coletar dados ambientais:
       POST /environmental-analysis/out-of-limits-chart/
       {
           "start_date": "YYYY-MM-DD",
           "end_date": "YYYY-MM-DD",
           "start_time": "HH:MM",
           "end_time": "HH:MM",
           "instruments": [1, 2, 3]
       }

    2. Realizar análise com IA:
       POST /environmental-analysis/analyze-with-ai/
       {
           "start_date": "YYYY-MM-DD",
           "end_date": "YYYY-MM-DD",
           "start_time": "HH:MM",
           "end_time": "HH:MM",
           "instruments": [1, 2, 3]
       }

    3. Usar os dados obtidos para alimentar os endpoints desta API na seguinte ordem:
       a. analyze-temperature/
       b. analyze-humidity/
       c. analyze-productivity/
       d. generate-report/

    Observações:
    - Todos os endpoints requerem uma chave de API (exceto em modo DEBUG)
    - Os dados devem ser coletados apenas em dias úteis (segunda a sexta)
    - O sistema considera o impacto na produtividade quando parâmetros estão fora dos limites
    - Todos os relatórios são gerados em português (BR)
    """

    authentication_classes = []  # Disable built-in authentication
    permission_classes = []      # Disable permission checks

    @swagger_auto_schema(
        operation_description="""
        Analisa dados de temperatura do ambiente.
        
        IMPORTANTE: Antes de usar este endpoint, você deve:
        1. Coletar dados usando POST /environmental-analysis/out-of-limits-chart/
        2. Realizar análise com IA usando POST /environmental-analysis/analyze-with-ai/
        
        Os dados retornados por esses endpoints devem ser usados para compor o payload desta requisição.
        """,
        method='post',
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'data': openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    description='Dados para análise de temperatura',
                    properties={
                        'temperature_related_key': openapi.Schema(type=openapi.TYPE_NUMBER, description='Dados relacionados à temperatura (chaves contendo "temp")'),
                        'total_something': openapi.Schema(type=openapi.TYPE_NUMBER, description='Dados totais (chaves contendo "total")')
                    }
                ),
                'api_key': openapi.Schema(type=openapi.TYPE_STRING, description='Chave de API para autenticação (não necessária em modo DEBUG)')
            },
            required=['data']
        ),
        responses={
            200: openapi.Response('Successful response', openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'analysis_result': openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        description='Resultado da análise de temperatura',
                        properties={
                            'thermal_stability_index': openapi.Schema(type=openapi.TYPE_STRING, description='Índice de estabilidade térmica'),
                            'time_outside_range': openapi.Schema(type=openapi.TYPE_STRING, description='Tempo total fora do intervalo ideal'),
                            'temperature_gradients': openapi.Schema(type=openapi.TYPE_STRING, description='Gradientes de temperatura por hora'),
                            'ac_cycle_correlation': openapi.Schema(type=openapi.TYPE_STRING, description='Correlação com ciclo do ar condicionado')
                        }
                    )
                }
            )),
            401: 'Chave de API inválida',
            500: 'Erro interno do servidor'
        }
    )
    @action(detail=False, methods=['post'], url_path='analyze-temperature')
    def analyze_temperature(self, request):
        try:
            data = request.data.get('data', {})
            api_key = request.data.get('api_key')

            # Bypass API key check in debug mode
            if not settings.DEBUG and api_key != settings.ANALYSIS_API_KEY:
                return Response(
                    {"error": "Invalid API key"},
                    status=status.HTTP_401_UNAUTHORIZED
                )
            data = json.loads(data)
            analysis_result = perform_temperature_analysis(data)
            return Response({
                "analysis_result": analysis_result
            })
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @swagger_auto_schema(
        operation_description="""
        Analisa dados de umidade do ambiente.
        
        IMPORTANTE: Antes de usar este endpoint, você deve:
        1. Coletar dados usando POST /environmental-analysis/out-of-limits-chart/
        2. Realizar análise com IA usando POST /environmental-analysis/analyze-with-ai/
        
        Os dados retornados por esses endpoints devem ser usados para compor o payload desta requisição.
        """,
        method='post',
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'data': openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    description='Dados para análise de umidade',
                    properties={
                        'humidity_related_key': openapi.Schema(type=openapi.TYPE_NUMBER, description='Dados relacionados à umidade (chaves contendo "humid")'),
                        'total_something': openapi.Schema(type=openapi.TYPE_NUMBER, description='Dados totais (chaves contendo "total")')
                    }
                ),
                'api_key': openapi.Schema(type=openapi.TYPE_STRING, description='Chave de API para autenticação (não necessária em modo DEBUG)')
            },
            required=['data']
        ),
        responses={
            200: openapi.Response('Successful response', openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'humidity_analysis': openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        description='Resultado da análise de umidade',
                        properties={
                            'hygrometric_stability_index': openapi.Schema(type=openapi.TYPE_STRING, description='Índice de estabilidade higrométrica'),
                            'time_outside_range': openapi.Schema(type=openapi.TYPE_STRING, description='Tempo total fora do intervalo ideal'),
                            'humidity_gradients': openapi.Schema(type=openapi.TYPE_STRING, description='Gradientes de umidade por hora'),
                            'ac_cycle_correlation': openapi.Schema(type=openapi.TYPE_STRING, description='Correlação com ciclo do ar condicionado')
                        }
                    )
                }
            )),
            401: 'Chave de API inválida',
            500: 'Erro interno do servidor'
        }
    )
    @action(detail=False, methods=['post'], url_path='analyze-humidity')
    def analyze_humidity(self, request):
        try:
            data = request.data.get('data', {})
            api_key = request.data.get('api_key')

            # Bypass API key check in debug mode
            if not settings.DEBUG and api_key != settings.ANALYSIS_API_KEY:
                return Response(
                    {"error": "Invalid API key"},
                    status=status.HTTP_401_UNAUTHORIZED
                )
            data = json.loads(data)
            humidity_analysis = perform_humidity_analysis(data)
            return Response({
                "humidity_analysis": humidity_analysis
            })
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @swagger_auto_schema(
        operation_description="""
        Analisa o impacto das condições ambientais na produtividade.
        
        IMPORTANTE: Antes de usar este endpoint, você deve:
        1. Coletar dados usando POST /environmental-analysis/out-of-limits-chart/
        2. Realizar análise com IA usando POST /environmental-analysis/analyze-with-ai/
        3. Obter análise de temperatura usando POST /analyze-temperature/
        4. Obter análise de umidade usando POST /analyze-humidity/
        
        Os dados retornados por todos esses endpoints devem ser usados para compor o payload desta requisição.
        """,
        method='post',
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'temperature_report': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description='Resultado da análise de temperatura (string com o relatório completo)'
                ),
                'humidity_report': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description='Resultado da análise de umidade (string com o relatório completo)'
                ),
                'environment_stats': openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    description='Estatísticas ambientais gerais',
                    properties={
                        'temperature_data': openapi.Schema(type=openapi.TYPE_OBJECT, description='Dados de temperatura'),
                        'humidity_data': openapi.Schema(type=openapi.TYPE_OBJECT, description='Dados de umidade'),
                        'time_series': openapi.Schema(type=openapi.TYPE_OBJECT, description='Séries temporais')
                    }
                ),
                'api_key': openapi.Schema(type=openapi.TYPE_STRING, description='Chave de API para autenticação (não necessária em modo DEBUG)')
            },
            required=['temperature_report',
                      'humidity_report', 'environment_stats']
        ),
        responses={
            200: openapi.Response('Successful response', openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'productivity_analysis': openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        description='Resultado da análise de produtividade',
                        properties={
                            'productivity_index': openapi.Schema(type=openapi.TYPE_OBJECT, description='Índice de produtividade por faixa térmica'),
                            'time_lost': openapi.Schema(type=openapi.TYPE_STRING, description='Tempo perdido devido a eventos críticos'),
                            'humidity_efficiency': openapi.Schema(type=openapi.TYPE_STRING, description='Correlação umidade vs eficiência'),
                            'schedule_recommendations': openapi.Schema(type=openapi.TYPE_STRING, description='Recomendações de horários otimizados'),
                            'productivity_estimates': openapi.Schema(type=openapi.TYPE_STRING, description='Estimativas de perda/produtividade')
                        }
                    )
                }
            )),
            401: 'Chave de API inválida',
            500: 'Erro interno do servidor'
        }
    )
    @action(detail=False, methods=['post'], url_path='analyze-productivity')
    def analyze_productivity(self, request):
        try:
            data = request.data
            temperature_report = data.get('temperature_report')
            humidity_report = data.get('humidity_report')
            environment_stats = data.get('environment_stats')
            api_key = data.get('api_key')

            # Bypass API key check in debug mode
            if not settings.DEBUG and api_key != settings.ANALYSIS_API_KEY:
                return Response(
                    {"error": "Invalid API key"},
                    status=status.HTTP_401_UNAUTHORIZED
                )

            productivity_analysis = perform_productivity_analysis(
                temperature_report,
                humidity_report,
                environment_stats
            )
            return Response({
                "productivity_analysis": productivity_analysis
            })
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @swagger_auto_schema(
        operation_description="""
        Gera um relatório completo de impacto ambiental.
        
        IMPORTANTE: Este é o último endpoint do fluxo e deve ser chamado após:
        1. Coletar dados usando POST /environmental-analysis/out-of-limits-chart/
        2. Realizar análise com IA usando POST /environmental-analysis/analyze-with-ai/
        3. Obter análise de temperatura usando POST /analyze-temperature/
        4. Obter análise de umidade usando POST /analyze-humidity/
        5. Obter análise de produtividade usando POST /analyze-productivity/
        
        O relatório final será gerado em português (BR) e incluirá todas as análises anteriores.
        """,
        method='post',
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'temperature_report': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description='Relatório de temperatura (string com o relatório completo)'
                ),
                'humidity_report': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description='Relatório de umidade (string com o relatório completo)'
                ),
                'productivity_report': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description='Relatório de produtividade (string com o relatório completo)'
                ),
                'api_key': openapi.Schema(type=openapi.TYPE_STRING, description='Chave de API para autenticação (não necessária em modo DEBUG)')
            },
            required=['temperature_report',
                      'humidity_report', 'productivity_report']
        ),
        responses={
            200: openapi.Response('Successful response', openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'impact_report': openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        description='Relatório de impacto em português (BR)',
                        properties={
                            'title': openapi.Schema(type=openapi.TYPE_STRING, description='Título descritivo do relatório'),
                            'summary': openapi.Schema(type=openapi.TYPE_STRING, description='Resumo executivo com principais descobertas'),
                            'analytics': openapi.Schema(type=openapi.TYPE_OBJECT, description='Análise detalhada de desempenho'),
                            'suggestion': openapi.Schema(type=openapi.TYPE_STRING, description='Sugestões de otimização operacional'),
                            'conclusion': openapi.Schema(type=openapi.TYPE_STRING, description='Conclusões sobre impacto no laboratório')
                        }
                    )
                }
            )),
            401: 'Chave de API inválida',
            500: 'Erro interno do servidor'
        }
    )
    @action(detail=False, methods=['post'], url_path='generate-report')
    def generate_report(self, request):
        try:
            data = request.data
            temperature_report = data.get('temperature_report')
            humidity_report = data.get('humidity_report')
            productivity_report = data.get('productivity_report')
            api_key = data.get('api_key')

            # Bypass API key check in debug mode
            if not settings.DEBUG and api_key != settings.ANALYSIS_API_KEY:
                return Response(
                    {"error": "Invalid API key"},
                    status=status.HTTP_401_UNAUTHORIZED
                )

            impact_report = generate_impact_report(
                temperature_report,
                humidity_report,
                productivity_report
            )
            impact_report_dict = impact_report.pydantic.model_dump()
            return Response({
                "impact_report": {
                    "title": impact_report_dict['title'],
                    "summary": impact_report_dict['summary'],
                    "analytics": impact_report_dict['analytics'],
                    "suggestion": impact_report_dict['suggestion'],
                    "conclusion": impact_report_dict['conclusion']
                }
            })
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
