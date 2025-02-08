import os
from textwrap import dedent
from crewai import Agent, Crew, Process, Task


def perform_humidity_analysis(environment_report_statistics: dict) -> str:
    # Filter humidity-related data
    report = {}
    for k, v in environment_report_statistics.items():
        if 'humid' in k or 'total' in k:
            report[k] = v

    humidity_specialist = Agent(
        role='Humidity Control Expert',
        goal='Evaluate humidity regulation performance and its relationship with temperature',
        backstory=dedent("""\
            You are a specialist in humidity control with deep knowledge of HVAC 
            systems and their effects on controlled environments. You excel at 
            identifying patterns in humidity fluctuations.
        """),
        cache=True,
        verbose=True,
        llm=os.getenv('HUMIDITY_EXPERT_MODEL', 'gpt-4o-mini'),
        max_rpm=30,
    )

    humidity_analysis_task = Task(
        description=dedent(f"""\
            Perform detailed humidity analysis:
            1. Calculate humidity stability metrics
            2. Identify deviations from optimal range
            3. Analyze humidity gradients
            4. Correlate with AC operation patterns

            The data is stored in the tags <data> and </data>
            <data>
            {report}
            </data>
        """),
        expected_output=dedent("""\
            Detailed humidity analysis containing:
            1. Hygrometric stability index
            2. Total time outside ideal range
            3. Hourly humidity gradients
            4. Correlation with AC cycle
        """),
        agent=humidity_specialist,
    )

    crew = Crew(
        agents=[humidity_specialist],
        tasks=[humidity_analysis_task],
        verbose=True,
        process=Process.sequential,
        cache=True,
    )

    result = crew.kickoff().raw
    return result
