#!/usr/bin/env python3
"""
GrokParty - Terminal-based AI Character Conversations
A Python application that creates conversations between AI characters using Grok models.
"""

import asyncio
import json
import os
import sys
import argparse
from datetime import datetime
from typing import List, Dict, Optional
import aiohttp
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.table import Table
from rich.text import Text
from rich.markdown import Markdown
from rich.live import Live
from rich.spinner import Spinner
from rich.layout import Layout
from rich.align import Align
import time

# Initialize Rich console
console = Console(width=120)

class GrokAPI:
    """Handles communication with Grok API"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.x.ai/v1"
        self.models = [
            {"id": "grok-4", "name": "Grok 4", "description": "Latest flagship model"},
            {"id": "grok-3-mini", "name": "Grok 3 Mini", "description": "Efficient next-generation model"},
            {"id": "grok-3-fast", "name": "Grok 3 Fast", "description": "High-speed processing model"},
            {"id": "grok-3-mini-fast", "name": "Grok 3 Mini Fast", "description": "Optimized for speed and efficiency"},
            {"id": "grok-3", "name": "Grok 3", "description": "Advanced conversational model"}
        ]
    
    async def send_request(self, model: str, messages: List[Dict], temperature: float = 0.8) -> str:
        """Send a request to Grok API"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "stream": False
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"API request failed: {response.status} - {error_text}")
                
                data = await response.json()
                return data["choices"][0]["message"]["content"]

class Character:
    """Represents an AI character with personality and model"""
    
    def __init__(self, personality: str, model: str, color: str):
        self.personality = personality
        self.model = model
        self.color = color
    
    def create_prompt(self, history: str, conversation_type: str, topic: str, setting: str) -> List[Dict]:
        """Create the prompt for this character"""
        return [
            {
                "role": "system",
                "content": f"""
                Assume the personality of {self.personality}.
                Roleplay as them and never break character.
                Do not speak as anyone else.
                Your responses should be around one to three sentences long, preferably one.
                Do not preface them with your name.
                """
            },
            {
                "role": "user",
                "content": f"""
                You're the next speaker in a {conversation_type} about {topic}.
                The setting is {setting}.
                Here are the last few messages:

                {history}

                [Stay focused on the main topic, but feel free to explore different aspects of it. 
                Only move to closely related subjects if the current discussion has reached a natural conclusion.]
                """
            }
        ]
    
    async def respond(self, grok_api: GrokAPI, history: str, conversation_type: str, topic: str, setting: str) -> str:
        """Generate a response from this character"""
        messages = self.create_prompt(history, conversation_type, topic, setting)
        return await grok_api.send_request(self.model, messages)

