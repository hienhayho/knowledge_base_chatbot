from .kb_search_tool import load_knowledge_base_search_tool
from .display_tool import load_display_tool
from llama_index.core.tools import FunctionTool
from typing import List

class ToolManager:
    def __init__(self, config):
        self.tools = [
            load_knowledge_base_search_tool(config),
            load_display_tool(config["conversation_id"])
        ]

    def add_tool(self, tool):
        self.tools.append(tool)

    def get_tool(self, name) -> FunctionTool:
        for tool in self.tools:
            if tool.metadata.name == name:
                return tool

    def get_tools(self) -> List[FunctionTool]:
        return self.tools

    def remove_tool(self, name):
        for tool in self.tools:
            if tool.name == name:
                self.tools.remove(tool)
                return

    def run_tool(self, name, args):
        tool = self.get_tool(name)
        if tool:
            tool.run(args)
        else:
            print(f"Tool {name} not found")