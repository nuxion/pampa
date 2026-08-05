import os
from openai import OpenAI

#MODEL = "gpt-5.6-luna" # GPT-5.6 Luna 
MODEL = "gpt-5-nano"
REASONING = "low"
           # GPT 5 nano a

available_tools = ["bash"]

system_prompt = f"""
you are an expert coding assistant called Pampa. You help users by reading files, 
executing commands, editing code, and writing new files.

{ ",".join(available_tools) }
"""

llm = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY")
)

try: 
    print("Welcome to Pampa Coding assistant\n")
    while True: 
        msg = input("Type your msg: ")
        print("Thinking...")
        rsp = llm.responses.create(
            model=MODEL,
            reasoning= { "effort": REASONING },
            instructions=system_prompt,
            input=msg,

        )
        print("Your message: ", rsp.output_text)
except KeyboardInterrupt:
    print("\nThanks! See you")