class Conversation:
    """Manages the conversation flow"""
    
    def __init__(self, conversation_type: str, topic: str, setting: str, characters: List[Character], decision_model: str):
        self.conversation_type = conversation_type
        self.topic = topic
        self.setting = setting
        self.characters = characters
        self.decision_model = decision_model
        self.history = []
        self.is_active = False
        self.is_paused = False
        self.current_speaker = None
    
    async def determine_next_speaker(self, grok_api: GrokAPI) -> Character:
        """Determine who should speak next"""
        if len(self.characters) == 2:
            # For two characters, alternate
            if self.current_speaker:
                return next(c for c in self.characters if c != self.current_speaker)
            else:
                return self.characters[0]
        
        # For more characters, use AI to decide
        participant_names = [c.personality for c in self.characters]
        history_string = "\n".join(self.history)
        
        messages = [{
            "role": "user",
            "content": f"""
            Based on this {self.conversation_type} history and listed participants,
            reply with the name of the most likely next speaker as it appears before their line
            and an explanation of your reasoning in the format of "<name>|<reason>" and nothing else.
            Avoid a round-robin style conversation.

            Participant names: {', '.join(participant_names)}

            {history_string}
            """
        }]
        
        try:
            response = await grok_api.send_request(self.decision_model, messages, temperature=0.3)
            speaker_name = response.split('|')[0].strip()
            
            # Find the character by name
            for character in self.characters:
                if character.personality == speaker_name:
                    return character
        except Exception as e:
            console.print(f"[red]Error determining next speaker: {e}[/red]")
        
        # Fallback to random selection
        import random
        return random.choice(self.characters)
    
    async def start(self, grok_api: GrokAPI):
        """Start the conversation"""
        self.is_active = True
        self.is_paused = False
        
        # Display conversation info
        self._display_conversation_info()
        
        # Choose random first speaker
        import random
        self.current_speaker = random.choice(self.characters)
        
        # Create intro prompt
        other_participants = [c.personality for c in self.characters if c != self.current_speaker]
        intro = f"start a {self.conversation_type} about {self.topic} with {', '.join(other_participants)}. the setting is {self.setting}."
        
        # Get first response
        with console.status(f"[{self.current_speaker.color}]{self.current_speaker.personality}[/{self.current_speaker.color}] is thinking..."):
            message = await self.current_speaker.respond(grok_api, intro, self.conversation_type, self.topic, self.setting)
        
        # Add to history and display
        self.history.append(f"{self.current_speaker.personality}: {message}")
        self._display_message(self.current_speaker, message)
        
        # Continue conversation
        await self._continue_conversation(grok_api)
    
    async def _continue_conversation(self, grok_api: GrokAPI):
        """Continue the conversation loop"""
        try:
            while self.is_active and not self.is_paused:
                await asyncio.sleep(2)  # Brief pause between messages
                
                if not self.is_active or self.is_paused:
                    break
                
                # Determine next speaker
                next_speaker = await self.determine_next_speaker(grok_api)
                
                # Get response
                history_string = "\n".join(self.history)
                with console.status(f"[{next_speaker.color}]{next_speaker.personality}[/{next_speaker.color}] is thinking..."):
                    message = await next_speaker.respond(grok_api, history_string, self.conversation_type, self.topic, self.setting)
                
                # Update current speaker
                self.current_speaker = next_speaker
                
                # Add to history and display
                self.history.append(f"{next_speaker.personality}: {message}")
                self._display_message(next_speaker, message)
        except Exception as e:
            console.print(f"[red]Error in conversation loop: {e}[/red]")
            self.stop()
    
    def _display_conversation_info(self):
        """Display conversation information"""
        info_table = Table(show_header=False, box=None, padding=(0, 1))
        info_table.add_row("Type:", self.conversation_type.title())
        info_table.add_row("Topic:", self.topic)
        info_table.add_row("Setting:", self.setting)
        
        participants_text = Text()
        for i, character in enumerate(self.characters):
            if i > 0:
                participants_text.append(", ")
            participants_text.append(character.personality, style=character.color)
        
        info_table.add_row("Participants:", participants_text)
        
        console.print(Panel(info_table, title="[bold blue]Conversation Info[/bold blue]", border_style="blue"))
        console.print()
    
    def _display_message(self, character: Character, message: str):
        """Display a message from a character"""
        # Create a panel with the character's message
        message_panel = Panel(
            message,
            title=f"[{character.color}]{character.personality}[/{character.color}]",
            border_style=character.color,
            padding=(0, 1)
        )
        console.print(message_panel)
        console.print()
    
    def pause(self):
        """Pause the conversation"""
        self.is_paused = True
        console.print("[yellow]Conversation paused.[/yellow]")
    
    def resume(self):
        """Resume the conversation"""
        self.is_paused = False
        console.print("[green]Conversation resumed.[/green]")
    
    def stop(self):
        """Stop the conversation"""
        self.is_active = False
        self.is_paused = False
        console.print("[red]Conversation stopped.[/red]")

