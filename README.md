# Pampa

[![PyPI - Version](https://img.shields.io/pypi/v/pampa.svg)](https://pypi.org/project/pampa)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/pampa.svg)](https://pypi.org/project/pampa)

Pampa is an experimental, interactive AI coding assistant for learning and experimentation. It uses the OpenAI Responses API and can inspect a project and run shell commands on the user's behalf. Every shell command is shown for approval before it is executed.

> **Status:** Pampa is in beta and is not intended for production use. Review generated commands and changes before allowing them to run.

See the [project roadmap](ROADMAP.md) for planned work.

## Requirements

- Python 3.12 or newer
- An OpenAI API key with access to the model configured in [`pampa/core.py`](pampa/core.py)
- [uv](https://docs.astral.sh/uv/) (recommended for development)

## Installation

Clone the repository and install its locked dependencies:

```console
git clone <repository-url>
cd pampa
uv sync --locked
```

Alternatively, install the package and its runtime dependency with pip:

```console
python -m pip install .
```

Set the API key in the environment. Do not commit it to the repository:

```console
export OPENAI_API_KEY="your-api-key"
```

## Usage

Pampa exposes its interactive assistant through the `pampa` command:

```console
uv run pampa
```

When running directly from a checkout, the module form remains available:

```console
uv run python -m pampa.core
```

The assistant reads a message from standard input. Because input is read as a multi-line block, finish a message with **Ctrl-D** on Linux/macOS (or the terminal's equivalent EOF shortcut on Windows). For example:

```console
$ uv run python -m pampa.core
Welcome to Pampa Coding assistant

>>>:
Inspect the files in this project and summarize the architecture.
# Press Ctrl-D here
Thinking...
```

The built-in command `/clear` removes the conversation context. Press Ctrl-C to exit. When Pampa requests a shell command, enter `Y` to approve it; any other response declines execution.

## Built-in tool

The assistant currently has one tool, `bash_run`, which executes a Bash command and returns its exit code, standard output, and standard error. The tool supports these arguments:

- `command` — command to execute (required)
- `timeout` — maximum execution time in seconds (default: `10`)
- `cwd` — optional working directory
- `max_output_bytes` — optional output limit
- `capture_stderr` — whether to return standard error (default: `true`)

The tool uses a restricted environment and rejects several obviously dangerous command patterns, including `sudo`, `su `, `shutdown`, `reboot`, and `dd if=`. This is only a basic safeguard; it is not a security boundary. Run Pampa in a disposable or otherwise appropriately isolated environment when working with untrusted prompts or generated commands.

## Development

Install the development dependencies with:

```console
uv sync --locked
```

Useful project commands:

```console
make test   # run pytest
make lint   # run Ruff
make help   # list Make targets
```

The package requires Python `>=3.12`, has `openai` as its runtime dependency, and uses `pytest` and `ruff` for development. The lockfile is `uv.lock`; update it whenever dependencies are changed:

```console
uv add <package>
uv add --dev <package>
uv lock
```

## Project layout

```text
pampa/
├── core.py          # interactive assistant loop and OpenAI integration
└── tools/bash.py    # Bash tool schema and command runner
tests/               # test suite
docs/                # Sphinx documentation
```

## License

Pampa is distributed under the terms of the [MIT](LICENSE.txt) license.
