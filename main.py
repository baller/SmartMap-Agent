from rich.panel import Panel
from augmented import hello


def main():
    print(hello())
    print("Hello from exp-llm-mcp-rag!")


if __name__ == "__main__":
    main()


print(
    Panel("", title="Hello"),
)