class GrokParty:
    """Main application class"""
    
    def __init__(self):
        self.grok_api = None
        self.conversation = None
        self.colors = ["red", "blue", "green", "yellow", "magenta", "cyan"]
    
    def display_welcome(self):
        """Display welcome message"""
        welcome_text = """
# 🤖 Welcome to GrokParty! 

**Create conversations between AI characters powered by Grok models.**

Choose your characters, set the scene, and watch them interact in real-time!
        """
        console.print(Markdown(welcome_text))
        console.print()
    
    def setup_api_key(self) -> bool:
        """Setup Grok API key"""
        # Check if API key exists in environment or config
        api_key = os.getenv('GROK_API_KEY')
        
        if not api_key:
            console.print("[yellow]Grok API key not found in environment.[/yellow]")
            api_key = Prompt.ask("Please enter your Grok API key", password=True)
        
        if not api_key:
            console.print("[red]API key is required to use GrokParty.[/red]")
            return False
        
        try:
            self.grok_api = GrokAPI(api_key)
            console.print("[green]✓ API key configured successfully![/green]")
            return True
        except Exception as e:
            console.print(f"[red]Error configuring API: {e}[/red]")
            return False
    
    def select_conversation_type(self) -> str:
        """Select conversation type"""
        types = [
            "conversation", "debate", "argument", "meeting", 
            "brainstorming", "lighthearted", "joking", "therapy"
        ]
        
        console.print("[bold]Select conversation type:[/bold]")
        for i, conv_type in enumerate(types, 1):
            console.print(f"  {i}. {conv_type.title()}")
        
        while True:
            try:
                choice = int(Prompt.ask("Enter choice (1-8)", default="1"))
                if 1 <= choice <= len(types):
                    return types[choice - 1]
                else:
                    console.print("[red]Invalid choice. Please enter 1-8.[/red]")
            except ValueError:
                console.print("[red]Please enter a valid number.[/red]")
    
    def get_topic_and_setting(self) -> tuple:
        """Get conversation topic and setting"""
        topic = Prompt.ask("What should they talk about?", default="anything interesting")
        setting = Prompt.ask("Where is this conversation taking place?", default="a comfortable room")
        return topic, setting
    
    def select_models(self) -> tuple:
        """Select models for characters and decision making"""
        console.print("\n[bold]Available Grok models:[/bold]")
        for i, model in enumerate(self.grok_api.models, 1):
            console.print(f"  {i}. {model['name']} - {model['description']}")
        
        # Select decision model
        while True:
            try:
                choice = int(Prompt.ask("Select decision model (1-5)", default="1"))
                if 1 <= choice <= len(self.grok_api.models):
                    decision_model = self.grok_api.models[choice - 1]["id"]
                    break
                else:
                    console.print("[red]Invalid choice. Please enter 1-5.[/red]")
            except ValueError:
                console.print("[red]Please enter a valid number.[/red]")
        
        return decision_model
    
    def create_characters(self, decision_model: str) -> List[Character]:
        """Create character list"""
        characters = []
        
        # Get number of characters (2-4)
        while True:
            try:
                num_chars = int(Prompt.ask("How many characters? (2-4)", default="2"))
                if 2 <= num_chars <= 4:
                    break
                else:
                    console.print("[red]Please enter a number between 2 and 4.[/red]")
            except ValueError:
                console.print("[red]Please enter a valid number.[/red]")
        
        console.print(f"\n[bold]Creating {num_chars} characters:[/bold]")
        
        for i in range(num_chars):
            console.print(f"\n[bold]Character {i + 1}:[/bold]")
            
            # Get personality
            personality = Prompt.ask(f"Describe character {i + 1}'s personality", 
                                   default=f"Character {i + 1}")
            
            # Select model for this character
            console.print("Available models:")
            for j, model in enumerate(self.grok_api.models, 1):
                console.print(f"  {j}. {model['name']}")
            
            while True:
                try:
                    model_choice = int(Prompt.ask(f"Select model for {personality} (1-5)", default="1"))
                    if 1 <= model_choice <= len(self.grok_api.models):
                        character_model = self.grok_api.models[model_choice - 1]["id"]
                        break
                    else:
                        console.print("[red]Invalid choice. Please enter 1-5.[/red]")
                except ValueError:
                    console.print("[red]Please enter a valid number.[/red]")
            
            # Assign color
            color = self.colors[i % len(self.colors)]
            
            characters.append(Character(personality, character_model, color))
            console.print(f"[{color}]✓ {personality} created with {self.grok_api.models[model_choice-1]['name']}[/{color}]")
        
        return characters
    
    async def run_conversation(self):
        """Run the main conversation"""
        try:
            await self.conversation.start(self.grok_api)
            
            # Keep the conversation running until manually stopped
            console.print("\n[dim]Conversation is running. Press Ctrl+C to stop.[/dim]")
            while self.conversation.is_active:
                await asyncio.sleep(1)
                
        except KeyboardInterrupt:
            console.print("\n[yellow]Conversation interrupted by user.[/yellow]")
            if self.conversation:
                self.conversation.stop()
        except Exception as e:
            console.print(f"\n[red]Error during conversation: {e}[/red]")
            import traceback
            console.print(f"[red]Traceback: {traceback.format_exc()}[/red]")
            if self.conversation:
                self.conversation.stop()
    
    def export_conversation(self):
        """Export conversation to file"""
        if not self.conversation or not self.conversation.history:
            console.print("[yellow]No conversation to export.[/yellow]")
            return
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"grokparty_conversation_{timestamp}.json"
        
        data = {
            "type": self.conversation.conversation_type,
            "topic": self.conversation.topic,
            "setting": self.conversation.setting,
            "participants": [c.personality for c in self.conversation.characters],
            "messages": []
        }
        
        for message in self.conversation.history:
            colon_index = message.find(':')
            if colon_index > 0:
                speaker = message[:colon_index].strip()
                content = message[colon_index + 1:].strip()
                data["messages"].append({
                    "speaker": speaker,
                    "content": content,
                    "timestamp": datetime.now().isoformat()
                })
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            console.print(f"[green]✓ Conversation exported to {filename}[/green]")
        except Exception as e:
            console.print(f"[red]Error exporting conversation: {e}[/red]")
    
    async def main(self):
        """Main application loop"""
        self.display_welcome()
        
        # Setup API key
        if not self.setup_api_key():
            return
        
        while True:
            try:
                # Get conversation parameters
                conversation_type = self.select_conversation_type()
                topic, setting = self.get_topic_and_setting()
                decision_model = self.select_models()
                characters = self.create_characters(decision_model)
                
                # Create conversation
                self.conversation = Conversation(
                    conversation_type, topic, setting, characters, decision_model
                )
                
                console.print("\n[bold green]Starting conversation...[/bold green]")
                console.print("[dim]Press Ctrl+C to stop the conversation[/dim]\n")
                
                # Run conversation
                await self.run_conversation()
                
                # Ask if user wants to export
                if Confirm.ask("\nWould you like to export this conversation?"):
                    self.export_conversation()
                
                # Ask if user wants to start another conversation
                if not Confirm.ask("\nWould you like to start another conversation?"):
                    break
                
                console.print("\n" + "="*50 + "\n")
                
            except KeyboardInterrupt:
                console.print("\n[yellow]Goodbye![/yellow]")
                break
            except Exception as e:
                console.print(f"\n[red]An error occurred: {e}[/red]")
                if not Confirm.ask("Would you like to try again?"):
                    break

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="GrokParty - Terminal-based AI Character Conversations",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py                    # Interactive mode
  python main.py --version          # Show version
  python main.py --models           # List available models
  
