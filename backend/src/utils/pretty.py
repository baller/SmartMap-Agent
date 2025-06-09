from rich.console import Console
from rich.theme import Theme
from rich.text import Text
from rich.panel import Panel

# 自定义主题
custom_theme = Theme({
    "info": "cyan",
    "warning": "yellow",
    "error": "bold red",
    "success": "bold green",
    "tool": "bold blue",
    "thinking": "magenta",
    "agent": "bold cyan",
})

RICH_CONSOLE = Console(theme=custom_theme)


class ALogger:
    def __init__(self, prefix: str):
        self.prefix = prefix

    def title(self, text: str, rule_style: str = "bright_cyan"):
        RICH_CONSOLE.rule(f"{self.prefix} {text}", style=rule_style)

    def info(self, text: str):
        RICH_CONSOLE.print(f"{self.prefix} {text}", style="info")

    def warning(self, text: str):
        RICH_CONSOLE.print(f"{self.prefix} {text}", style="warning")

    def error(self, text: str):
        RICH_CONSOLE.print(f"{self.prefix} {text}", style="error")

    def success(self, text: str):
        RICH_CONSOLE.print(f"{self.prefix} {text}", style="success")

    def tool(self, text: str):
        RICH_CONSOLE.print(f"{self.prefix} {text}", style="tool")

    def thinking(self, text: str):
        RICH_CONSOLE.print(Panel(text, title="🤔 思考中", style="thinking"))

    def tool_call(self, tool_name: str, args: str):
        RICH_CONSOLE.print(Panel(
            f"工具: {tool_name}\n参数: {args}",
            title="🔧 调用工具",
            style="tool"
        ))

    def agent_response(self, text: str):
        RICH_CONSOLE.print(Panel(text, title="🤖 Agent 回复", style="agent")) 