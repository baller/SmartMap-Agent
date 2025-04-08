from rich.panel import Panel

from rich.console import RenderableType
from rich import print as rprint


def log_title(renderable: RenderableType = "", title: str = "-"):
    rprint(
        Panel(
            renderable,
            title=title,
        )
    )
