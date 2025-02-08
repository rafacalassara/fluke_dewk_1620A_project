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
    authentication_classes = []  # Disable built-in authentication
    permission_classes = []      # Disable permission checks

    @swagger_auto_schema(
        method='post',
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'data': openapi.Schema(type=openapi.TYPE_OBJECT, description='Data for temperature analysis'),
                'api_key': openapi.Schema(type=openapi.TYPE_STRING, description='API key for authentication')
            }
        ),
        responses={
            200: openapi.Response('Successful response', openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'analysis_result': openapi.Schema(type=openapi.TYPE_OBJECT, description='Temperature analysis result')
                }
            )),
            401: 'Invalid API key',
            500: 'Server error'
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
        method='post',
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'data': openapi.Schema(type=openapi.TYPE_OBJECT, description='Data for humidity analysis'),
                'api_key': openapi.Schema(type=openapi.TYPE_STRING, description='API key for authentication')
            }
        ),
        responses={
            200: openapi.Response('Successful response', openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'humidity_analysis': openapi.Schema(type=openapi.TYPE_OBJECT, description='Humidity analysis result')
                }
            )),
            401: 'Invalid API key',
            500: 'Server error'
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
        method='post',
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'temperature_report': openapi.Schema(type=openapi.TYPE_OBJECT, description='Temperature report data'),
                'humidity_report': openapi.Schema(type=openapi.TYPE_OBJECT, description='Humidity report data'),
                'environment_stats': openapi.Schema(type=openapi.TYPE_OBJECT, description='Environmental statistics'),
                'api_key': openapi.Schema(type=openapi.TYPE_STRING, description='API key for authentication')
            }
        ),
        responses={
            200: openapi.Response('Successful response', openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'productivity_analysis': openapi.Schema(type=openapi.TYPE_OBJECT, description='Productivity analysis result')
                }
            )),
            401: 'Invalid API key',
            500: 'Server error'
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
        method='post',
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'temperature_report': openapi.Schema(type=openapi.TYPE_OBJECT, description='Temperature report data'),
                'humidity_report': openapi.Schema(type=openapi.TYPE_OBJECT, description='Humidity report data'),
                'productivity_report': openapi.Schema(type=openapi.TYPE_OBJECT, description='Productivity report data'),
                'api_key': openapi.Schema(type=openapi.TYPE_STRING, description='API key for authentication')
            }
        ),
        responses={
            200: openapi.Response('Successful response', openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'impact_report': openapi.Schema(type=openapi.TYPE_OBJECT, description='Impact report', properties={
                        'title': openapi.Schema(type=openapi.TYPE_STRING, description='Report title'),
                        'summary': openapi.Schema(type=openapi.TYPE_STRING, description='Report summary'),
                        'analytics': openapi.Schema(type=openapi.TYPE_OBJECT, description='Analytics details'),
                        'suggestion': openapi.Schema(type=openapi.TYPE_STRING, description='Suggestions'),
                        'conclusion': openapi.Schema(type=openapi.TYPE_STRING, description='Conclusion'),
                    })
                }
            )),
            401: 'Invalid API key',
            500: 'Server error'
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
