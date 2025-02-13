"""
Views for thermohygrometer management.
This module provides endpoints for managing thermohygrometer devices,
including device discovery, connection management, and basic CRUD operations.
"""

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status, viewsets
from rest_framework.authentication import (BasicAuthentication,
                                           SessionAuthentication)
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.versioning import URLPathVersioning

from fluke_data.models import ThermohygrometerModel
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
