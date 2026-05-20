#!/usr/bin/env python3
"""
MCP server wrapping local ollama instance.
Gives Claude Code a run_local tool to offload routine tasks to
qwq:32b / deepseek-r1:32b / qwen2.5-coder:32b without burning Anthropic tokens.
"""
import json
import urllib.request
import urllib.error
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

OLLAMA_BASE = "http://localhost:11434"

# Cost tiers — pick the right model for the job
ROUTING_GUIDE = """
Model routing guide:
- qwq:32b            — deep reasoning, analysis, planning (slow, thorough)
- deepseek-r1:32b    — reasoning + code, good for complex logic
- qwen2.5-coder:32b  — code generation, refactoring, boilerplate
- qwen2.5:14b        — fast general tasks, email drafting, summaries
- qwen2.5:7b         — quick responses, simple transforms
- gemma2:2b          — ultra-fast tiny tasks (very limited)
- nomic-embed-text   — embeddings only (not a chat model)
"""

app = Server("local-llm")


def _ollama_chat(model: str, system: str, prompt: str, stream: bool = False) -> str:
    payload = {
        "model": model,
        "stream": False,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ],
    }
    data = json.dumps(payload).encode()
    req = urllib.request.Request(
        f"{OLLAMA_BASE}/api/chat",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=300) as resp:
            result = json.loads(resp.read())
            return result["message"]["content"]
    except urllib.error.URLError as e:
        return f"ERROR: ollama not reachable — {e}. Start it with: ollama serve"
    except Exception as e:
        return f"ERROR: {e}"


def _ollama_list() -> list[dict]:
    req = urllib.request.Request(f"{OLLAMA_BASE}/api/tags", method="GET")
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
            return data.get("models", [])
    except Exception:
        return []


@app.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="run_local",
            description=(
                "Delegate a task to a local ollama model running on the MERIT server "
                "(R9700, 32GB VRAM). Use this instead of burning Anthropic tokens for: "
                "worker agent email drafts, data analysis, code boilerplate, summaries, "
                "cause tag extraction, vendor recommendations, compliance email text. "
                "Prefer qwq:32b for reasoning, qwen2.5-coder:32b for code, qwen2.5:14b "
                "for fast drafts. Returns the model's response as plain text."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "prompt": {
                        "type": "string",
                        "description": "The full task/question to send to the local model.",
                    },
                    "model": {
                        "type": "string",
                        "description": (
                            "Which local model to use. Available: qwq:32b, deepseek-r1:32b, "
                            "qwen2.5-coder:32b, qwen2.5:32b, qwen2.5:14b, qwen2.5:7b, "
                            "deepseek-r1:14b, gemma2:9b, gemma4:latest, gemma2:2b, "
                            "llama3.1:8b, glm4:9b"
                        ),
                        "default": "qwen2.5:14b",
                    },
                    "system": {
                        "type": "string",
                        "description": "Optional system prompt to set role/context.",
                        "default": "You are a helpful assistant working on the MERIT nonprofit discovery platform.",
                    },
                },
                "required": ["prompt"],
            },
        ),
        Tool(
            name="list_local_models",
            description="List all models currently available in the local ollama instance with their sizes.",
            inputSchema={"type": "object", "properties": {}, "required": []},
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    if name == "run_local":
        prompt = arguments["prompt"]
        model = arguments.get("model", "qwen2.5:14b")
        system = arguments.get(
            "system",
            "You are a helpful assistant working on the MERIT nonprofit discovery platform.",
        )
        result = _ollama_chat(model=model, system=system, prompt=prompt)
        return [TextContent(type="text", text=result)]

    if name == "list_local_models":
        models = _ollama_list()
        if not models:
            return [TextContent(type="text", text="ollama not running or no models loaded.")]
        lines = [ROUTING_GUIDE, "\nCurrently loaded:"]
        for m in models:
            size_gb = m.get("size", 0) / 1024**3
            lines.append(f"  {m['name']:<35} {size_gb:.1f} GB")
        return [TextContent(type="text", text="\n".join(lines))]

    return [TextContent(type="text", text=f"Unknown tool: {name}")]


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
