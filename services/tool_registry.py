from sql_tool.sql_tool import (
    SQLTool,
    TableSchemaTool,
    SQLValidationTool,
    OpenAITool,
    NaturalLanguageResponseTool,
    MemoryQueryTool,
    TableSummaryTool,
    FallbackTool,
    RateLimiterTool,
    ExplainSQLTool,
    FeedbackLoggingTool,
    QueryCacheTool
)

from mcp_tools.vartopia_tools import VartopiaTool
from services.feedback_tool import FeedbackTool 
    
class ToolRegistry:
    def __init__(self):
        self.tools = {
            "SQLTool": SQLTool(),
            "TableSchemaTool": TableSchemaTool(),
            "SQLValidationTool": SQLValidationTool(),
            "OpenAITool": OpenAITool(),
            "NaturalLanguageResponseTool": NaturalLanguageResponseTool(),
            "MemoryQueryTool": MemoryQueryTool(),
            "TableSummaryTool": TableSummaryTool(),
            "FallbackTool": FallbackTool(),
            "RateLimiterTool": RateLimiterTool(),
            "ExplainSQLTool": ExplainSQLTool(),
            # "FeedbackLoggingTool": FeedbackLoggingTool(),
            "QueryCacheTool": QueryCacheTool(),
            
            "VartopiaTool": VartopiaTool(),
            "FeedbackTool":FeedbackTool(),
        }

    def get(self, tool_name: str):
        """Fetch a tool instance by its name."""
        return self.tools.get(tool_name)

    def list_names(self):
        """List available tool names (for tools/list)."""
        return list(self.tools.keys())

    def list_tools(self):
        """List tool instances (for iteration)."""
        return list(self.tools.values())

    def __iter__(self):
        return iter(self.tools.values())


def get_available_tools():
    """Convenience method to get all tool instances."""
    return ToolRegistry().list_tools()