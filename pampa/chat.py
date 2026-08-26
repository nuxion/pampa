from prompt_toolkit.completion import Completer, Completion

COMMANDS = ["/clear", "/model", "/help", "/quit", "/history"]
DESCRIPTIONS = {
    "/clear": "clear the screen",
    "/model": "switch model",
    "/quit": "exit",
}



class SlashCommandCompleter(Completer):
    def __init__(self, commands):
        self.commands = commands

    def get_completions(self, document, complete_event):
        text = document.text_before_cursor

        if not text.startswith("/") or " " in text:
            return

        for cmd in self.commands:
            if cmd.startswith(text):
                yield Completion(
                    cmd,
                    start_position=-len(text),
                    display=cmd,
                    display_meta=DESCRIPTIONS.get(cmd, ""),
                )


