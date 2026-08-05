import os
import json
import platform
from openai import OpenAI
from pampa.tools import bash 

#MODEL = "gpt-5.6-luna" # GPT-5.6 Luna 
MODEL = "gpt-5-nano"
REASONING = "medium"
           # GPT 5 nano a

available_tools = ["bash"]

system_prompt = f"""
you are an expert coding assistant called Pampa. You help users by reading files, 
executing commands, editing code, and writing new files.

{ ",".join(available_tools) }

----
About you: 
You are built on Python 3.12
And you run over: {platform.system()}
"""

llm = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY")
)

def should_i_execute(cmd: str) -> bool:
    rsp = input(f"Do you want to execute {cmd} ? (Y/n): ")
    if rsp == "Y":
        return True
    return False

try: 
    print("Welcome to Pampa Coding assistant\n")
    context = []
    while True: 
        msg = input(">>> ")
        if msg[0] == "/": 
            if msg == "/clear": 
                context = []
                print("Context cleared")
            else:
                print(f"cmd: {msg} unknown") 
        else:
            context.append({"role": "user", "content": msg})
            print("Thinking...")
            rsp = llm.responses.create(
                model=MODEL,
                reasoning= { "effort": REASONING },
                instructions=system_prompt,
                input=context,
                tools=[bash.schema]

            )
            context += rsp.output
            for item in rsp.output:
                if item.type == "function_call":
                    if item.name == bash.schema["name"]:
                        _args = json.loads(item.arguments)
                        try:
                            if should_i_execute(_args["command"]):
                                rsp = bash.run_bash_command(**_args)
                                rsp = json.dumps(rsp)
                        except Exception as e:
                                rsp = str(e)
                        final = {
                            "type": "function_call_output",  
                            "call_id": item.call_id,
                            "output": rsp
                        }
                        context.append(final)
                        get_answer = llm.responses.create(
                            model=MODEL,
                            reasoning= { "effort": REASONING },
                            instructions=system_prompt,
                            input=context,
                            tools=[bash.schema]

                        )
                        context += get_answer.output
                        print(get_answer.output_text)
                elif item.type == "message":
                    print(rsp.output_text)
            print("\n")
except KeyboardInterrupt:
    print("\nThanks! See you")


