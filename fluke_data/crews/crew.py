import os
from textwrap import dedent
import requests
import httpx
from tenacity import retry, stop_after_attempt, wait_fixed

from crewai import Agent, Crew, Process, Task
from crewai.flow.flow import Flow, start, listen, and_
from dotenv import load_dotenv
from load_dotenv import load_dotenv
from pydantic import BaseModel, Field

from .tools.data_analysis_tools import analyze_environmental_impact

load_dotenv()


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


class AnalyticalCrewFlow(Flow[AnalytialCrewState]):
    @start()
    def initialize(self):
        self.api_base_url = os.getenv(
            'ANALYSIS_API_URL', 'http://localhost:8000/api/v1/crew-analysis')
        self.api_key = os.getenv('ANALYSIS_API_KEY', 'default_key')
        print(self.state.environment_report_statistics)

    @listen(initialize)
    def analyze_temperature(self):
        try:
            response = requests.post(
                f"{self.api_base_url}/analyze-temperature/",
                json={
                    "data": self.state.environment_report_statistics,
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
                    "data": self.state.environment_report_statistics,
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
                    "environment_stats": self.state.environment_report_statistics,
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


class ACImpactAnalysisCrew:
    def __init__(self, start_date, end_date, instruments, start_time='08:00', end_time='16:00'):
        # Initialize tools
        self.environmental_report = analyze_environmental_impact(
            start_date=start_date,
            end_date=end_date,
            instruments=instruments,
            start_time=start_time,
            end_time=end_time
        )
        self.create_agents()

    def create_agents(self):
        self.thermal_analyst = Agent(
            role='Thermal Stability Analyst',
            goal='Analyze temperature variations and their impact on lab conditions',
            backstory=dedent("""
                You are a specialist in thermal analysis with deep knowledge of HVAC 
                systems and their effects on controlled environments. You excel at 
                identifying patterns in temperature fluctuations."""),
            cache=True,
            verbose=True,
            llm=os.getenv('THERMAL_ANALYST_MODEL', 'gpt-4o-mini'),
            max_rpm=30,
        )

        self.humidity_expert = Agent(
            role='Humidity Control Expert',
            goal='Evaluate humidity regulation performance and its relationship with temperature',
            backstory=dedent("""
                You are a humidity control specialist with expertise in environmental 
                monitoring. You understand the critical relationship between temperature 
                and humidity in laboratory settings."""),
            verbose=True,
            cache=True,
            llm=os.getenv('HUMIDITY_EXPERT_MODEL', 'gpt-4o-mini'),
            max_rpm=30,
        )

        self.productivity_analyst = Agent(
            role='Productivity Impact Analyst',
            goal='Correlate environmental conditions with laboratory productivity',
            backstory=dedent("""
                You are an operational efficiency specialist with experience in 
                analyzing the impact of environmental factors on laboratory performance.
                You have expertise in scientific operations management and environmental control."""),
            verbose=True,
            cache=True,
            llm=os.getenv('PRODUCTIVITY_ANALYST_MODEL', 'gpt-4o-mini'),
            max_rpm=30,
        )

        self.report_generator = Agent(
            role='Impact Report Generator',
            goal='Create comprehensive reports on AC system performance and environmental impact',
            backstory=dedent("""
                You are a technical report specialist with experience in environmental 
                control systems. You excel at synthesizing complex data into clear, 
                actionable insights."""),
            verbose=True,
            cache=True,
            allow_delegation=True,
            llm=os.getenv('REPORT_GENERATOR_MODEL', 'gpt-4o-mini'),
            max_rpm=30,
        )

    def create_tasks(self):
        analyze_temperature_task_description = dedent(f"""
            Perform detailed temperature analysis:
            1. Calculate thermal stability metrics
            2. Identify deviations from optimal range
            3. Analyze temperature gradients
            4. Correlate with AC operation patterns

            The data is stored in the tags <data> and </data>
            <data>
            {self.environmental_report}
            </data>
        """)
        analyze_temperature = Task(
            description=analyze_temperature_task_description,
            expected_output=dedent('''Detailed thermal analysis containing:
            1. Thermal stability index
            2. Total time outside ideal range
            3. Hourly temperature gradients
            4. Correlation with AC cycle'''),
            agent=self.thermal_analyst,
        )

        analyze_humidity_task_description = dedent(f"""
            Perform detailed humidity analysis:
            1. Calculate humidity stability metrics
            2. Identify deviations from optimal range
            3. Analyze humidity gradients
            4. Correlate with AC operation patterns

            The data is stored in the tags <data> and </data>
            <data>
            {self.environmental_report}
            </data>
        """)

        analyze_humidity = Task(
            description=analyze_humidity_task_description,
            agent=self.humidity_expert,
            expected_output=dedent('''Hygrometric performance report containing:
            1. Humidity percentage distribution
            2. Critical events (peaks/valleys) identified
            3. Variation rates by period
            4. Humidity-temperature correlation'''),
        )

        analyze_productivity_impact_task_description = dedent("""
            Analyze the impact of environmental conditions on operations:
            1. Correlate thermal variations with productivity
            2. Link critical humidity events with operational stops
            3. Calculate potential losses from environmental deviations
            4. Identify peak operational efficiency hours
        """)

        analyze_productivity_impact = Task(
            description=analyze_productivity_impact_task_description,
            expected_output=dedent('''Operational impact report containing:
            1. Productivity index by thermal range
            2. Time lost due to critical events
            3. Humidity vs efficiency correlation
            4. Optimized schedule recommendations
            5. Loss/productivity estimates'''),
            agent=self.productivity_analyst,
            context=[analyze_temperature, analyze_humidity],
        )

        generate_report = Task(
            description=dedent("""
            Create comprehensive impact report:
            1. Summarize key findings
            2. Document critical events
            3. Generate performance visualizations
            4. Provide optimization recommendations
            If necessary, ask coworkers for more information.
                           
            The report must be in the OutputReportFormat format.
            The report language must be Portuguese (BR).
            """),
            expected_output=dedent('''Complete technical report containing:
            - Descriptive title
            - Executive summary with key findings
            - Detailed performance analysis
            - Operational optimization suggestions
            - Laboratory impact conclusions
            - Graphical attachments (thermal profile, correlation map)'''),
            agent=self.report_generator,
            output_pydantic=OutputReportFormat,
            context=[analyze_temperature, analyze_humidity,
                     analyze_productivity_impact],
        )

        return [analyze_temperature, analyze_humidity,
                analyze_productivity_impact, generate_report]

    def run_analysis(self):
        """
        Execute the AC impact analysis workflow

        Returns:
            Analysis results and recommendations
        """
        crew = Crew(
            agents=[
                self.thermal_analyst,
                self.humidity_expert,
                self.productivity_analyst,
                self.report_generator
            ],
            tasks=self.create_tasks(),
            verbose=True,
            process=Process.sequential,
            cache=True,
        )

        result = crew.kickoff()
        if hasattr(result, 'pydantic'):
            return result.pydantic.json()
        else:
            return result


# if __name__ == '__main__':

#     flow = AnalyticalCrewFlow(start_date='2024-01-01', end_date='2024-01-31', instruments=[{'id': 1, 'instrument_name': 'Instrument 1'}])
#     flow.plot('/home/rafaelcalassara/Programming/LRC/fluke_dewk_1620A_project/fluke_data/crews/plot')
