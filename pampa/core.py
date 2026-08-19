import json
import os
import platform
from dataclasses import dataclass
from typing import Any, Callable

from openai import OpenAI
from pampa.tools import bash

MODEL = "gpt-5.6-luna"  # GPT-5.6 Luna
# MODEL = "gpt-5-nano"
REASONING = "medium"


@dataclass
class ToolSpec:
    """Description and execution policy for a model-callable tool."""

    schema: dict[str, Any]
    handler: Callable[..., Any]
    requires_confirmation: Callable[[dict[str, Any]], bool] | None = None


def should_i_execute(command: str) -> bool:
    response = input(f"Do you want to execute {command}? (Y/n): ")
    # The prompt uses (Y/n), so an empty response means yes.
    return response.strip().lower() in ("", "y", "yes")


def confirm_bash(args: dict[str, Any]) -> bool:
    return should_i_execute(args["command"])


# Register tools here. Adding a tool does not require changes to the dispatcher.
TOOLS: dict[str, ToolSpec] = {
    bash.schema["name"]: ToolSpec(
        schema=bash.schema,
        handler=bash.run_bash_command,
        requires_confirmation=confirm_bash,
    ),
}

available_tools = list(TOOLS)

system_prompt = f"""
you are an expert coding assistant called Pampa. You help users by reading files,
executing commands, editing code, and writing new files.

{", ".join(available_tools)}

----
About you:
You are built on Python 3.12
And you run over: {platform.system()}
"""

llm = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))


def create_response(context):
    return llm.responses.create(
        model=MODEL,
        reasoning={"effort": REASONING},
        instructions=system_prompt,
        input=context,
        tools=[tool.schema for tool in TOOLS.values()],
    )


def handle_tool_call(item, context) -> bool:
    """Dispatch any registered function call and append its result."""
    tool = TOOLS.get(item.name)

    if tool is None:
        output = f"Unknown tool: {item.name}"
    else:
        try:
            args = json.loads(item.arguments)

            if (
                tool.requires_confirmation is not None
                and not tool.requires_confirmation(args)
            ):
                output = "Tool execution denied by user."
            else:
                result = tool.handler(**args)
                output = json.dumps(result, default=str)
        except json.JSONDecodeError as exc:
            output = f"Invalid arguments for {item.name}: {exc}"
        except Exception as exc:
            output = f"Tool {item.name} failed: {exc}"

    context.append({
        "type": "function_call_output",
        "call_id": item.call_id,
        "output": output,
    })
    return True


def process_response(response, context):
    """Process a response and return whether another response is needed."""
    tool_called = False

    for item in response.output:
        if item.type == "function_call":
            tool_called = handle_tool_call(item, context) or tool_called

    if response.output_text:
        print(response.output_text)

    return tool_called


try:
    print("Welcome to Pampa Coding assistant\n")
    context = []
    while True:
        msg = input(">>> ")

        if msg.startswith("/"):
            if msg == "/clear":
                context = []
                print("Context cleared")
            else:
                print(f"cmd: {msg} unknown")
            continue

        context.append({"role": "user", "content": msg})
        print("Thinking...")

        response = create_response(context)
        breakpoint()
        context.extend(response.output)

        while process_response(response, context):
            response = create_response(context)
            context.extend(response.output)

        print("\n")
except KeyboardInterrupt:
    print("\nThanks! See you")
