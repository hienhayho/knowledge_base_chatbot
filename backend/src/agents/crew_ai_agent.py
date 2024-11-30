from typing import Any
from crewai import Agent, Crew, Task


class CrewAIAgent:
    def __init__(
        self, agents: list[Agent], tasks: list[Task], manager_llm: str, verbose: bool
    ):
        self.agents = agents
        self.tasks = tasks
        self.manager_llm = manager_llm
        self.verbose = verbose

        self.crew = self.get_crew()

    def get_crew(self):
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            manager_llm=self.manager_llm,
            verbose=self.verbose,
        )

    def chat(self, inputs: Any, *args, **kwargs) -> Any:
        return self.crew.kickoff(inputs=inputs).raw
