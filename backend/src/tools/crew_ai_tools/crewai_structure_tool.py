from typing import Any, Type
from pydantic import BaseModel
from langchain.output_parsers import PydanticOutputParser
from crewai.tools.base_tool import Tool
from langchain.tools.base import Tool as LangchainTool


class CrewAIStructuredTool:
    def from_function(
        self,
        func,
        name,
        description,
        args_schema: Type[BaseModel] = None,
        return_direct: bool = False,
    ):
        """Create a structured tool from a function."""

        parser = PydanticOutputParser(pydantic_object=args_schema)

        description_with_schema = f"""{description}
        Input should be a string representation of a dictionary containing the following keys:
        {parser.get_format_instructions()}
        """

        print(description_with_schema)

        def parse_input_and_delegate(input: str) -> Any:
            """Parse the input and delegate to the function."""
            try:
                parsed = parser.invoke(input)
            except Exception as e:
                return f"Could not parse input: {str(e)}"
            return func(parsed)

        tool = LangchainTool.from_function(
            parse_input_and_delegate,
            name,
            description_with_schema,
            args_schema=None,
            return_direct=return_direct,
        )
        return Tool.from_langchain(tool)


"""Example usage:

class GetPostInput(BaseModel):
    "Input for reading a post"

    blog_id: int = Field(description="blog_id to look up")
    post_id: int = Field(description="post_id to look up")


def get_post(input=GetPostInput) -> Any:
    "Gets content and metadata about blog posts."
    blog_id = input.blog_id
    post_id = input.post_id

    token = os.environ["MY_ACCESS_TOKEN"]
    client = MyApiClient(access_token=token)
    try:
        return client.get_post(blog_id, post_id)
    except Exception as e:
        return f"Error fetching post: {str(e)}"


# now create the tool
get_post_tool = CrewAIStructuredTool().from_function(
    get_post,
    "get_post",
    "Tool that gets content and metadata about blog posts",
    args_schema=GetPostInput,
)
"""
