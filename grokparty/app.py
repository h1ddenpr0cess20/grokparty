import asyncio
import json
import os
from datetime import datetime
from typing import List
from rich.console import Console
from rich.markdown import Markdown
from rich.prompt import Prompt, Confirm
from grokparty.core.grok_api import GrokAPI
from grokparty.models.character import Character
from grokparty.models.conversation import Conversation

console = Console(width=120, highlight=False)

class GrokParty:
    """Main application class"""
    
    def __init__(self):
        self.grok_api = None
        self.conversation = None
        self.colors = ["red", "blue", "green", "yellow", "magenta", "cyan"]
    
    def display_welcome(self):
        """Display welcome message"""
        welcome_text = """
🤖 Welcome to GrokParty! 

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
        topic = Prompt.ask("What should they talk about?", default="anything")
        setting = Prompt.ask("Where is this conversation taking place?", default="anywhere")
        return topic, setting
    
    def select_models(self) -> str:
        """Select models for characters and decision making"""
        console.print("\n[bold]Available models:[/bold]")
        for i, model in enumerate(self.grok_api.models, 1): 
            console.print(f"  {i}. {model['name']}")
        
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
        
        # Get number of characters (minimum 2)
        while True:
            try:
                num_chars = int(Prompt.ask("How many characters? (minimum 2)", default="2"))
                if num_chars >= 2:
                    break
                else:
                    console.print("[red]Please enter a number 2 or greater.[/red]")
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
    
    async def _listen_for_commands(self):
        """Listen for keyboard commands in a separate task"""
        while self.conversation.is_active:
            try:
                # Use run_in_executor to call msvcrt functions without blocking the event loop
                has_key = await asyncio.get_event_loop().run_in_executor(None, self._check_for_key)
                if has_key:
                    key = await asyncio.get_event_loop().run_in_executor(None, self._get_key)
                    key = key.lower()
                    
                    if key == b'p' or key == 'p':  # Handle both bytes and string
                        if self.conversation.is_paused:
                            self.conversation.resume()
                        else:
                            self.conversation.pause()
                    elif key == b's' or key == 's':  # Handle both bytes and string
                        self.conversation.stop()
                        console.print("\n[red]Stopping conversation...[/red]")
                        return
            except Exception:
                # If msvcrt is not available, continue with brief sleep
                pass
                
            # Small delay to prevent excessive CPU usage
            await asyncio.sleep(0.1)
    
    async def run_conversation(self):
        """Run the main conversation with interactive controls"""
        try:
            # Start conversation and command listener as concurrent tasks
            conversation_task = asyncio.create_task(self.conversation.start(self.grok_api))
            command_task = asyncio.create_task(self._listen_for_commands())
            
            
            # Wait for either task to complete
            done, pending = await asyncio.wait(
                [conversation_task, command_task],
                return_when=asyncio.FIRST_COMPLETED
            )
            
            # Cancel any pending tasks
            for task in pending:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
                    
            # Wait for conversation task to complete if it's still running
            if not conversation_task.done():
                await conversation_task
                
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
    
    def _check_for_key(self):
        """Check if a key has been pressed (non-blocking)"""
        try:
            import msvcrt
            return msvcrt.kbhit()
        except ImportError:
            return False

    def _get_key(self):
        """Get the pressed key"""
        try:
            import msvcrt
            return msvcrt.getch()
        except ImportError:
            return ''
            
    async def main(self):
        """Main application loop"""
        self.display_welcome()
        
        # Setup API key
        if not self.setup_api_key():
            return
        
        while True:
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
            console.print("[dim]Press 'p' to pause/resume, 's' to stop[/dim]\n")
            
            # Run conversation
            await self.run_conversation()
            
            # Ask if user wants to export
            if Confirm.ask("\nWould you like to export this conversation?"):
                self.export_conversation()
            
            # Ask if user wants to start another conversation
            if not Confirm.ask("\nWould you like to start another conversation?"):
                break
            
            console.print("\n" + "="*50 + "\n")
            
        console.print("\n[yellow]Goodbye![/yellow]")