Environment Variables:
  GROK_API_KEY                      # Your Grok API key
        """
    )
    
    parser.add_argument(
        "--version", 
        action="version", 
        version="GrokParty 1.0.0"
    )
    
    parser.add_argument(
        "--models", 
        action="store_true",
        help="List available Grok models and exit"
    )
    
    parser.add_argument(
        "--api-key",
        type=str,
        help="Grok API key (overrides environment variable)"
    )
    
    return parser.parse_args()

def list_models():
    """List available Grok models"""
    console.print("[bold blue]Available Grok Models:[/bold blue]\n")
    
    # Create a temporary GrokAPI instance to get models
    models = [
        {"id": "grok-4", "name": "Grok 4", "description": "Latest flagship model"},
        {"id": "grok-3-mini", "name": "Grok 3 Mini", "description": "Efficient next-generation model"},
        {"id": "grok-3-fast", "name": "Grok 3 Fast", "description": "High-speed processing model"},
        {"id": "grok-3-mini-fast", "name": "Grok 3 Mini Fast", "description": "Optimized for speed and efficiency"},
        {"id": "grok-3", "name": "Grok 3", "description": "Advanced conversational model"}
    ]
    
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Model ID", style="cyan")
    table.add_column("Name", style="green")
    table.add_column("Description", style="white")
    
    for model in models:
        table.add_row(model["id"], model["name"], model["description"])
    
    console.print(table)

def main():
    """Entry point"""
    args = parse_arguments()
    
    # Handle special commands
    if args.models:
        list_models()
        return
    
    try:
        app = GrokParty()
        
        # Set API key from command line if provided
        if args.api_key:
            os.environ['GROK_API_KEY'] = args.api_key
        
        asyncio.run(app.main())
    except KeyboardInterrupt:
        console.print("\n[yellow]Goodbye![/yellow]")
    except Exception as e:
        console.print(f"[red]Fatal error: {e}[/red]")
        sys.exit(1)

if __name__ == "__main__":
    main()
