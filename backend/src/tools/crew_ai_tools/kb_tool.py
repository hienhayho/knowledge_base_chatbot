import sys
import uuid

from pathlib import Path
from typing import Type
from dotenv import load_dotenv
from pydantic import BaseModel, Field, ConfigDict
from crewai.tools import BaseTool

sys.path.append(str(Path(__file__).parent.parent.parent))
from src.database import ContextualRAG


load_dotenv()


class KBSearchToolInput(BaseModel):
    """Input schema for KBSearchTool."""

    query: str = Field(
        title="Query",
        description="Câu hỏi của người dùng.",
    )


class KBSearchTool(BaseTool):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    name: str = "KB Search tool"
    description: str = """
Trả lời những câu hỏi liên quan tới: sử dụng các sản phẩm thông minh, dịch vụ liên quan đến nhà thông minh như các dịch vụ an ninh, giải pháp cho các vấn đề liên quan đến nhà thông minh.
Nếu câu hỏi nào bạn không có thông tin hoặc không biết câu trả lời thì hãy trả lời là:"Với câu hỏi này hiện em chưa trả lời được. Anh/chị có thể cung cấp số điện thoại để em có thể hỗ trợ trả lời sau được không ạ?"

        The output should be formatted as a JSON instance that conforms to the JSON schema below.

As an example, for the schema {"properties": {"foo": {"title": "Foo", "description": "a list of strings", "type": "array", "items": {"type": "string"}}}, "required": ["foo"]}
the object {"foo": ["bar", "baz"]} is a well-formatted instance of the schema. The object {"properties": {"foo": ["bar", "baz"]}} is not well-formatted.

Here is the output schema:
```
{"description": "Input schema for KBSearchTool.", "properties": {"query": {"description": "Câu hỏi của người dùng.", "title": "Query", "type": "string"}}, "required": ["query"]}
```
    """
    args_schema: Type[BaseModel] = KBSearchToolInput
    contextual_rag: ContextualRAG
    kb_ids: list[str | uuid.UUID]
    session_id: str | uuid.UUID
    is_contextual_rag: bool
    system_prompt: str

    def _run(self, query: str) -> str:
        return self.contextual_rag.search(
            session_id=str(self.session_id),
            is_contextual_rag=self.is_contextual_rag,
            kb_ids=[str(kb_id) for kb_id in self.kb_ids],
            query=query,
            top_k=self.setting.contextual_rag_config.top_k,
            system_prompt=self.system_prompt,
        )


"""Example usage:

llm = ChatOpenAI(model="gpt-4o-mini")

agent = Agent(
    role="Assistant",
    goal="Helping users find information in the knowledge base.",
    backstory="You are a very intelligent assistant. You have access to a knowledge base that contains a lot of information.",
    llm=llm,
)

search_task = Task(
    description="Search the knowledge base for information about {query}.",
    expected_output="A most relevant answer from the knowledge base for the given query.",
    agent=agent,
    tools=[
        KBSearchTool(
            setting=get_default_setting(),
            contextual_rag=ContextualRAG.from_setting(get_default_setting()),
            kb_ids=[
                "3e6a1373-cb33-4115-a9db-ed7e0018fc9e",
                "8ad56aec-f187-4bf1-bae5-f59e9f6f969d",
            ],
            session_id="3e6a1373-cb33-4115-a9db-ed7e0018fc9e",
            is_contextual_rag=True,
            system_prompt="You are a very intelligent assistant. You have access to a knowledge base that contains a lot of information.",
            result_as_answer=True,
        )
    ],
)

crew = Crew(agents=[agent], tasks=[search_task], manager_llm=llm, verbose=True)

query = "ChainBuddy là gì ?"

inputs = {
    "query": query,
}

response = crew.kickoff(inputs=inputs)

print(response)

"""