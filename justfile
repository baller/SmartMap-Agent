# NOTE: now using python-dotenv to inject .env files, not need these configs
# set dotenv-required
# set dotenv-load
# set dotenv-filename := '.env.local'

default: help

help:
    @echo "`just -l`"

format-and-lintfix:
	ruff format
	ruff check --fix

# step 0: init with utils
run_example_0_pretty:
	uv run src/augmented/utils/pretty.py


# step 1: impl ChatOpenai
run_example_1_chat_openai:
	uv run src/augmented/chat_openai.py


# step 2: impl MCPClient
run_example_2_mcp_client:
	uv run src/augmented/mcp_client.py


# step 3: impl Agent
run_example_3_agent:
	uv run src/augmented/agent.py

# step 4: impl RAG
run_example_4_rag:
	uv run rag_example.py