import asyncio
import shlex
from augmented.agent import Agent, McpCmdOptions
from rich import print as rprint

from augmented.embedding_retriever import EembeddingRetriever
from augmented.mcp_client import MCPClient
from augmented.utils import pretty
from augmented.utils.info import PROJECT_ROOT_DIR
from augmented.vector_store import VectorStoreItem


ENABLED_MCP_CLIENTS = []
for mcp_name, cmd in [
    (
        "filesystem",
        f"npx {McpCmdOptions.npx_use_cn_mirror} -y @modelcontextprotocol/server-filesystem {PROJECT_ROOT_DIR!s}",
    ),
    (
        "fetch",
        f"uvx {McpCmdOptions.uvx_use_cn_mirror} mcp-server-fetch {McpCmdOptions.fetch_server_mcp_use_proxy}".strip(),
    ),
]:
    rprint(cmd)
    command, *args = shlex.split(cmd)
    mcp_client = MCPClient(
        name=mcp_name,
        command=command,
        args=args,
    )
    ENABLED_MCP_CLIENTS.append(mcp_client)


KNOWLEDGE_BASE_DIR = PROJECT_ROOT_DIR / "output" / "step4-rag" / "kownledge"
KNOWLEDGE_BASE_DIR.mkdir(parents=True, exist_ok=True)


async def prepare_knowleage_data():
    pretty.log_title("[RAG] prepare_knowleage_data")
    if list(KNOWLEDGE_BASE_DIR.glob("*.md")):
        rprint("[green]knowledge base already exists, skip prepare_knowleage_data[/green]")
        return
    agent = Agent(
        model="gpt-4o-mini",
        mcp_clients=ENABLED_MCP_CLIENTS,
    )
    await agent.init()
    resp = await agent.invoke(
        f"爬取 https://jsonplaceholder.typicode.com/users 的内容, 在 {KNOWLEDGE_BASE_DIR!s} 每个人创建一个md文件, 保存基本信息"
    )
    rprint(resp)


async def retrieve_context(prompt: str):
    er = EembeddingRetriever("BAAI/bge-m3")
    for path in KNOWLEDGE_BASE_DIR.glob("*.md"):
        document = path.read_text()
        await er.embed_documents(document)

    context: list[VectorStoreItem] = await er.retrieve(prompt)
    pretty.log_title("CONTEXT")
    rprint(context)
    return "\n".join([c.document for c in context])


async def rag():
    prompt = f"根据Bret的信息, 创作一个他的故事, 并且把他的故事保存到 {KNOWLEDGE_BASE_DIR.parent / 'story.md'!s} , 要包含他的基本信息和故事"

    context = await retrieve_context(prompt)

    agent = Agent(
        model="gpt-4o-mini",
        mcp_clients=ENABLED_MCP_CLIENTS,
        context=context,
    )
    await agent.init()
    resp = await agent.invoke(prompt)
    rprint(resp)


async def main():
    await prepare_knowleage_data()
    await rag()


if __name__ == "__main__":
    asyncio.run(main())
