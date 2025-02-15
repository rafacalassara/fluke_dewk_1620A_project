import os
import json
from textwrap import dedent
import requests
import httpx
from tenacity import retry, stop_after_attempt, wait_fixed
import numpy as np

from crewai import Agent, Crew, Process, Task
from crewai.flow.flow import Flow, start, listen, and_
from dotenv import load_dotenv
from load_dotenv import load_dotenv
from pydantic import BaseModel, Field

from .tools.data_analysis_tools import analyze_environmental_impact

load_dotenv()


def convert_numpy_types(obj):
    if isinstance(obj, dict):
        return {key: convert_numpy_types(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy_types(item) for item in obj]
    elif isinstance(obj, (np.int64, np.int32)):
        return int(obj)
    elif isinstance(obj, (np.float64, np.float32)):
        return float(obj)
    return obj


class OutputReportFormat(BaseModel):
    title: str
    summary: str
    analytics: str
    suggestion: str
    conclusion: str


class AnalytialCrewState(BaseModel):
    environment_report_statistics: dict = Field(default_factory=dict)
    temperature_report: str = Field(default='')
    humidity_report: str = Field(default='')
    productivity_report: str = Field(default='')

    def update_environment_stats(self, stats):
        self.environment_report_statistics = convert_numpy_types(stats)


class AnalyticalCrewFlow(Flow[AnalytialCrewState]):
    @start()
    def initialize(self):
        self.api_base_url = os.getenv(
            'ANALYSIS_API_URL', 'http://localhost:8000/api/v1/crew-analysis')
        self.api_key = os.getenv('ANALYSIS_API_KEY', 'default_key')
        self.state.update_environment_stats(
            self.state.environment_report_statistics)
        print(self.state.environment_report_statistics)

    @listen(initialize)
    def analyze_temperature(self):
        try:
            response = requests.post(
                f"{self.api_base_url}/analyze-temperature/",
                json={
                    "data": json.dumps(self.state.environment_report_statistics),
                    "api_key": self.api_key
                },
                timeout=30
            )
            response.raise_for_status()
            self.state.temperature_report = response.json()['analysis_result']

        except requests.exceptions.RequestException as e:
            self.state.temperature_report = f"Erro na API: {str(e)}"

    @listen(initialize)
    def analyze_humidity(self):
        try:
            response = requests.post(
                f"{self.api_base_url}/analyze-humidity/",
                json={
                    "data": json.dumps(self.state.environment_report_statistics),
                    "api_key": self.api_key
                },
                timeout=30
            )
            response.raise_for_status()
            self.state.humidity_report = response.json()['humidity_analysis']

        except requests.exceptions.RequestException as e:
            self.state.humidity_report = f"Erro na API: {str(e)}"

    @listen(and_(analyze_temperature, analyze_humidity))
    def analyze_productivity(self):
        try:
            response = requests.post(
                f"{self.api_base_url}/analyze-productivity/",
                json={
                    "temperature_report": self.state.temperature_report,
                    "humidity_report": self.state.humidity_report,
                    "environment_stats": json.dumps(self.state.environment_report_statistics),
                    "api_key": self.api_key
                },
                timeout=30
            )
            response.raise_for_status()
            self.state.productivity_report = response.json()[
                'productivity_analysis']

        except requests.exceptions.RequestException as e:
            self.state.productivity_report = f"Erro na API: {str(e)}"

    @listen(analyze_productivity)
    def generate_report(self):
        try:
            response = requests.post(
                f"{self.api_base_url}/generate-report/",
                json={
                    "temperature_report": self.state.temperature_report,
                    "humidity_report": self.state.humidity_report,
                    "productivity_report": self.state.productivity_report,
                    "api_key": self.api_key
                },
                timeout=30
            )
            response.raise_for_status()
            retorno = response.json()['impact_report']
            return retorno

        except requests.exceptions.RequestException as e:
            return f"Erro na API: {str(e)}"

    @retry(stop=stop_after_attempt(3), wait=wait_fixed(1))
    def call_analysis_api(self, endpoint, payload):
        response = requests.post(
            f"{self.api_base_url}/{endpoint}",
            json=payload,
            headers={"Authorization": f"Bearer {self.api_key}"}
        )
        response.raise_for_status()
        return response.json()

# if __name__ == '__main__':

#     flow = AnalyticalCrewFlow(start_date='2024-01-01', end_date='2024-01-31', instruments=[{'id': 1, 'instrument_name': 'Instrument 1'}])
#     flow.plot('/home/rafaelcalassara/Programming/LRC/fluke_dewk_1620A_project/fluke_data/crews/plot')
