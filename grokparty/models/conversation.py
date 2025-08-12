from typing import List
import asyncio
import random
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from grokparty.models.character import Character

console = Console(width=120, highlight=False)

class Conversation:
    """Manages the conversation flow"""
    
    def __init__(self, conversation_type: str, topic: str, setting: str, characters: List[Character], decision_model: str, mood: str = "friendly"):
        self.conversation_type = conversation_type
        self.topic = topic
        self.setting = setting
        self.mood = mood
        self.characters = characters
        self.decision_model = decision_model
        self.history = []
        self.is_active = False
        self.is_paused = False
        self.current_speaker = None

    
    async def determine_next_speaker(self, grok_api) -> Character:
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
            response = await grok_api.send_request(self.decision_model, messages, temperature=0.3, disable_search=True)
            speaker_name = response.split('|')[0].strip()
            
            # Find the character by name
            for character in self.characters:
                if character.personality == speaker_name:
                    return character
        except Exception as e:
            console.print(f"[red]Error determining next speaker: {e}[/red]")
        
        # Fallback to random selection
        return random.choice(self.characters)
    
    async def start(self, grok_api):
        """Start the conversation"""
        self.is_active = True
        self.is_paused = False
        
        self._display_conversation_info()

        self.current_speaker = random.choice(self.characters)
        
        other_participants = [c.personality for c in self.characters if c != self.current_speaker]
        intro = f"start a {self.conversation_type} about {self.topic} with {', '.join(other_participants)}. the setting is {self.setting}."
        
        with console.status(f"[{self.current_speaker.color}]{self.current_speaker.personality}[/{self.current_speaker.color}] is thinking..."):
            message = await self.current_speaker.respond(grok_api, intro, self.conversation_type, self.topic, self.setting, self.mood)
        
        self.history.append(f"{self.current_speaker.personality}: {message}")
        self._display_message(self.current_speaker, message)
        
        await self._continue_conversation(grok_api)
    
    async def _continue_conversation(self, grok_api):
        """Continue the conversation loop"""
        try:
            while self.is_active:
                while self.is_paused and self.is_active:
                    await asyncio.sleep(0.1)  # Check every 100ms for better responsiveness
                
                if not self.is_active:
                    break
                
                await asyncio.sleep(2)
                
                if not self.is_active:
                    break
                if self.is_paused:
                    continue
                
                next_speaker = await self.determine_next_speaker(grok_api)
                
                history_string = "\n".join(self.history)
                with console.status(f"[{next_speaker.color}]{next_speaker.personality}[/{next_speaker.color}] is thinking..."):
                    message = await next_speaker.respond(grok_api, history_string, self.conversation_type, self.topic, self.setting, self.mood)
                
                self.current_speaker = next_speaker
                
                self.history.append(f"{next_speaker.personality}: {message}")
                self._display_message(next_speaker, message)
        except Exception as e:
            console.print(f"[red]Error in conversation loop: {e}[/red]")
            self.stop()
    
    def _display_conversation_info(self):
        """Display conversation information"""
        info_table = Table(show_header=False, box=None, padding=(0, 1))
        info_table.add_row("Type:", self.conversation_type)
        info_table.add_row("Topic:", self.topic)
        info_table.add_row("Setting:", self.setting)
        info_table.add_row("Mood:", self.mood)
        
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
