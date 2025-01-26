import os
from textwrap import dedent

from crewai import Agent, Crew, Process, Task
from dotenv import load_dotenv
from load_dotenv import load_dotenv
from pydantic import BaseModel

from .tools.data_analysis_tools import analyze_environmental_impact

# from .tools.data_analysis_tools import (NumpyAnalysisTool, PandasAnalysisTool,
#                                         StatisticalAnalysisTool,
#                                         VisualizationTool)

load_dotenv()


class OutputReportFormat(BaseModel):
    title: str
    summary: str
    analytics: str
    suggestion: str
    conclusion: str


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
            # tools=[self.pandas_tool, self.numpy_tool,
            #        self.stats_tool, self.viz_tool],
            cache=True,
            verbose=True,
            model=os.getenv('THERMAL_ANALYST_MODEL', 'gpt-4o-mini')
        )

        self.humidity_expert = Agent(
            role='Humidity Control Expert',
            goal='Evaluate humidity regulation performance and its relationship with temperature',
            backstory=dedent("""
                You are a humidity control specialist with expertise in environmental 
                monitoring. You understand the critical relationship between temperature 
                and humidity in laboratory settings."""),
            # tools=[self.pandas_tool, self.stats_tool, self.viz_tool],
            verbose=True,
            cache=True,
            model=os.getenv('HUMIDITY_EXPERT_MODEL', 'gpt-4o-mini')
        )

        self.productivity_analyst = Agent(
            role='Productivity Impact Analyst',
            goal='Correlate environmental conditions with laboratory productivity',
            backstory=dedent("""
                You are an operational efficiency specialist with experience in 
                analyzing the impact of environmental factors on laboratory performance.
                You have expertise in scientific operations management and environmental control."""),
            # tools=[self.pandas_tool, self.stats_tool],
            verbose=True,
            cache=True,
            model=os.getenv('PRODUCTIVITY_ANALYST_MODEL', 'gpt-4o-mini')
        )

        self.report_generator = Agent(
            role='Impact Report Generator',
            goal='Create comprehensive reports on AC system performance and environmental impact',
            backstory=dedent("""
                You are a technical report specialist with experience in environmental 
                control systems. You excel at synthesizing complex data into clear, 
                actionable insights."""),
            # tools=[self.pandas_tool, self.viz_tool],
            verbose=True,
            cache=True,
            allow_delegation=True,
            model=os.getenv('REPORT_GENERATOR_MODEL', 'gpt-4o-mini')
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
            # async_execution=True,
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
            # async_execution=True,
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

        Args:
            data (pd.DataFrame): DataFrame containing temperature and humidity data

        Returns:
            dict: Analysis results and recommendations
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
        return result.pydantic.json()

# Example usage:
# crew = ACImpactAnalysisCrew()
# results = crew.run_analysis(your_data_frame)
