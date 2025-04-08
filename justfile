set dotenv-required
set dotenv-load
# set dotenv-filename := '.env.local'

default: help

help:
    @echo "`just -l`"

run_main:
	uv run main.py


run_example_pretty:
	uv run src/augmented/utils/pretty.py


run_example_chat_openai:
	uv run src/augmented/chat_openai.py


run_example_mcp_client:
	uv run src/augmented/mcp_client.py
