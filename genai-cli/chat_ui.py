from prompt_toolkit import PromptSession
from prompt_toolkit.enums import EditingMode

from llm_chat import GoogleAIChat
from google.genai.types import Content
from google.genai.types import Part

from rich.console import Console

console = Console()
session = PromptSession(editing_mode=EditingMode.VI, vi_mode=True)
chat_client = GoogleAIChat()

history = []

while True:
    try:
        user_input = session.prompt(">> ")

        with console.status("[bold green]Generating response...[/bold green]"):
            response = chat_client.generate_response(user_input)

        console.print(f"[bold blue]AI:[/bold blue] {response}")
    except KeyboardInterrupt:
        console.print("[bold red]Exiting the chat. Goodbye![/bold red]")
        break
    except EOFError:
        console.print("[bold red]Exiting the chat. Goodbye![/bold red]")
        break

    history.append(Content(role="user", parts=[Part(text=user_input)]))
    history.append(Content(role="model", parts=[Part(text=response)]))
