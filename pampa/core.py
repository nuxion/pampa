import json
import tomllib
from pathlib import Path
import os
import platform
from dataclasses import dataclass
from typing import Any, Callable

from openai import OpenAI
from pampa.tools import bash
from prompt_toolkit import PromptSession
from pampa.chat import SlashCommandCompleter, COMMANDS, DESCRIPTIONS
from prompt_toolkit.shortcuts import choice


MODEL = "gpt-5.6-luna"  # GPT-5.6 Luna
# MODEL = "gpt-5-nano"
REASONING = "medium"


@dataclass
class ToolSpec:
    """Description and execution policy for a model-callable tool."""

    schema: dict[str, Any]
    handler: Callable[..., Any]
    requires_confirmation: Callable[[dict[str, Any]], bool] | None = None


def load_models() -> list[dict[str, Any]]:
    """Load the model choices from the bundled TOML catalogue."""
    models_file = Path(__file__).with_name("models.toml")
    with models_file.open("rb") as file:
        catalogue = tomllib.load(file)

    models = catalogue.get("models", [])
    if not isinstance(models, list):
        raise ValueError("models.toml must contain a [[models]] list")
    
    return [m for m in models if m.get("visible")]


def model_options() -> list[tuple[str, str]]:
    """Build the options displayed by prompt-toolkit's model chooser."""
    return [
        (
            model["code_name"],
            f'{model["friendly_name"]} — {model["description"]}',
        )
        for model in load_models()
    ]



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

Available Tools:
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



def chat_assistant():
    print("Welcome to Pampa Coding assistant\n")
    context = []
    session = PromptSession(completer=SlashCommandCompleter(COMMANDS))
    while True:
        try:
            # msg = input(">>> ")
            line = session.prompt("You> ")
            if line in ("/exit", "/quit"):
                break
            if line == "/clear":
                context = []
                print("Context cleared")
            elif line == "/help":
                for command in COMMANDS:
                    print(f"{command:<10} {DESCRIPTIONS[command]}")
            elif line == "/model":
                options = model_options()
                if not options:
                    print("No models are configured.")
                    continue
                result = choice(
                    message="Please choose a Model:",
                    options=options,
                    default=options[0][0],
                )
                print(f"You have chosen: {result}")
            else:

                context.append({"role": "user", "content": line})
                print("Thinking...")

                response = create_response(context)
                context.extend(response.output)

                while process_response(response, context):
                    response = create_response(context)
                    context.extend(response.output)

            print("\n")
        except (EOFError, KeyboardInterrupt):
            print("\nThanks! See you")
            break
if __name__ == "__main__":
    chat_assistant()
