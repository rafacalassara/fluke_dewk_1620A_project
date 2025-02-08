import os
from textwrap import dedent
from crewai import Agent, Crew, Process, Task


def perform_productivity_analysis(temperature_report: str, humidity_report: str, environment_report_statistics: dict) -> str:
    productivity_analyst = Agent(
        role='Productivity Impact Analyst',
        goal='Correlate environmental conditions with laboratory productivity',
        backstory=dedent("""\
            You are an operational efficiency specialist with experience in 
            analyzing the impact of environmental factors on laboratory performance.
            You have expertise in scientific operations management and environmental control.
        """),
        verbose=True,
        cache=True,
        llm=os.getenv('PRODUCTIVITY_ANALYST_MODEL', 'gpt-4o-mini'),
        max_rpm=30,
    )

    productivity_analysis_task = Task(
        description=dedent("""\
            Analyze the impact of environmental conditions on operations:
            1. Correlate thermal variations with productivity
            2. Link critical humidity events with operational stops
            3. Calculate potential losses from environmental deviations
            4. Identify peak operational efficiency hours
            
            Remember that every time one of the parameters is out of the limits, 
            the productivity is affected because the technician has to stop working and wait
            for the air conditioning to return to the ideal range.
        """),
        expected_output=dedent(f"""\
            Operational impact report containing:
            1. Productivity index by thermal range
            2. Time lost due to critical events
            3. Humidity vs efficiency correlation
            4. Optimized schedule recommendations
            5. Loss/productivity estimates
            
            temperature_report: {temperature_report}
            humidity_report: {humidity_report}
            environment_report_statistics: {environment_report_statistics}
        """),
        agent=productivity_analyst,
    )

    crew = Crew(
        agents=[productivity_analyst],
        tasks=[productivity_analysis_task],
        verbose=True,
        process=Process.sequential,
        cache=True,
    )

    result = crew.kickoff().raw
    return result
