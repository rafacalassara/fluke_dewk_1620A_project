import os
from textwrap import dedent
from crewai import Agent, Crew, Process, Task


def perform_temperature_analysis(environment_report_statistics: dict) -> str:
    # Filter temperature-related data
    report = {}
    for k, v in environment_report_statistics.items():
        if 'temp' in k or 'total' in k:
            report[k] = v

    temperature_specialist = Agent(
        role='Thermal Stability Analyst',
        goal='Analyze temperature variations and their impact on lab conditions',
        backstory=dedent("""\
            You are a specialist in thermal analysis with deep knowledge of HVAC 
            systems and their effects on controlled environments. You excel at 
            identifying patterns in temperature fluctuations.
        """),
        cache=True,
        verbose=True,
        llm=os.getenv('THERMAL_ANALYST_MODEL', 'gpt-4o-mini'),
        max_rpm=30,
    )

    temperature_analysis_task = Task(
        description=dedent(f"""\
            Perform detailed temperature analysis:
            1. Calculate thermal stability metrics
            2. Identify deviations from optimal range
            3. Analyze temperature gradients
            4. Correlate with AC operation patterns

            The data is stored in the tags <data> and </data>
            <data>
            {report}
            </data>
        """),
        expected_output=dedent("""\
            Detailed thermal analysis containing:
            1. Thermal stability index
            2. Total time outside ideal range
            3. Hourly temperature gradients
            4. Correlation with AC cycle
        """),
        agent=temperature_specialist,
    )

    crew = Crew(
        agents=[temperature_specialist],
        tasks=[temperature_analysis_task],
        verbose=True,
        process=Process.sequential,
        cache=True,
    )

    result = crew.kickoff().raw
    return result
