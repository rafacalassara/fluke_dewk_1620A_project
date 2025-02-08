import os
from textwrap import dedent
from crewai import Agent, Crew, Process, Task
from fluke_data.crews.crew import OutputReportFormat


def generate_impact_report(temperature_report: str, humidity_report: str, productivity_report: str):
    report_generator = Agent(
        role='Impact Report Generator',
        goal='Create comprehensive reports on AC system performance and environmental impact',
        backstory=dedent("""\
            You are a technical report specialist with experience in environmental 
            control systems. You excel at synthesizing complex data into clear, 
            actionable insights.
        """),
        verbose=True,
        cache=True,
        allow_delegation=True,
        llm=os.getenv('REPORT_GENERATOR_MODEL', 'gpt-4o-mini'),
        max_rpm=30,
    )

    report_generation_task = Task(
        description=dedent(f"""\
            Create comprehensive impact report:
            1. Summarize key findings
            2. Document critical events
            3. Generate performance visualizations
            4. Provide optimization recommendations
            If necessary, ask coworkers for more information.
                        
            The report must be in the OutputReportFormat format.
            The report language must be Portuguese (BR).

            temperature_report: {temperature_report}
            humidity_report: {humidity_report}
            productivity_report: {productivity_report}
        """),
        expected_output=dedent("""\
            Complete technical report containing:
            - Descriptive title
            - Executive summary with key findings
            - Detailed performance analysis
            - Operational optimization suggestions
            - Laboratory impact conclusions
        """),
        agent=report_generator,
        output_pydantic=OutputReportFormat,
    )

    crew = Crew(
        agents=[report_generator],
        tasks=[report_generation_task],
        verbose=True,
        process=Process.sequential,
        cache=True,
    )

    result = crew.kickoff()
    return result
