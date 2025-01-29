from typing import Type

import pandas as pd
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from django.db.models import F
from fluke_data.models import MeasuresModel


class AnalyzeEnvironmentalImpactInput(BaseModel):
    start_date: str = Field(...,
                            description="Start date of the analysis period")
    end_date: str = Field(..., description="End date of the analysis period")
    instruments: list = Field(..., description="List of instrument IDs")
    start_time: str = Field(...,
                            description="Start time of the analysis period")
    end_time: str = Field(...,
                          description="End time of the analysis period")


class AnalyzeEnvironmentalImpactTool(BaseTool):
    """
    Analisa o impacto de condições ambientais na produção laboratorial.

    Args:
        start_date (date): Data inicial do período de análise.
        end_date (date): Data final do período de análise.
        instruments (list): Lista de objetos de instrumentos com atributos 'id' e 'instrument_name'.
        start_time (str): Horário diário de início (HH:MM).
        end_time (str): Horário diário de término (HH:MM).

    Returns:
        dict: Dicionário com as seguintes métricas de análise:
            - total_available_hours (float): Total de horas disponíveis no período.
            - total_downtime (dict): Dicionário com o tempo total de inatividade por instrumento.
            - event_count (dict): Dicionário com a contagem de eventos por instrumento.
            - percentage_out_of_limits (dict): Dicionário com a porcentagem de tempo fora dos limites por instrumento.
            - both_downtime (dict): Dicionário com o tempo de inatividade quando ambos os parâmetros estão fora dos limites.
            - temp_only_downtime (dict): Dicionário com o tempo de inatividade apenas para temperatura.
            - humid_only_downtime (dict): Dicionário com o tempo de inatividade apenas para umidade.
            - both_events (dict): Dicionário com a contagem de eventos quando ambos os parâmetros estão fora dos limites.
            - temp_only_events (dict): Dicionário com a contagem de eventos apenas para temperatura.
            - humid_only_events (dict): Dicionário com a contagem de eventos apenas para umidade.
    """
    name: str = "Analyze Environmental Impact"
    description: str = "Analyses the impact of environmental conditions on laboratory production."
    args_schema: Type[BaseModel] = AnalyzeEnvironmentalImpactInput


def analyze_environmental_impact(start_date, end_date, instruments, start_time='08:00', end_time='16:00'):
    """
    Analisa o impacto de condições ambientais na produção laboratorial.

    Args:
        start_date (date): Data inicial do período de análise.
        end_date (date): Data final do período de análise.
        instruments (list): Lista de objetos de instrumentos com atributos 'id' e 'instrument_name'.
        start_time (str): Horário diário de início (HH:MM).
        end_time (str): Horário diário de término (HH:MM).

    Returns:
        dict: Dicionário com as seguintes métricas de análise:
            - total_available_hours (float): Total de horas disponíveis no período.
            - total_downtime (dict): Dicionário com o tempo total de inatividade por instrumento.
            - event_count (dict): Dicionário com a contagem de eventos por instrumento.
            - percentage_out_of_limits (dict): Dicionário com a porcentagem de tempo fora dos limites por instrumento.
            - both_downtime (dict): Dicionário com o tempo de inatividade quando ambos os parâmetros estão fora dos limites.
            - temp_only_downtime (dict): Dicionário com o tempo de inatividade apenas para temperatura.
            - humid_only_downtime (dict): Dicionário com o tempo de inatividade apenas para umidade.
            - both_events (dict): Dicionário com a contagem de eventos quando ambos os parâmetros estão fora dos limites.
            - temp_only_events (dict): Dicionário com a contagem de eventos apenas para temperatura.
            - humid_only_events (dict): Dicionário com a contagem de eventos apenas para umidade.
    """
    # Get instrument IDs
    instrument_ids = [str(inst['id']) for inst in instruments]

    # Garantir que todos os IDs sejam strings
    instrument_ids_str = [str(r) for r in instrument_ids]

    # 1. Buscar dados relevantes
    measures = MeasuresModel.objects.filter(
        instrument__id__in=instrument_ids_str,
        date__range=(start_date, end_date),
        date__week_day__gte=2,  # Segunda (Django usa 2)
        date__week_day__lte=6,  # Sexta
        date__time__gte=start_time,
        date__time__lte=end_time
    ).exclude(corrected_temperature__isnull=True).exclude(corrected_humidity__isnull=True).annotate(
        instrument_str=F('instrument__id'),
        min_temp=F('instrument__min_temperature'),
        max_temp=F('instrument__max_temperature'),
        min_hum=F('instrument__min_humidity'),
        max_hum=F('instrument__max_humidity'),
        time_interval=F('instrument__time_interval_to_save_measures')
    ).values('date', 'corrected_temperature', 'corrected_humidity',
             'instrument_str', 'min_temp', 'max_temp', 'min_hum', 'max_hum', 'time_interval')

    # Converter para DataFrame e garantir que date seja datetime
    df = pd.DataFrame.from_records(measures)
    if df.empty:
        empty_result = {
            str(instrument): 0 for instrument in instrument_ids_str}
        return {
            'total_downtime': empty_result,
            'event_count': empty_result,
            'total_available_hours': 0,
            'percentage_out_of_limits': empty_result,
            'temp_only_downtime': empty_result,
            'humid_only_downtime': empty_result,
            'both_downtime': empty_result,
            'temp_only_events': empty_result,
            'humid_only_events': empty_result,
            'both_events': empty_result
        }

    df['date'] = pd.to_datetime(df['date'])
    df['instrument_str'] = df['instrument_str'].astype(
        str)  # Converter instrument para string

    # 2. Filtrar por horário comercial
    if isinstance(start_time, str):
        start_time = pd.to_datetime(start_time).time()
    if isinstance(end_time, str):
        end_time = pd.to_datetime(end_time).time()

    df = df[(df['date'].dt.time >= start_time)
            & (df['date'].dt.time <= end_time)]

    if df.empty:
        empty_result = {
            str(instrument): 0 for instrument in instrument_ids_str}
        return {
            'total_downtime': empty_result,
            'event_count': empty_result,
            'total_available_hours': 0,
            'percentage_out_of_limits': empty_result,
            'temp_only_downtime': empty_result,
            'humid_only_downtime': empty_result,
            'both_downtime': empty_result,
            'temp_only_events': empty_result,
            'humid_only_events': empty_result,
            'both_events': empty_result
        }

    # 3. Análise sequencial das condições fora dos limites
    results = {}
    for instrument in instrument_ids_str:
        instrument_data = df[df['instrument_str'] == instrument].copy()
        if not instrument_data.empty:
            # Converter para horas
            time_interval = instrument_data['time_interval'].iloc[0] / 60

            # 3.1 Primeiro identificar registros com ambos parâmetros fora
            temp_out = (
                (instrument_data['corrected_temperature'] < instrument_data['min_temp']) |
                (instrument_data['corrected_temperature']
                 > instrument_data['max_temp'])
            )
            humid_out = (
                (instrument_data['corrected_humidity'] < instrument_data['min_hum']) |
                (instrument_data['corrected_humidity']
                 > instrument_data['max_hum'])
            )

            # Registros com ambos fora
            both_out = temp_out & humid_out
            both_count = both_out.sum()
            both_events = (both_out != both_out.shift()).sum() // 2

            # 3.2 Remover registros com ambos fora e analisar restantes
            remaining_data = instrument_data[~both_out].copy()

            if not remaining_data.empty:
                # Temperatura fora (excluindo registros já contados em both)
                temp_only_out = (
                    (remaining_data['corrected_temperature'] < remaining_data['min_temp']) |
                    (remaining_data['corrected_temperature']
                     > remaining_data['max_temp'])
                )
                temp_only_count = temp_only_out.sum()
                temp_only_events = (
                    temp_only_out != temp_only_out.shift()).sum() // 2

                # Umidade fora (excluindo registros já contados em both)
                humid_only_out = (
                    (remaining_data['corrected_humidity'] < remaining_data['min_hum']) |
                    (remaining_data['corrected_humidity']
                     > remaining_data['max_hum'])
                )
                humid_only_count = humid_only_out.sum()
                humid_only_events = (
                    humid_only_out != humid_only_out.shift()).sum() // 2
            else:
                temp_only_count = humid_only_count = 0
                temp_only_events = humid_only_events = 0

            results[instrument] = {
                'both_downtime': both_count * time_interval,
                'temp_only_downtime': temp_only_count * time_interval,
                'humid_only_downtime': humid_only_count * time_interval,
                'total_downtime': (both_count + temp_only_count + humid_only_count) * time_interval,
                'both_events': both_events,
                'temp_only_events': temp_only_events,
                'humid_only_events': humid_only_events,
                'event_count': both_events + temp_only_events + humid_only_events
            }
        else:
            results[instrument] = {
                'both_downtime': 0,
                'temp_only_downtime': 0,
                'humid_only_downtime': 0,
                'total_downtime': 0,
                'both_events': 0,
                'temp_only_events': 0,
                'humid_only_events': 0,
                'event_count': 0
            }

    # 4. Calcular horas totais disponíveis
    total_work_days = len(pd.date_range(
        start_date, end_date, freq='B'))  # Dias úteis

    # Calcular diferença de horas
    start_hour = start_time.hour + start_time.minute / 60
    end_hour = end_time.hour + end_time.minute / 60
    daily_hours = end_hour - start_hour

    total_available_hours = total_work_days * daily_hours

    # 5. Organizar resultados
    analysis = {
        'total_available_hours': round(total_available_hours, 2),
        'total_downtime': {instrument: round(results[instrument]['total_downtime'], 2) for instrument in instrument_ids_str},
        'event_count': {instrument: results[instrument]['event_count'] for instrument in instrument_ids_str},
        'percentage_out_of_limits': {
            instrument: round((results[instrument]['total_downtime'] /
                               total_available_hours * 100), 2)
            if total_available_hours > 0 else 0
            for instrument in instrument_ids_str
        },
        'both_downtime': {instrument: round(results[instrument]['both_downtime'], 2) for instrument in instrument_ids_str},
        'temp_only_downtime': {instrument: round(results[instrument]['temp_only_downtime'], 2) for instrument in instrument_ids_str},
        'humid_only_downtime': {instrument: round(results[instrument]['humid_only_downtime'], 2) for instrument in instrument_ids_str},
        'both_events': {instrument: results[instrument]['both_events'] for instrument in instrument_ids_str},
        'temp_only_events': {instrument: results[instrument]['temp_only_events'] for instrument in instrument_ids_str},
        'humid_only_events': {instrument: results[instrument]['humid_only_events'] for instrument in instrument_ids_str}
    }

    # Replace IDs with instrument names in results
    id_to_name = {
        str(inst['id']): inst['instrument_name'] for inst in instruments}

    # Safely convert IDs to names with fallback to original ID
    def safe_convert_dict(data_dict):
        return {
            id_to_name.get(str(k), f"Instrument {k}"): v
            for k, v in data_dict.items()
        }

    analysis['total_downtime'] = safe_convert_dict(
        analysis['total_downtime'])
    analysis['percentage_out_of_limits'] = safe_convert_dict(
        analysis['percentage_out_of_limits'])
    analysis['both_downtime'] = safe_convert_dict(
        analysis['both_downtime'])
    analysis['temp_only_downtime'] = safe_convert_dict(
        analysis['temp_only_downtime'])
    analysis['humid_only_downtime'] = safe_convert_dict(
        analysis['humid_only_downtime'])
    analysis['both_events'] = safe_convert_dict(
        analysis['both_events'])
    analysis['temp_only_events'] = safe_convert_dict(
        analysis['temp_only_events'])
    analysis['humid_only_events'] = safe_convert_dict(
        analysis['humid_only_events'])
    analysis['event_count'] = safe_convert_dict(
        analysis['event_count'])

    return analysis
