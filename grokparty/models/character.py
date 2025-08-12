from typing import List, Dict
from grokparty.core.grok_api import GrokAPI


class Character:
    """Represents an AI character with personality and model"""
    
    def __init__(self, personality: str, model: str, color: str):
        self.personality = personality
        self.model = model
        self.color = color
       
    
    def create_prompt(self, history: str, conversation_type: str, topic: str, setting: str, mood: str) -> List[Dict]:
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
                The mood is {mood}
                Here are the last few messages:

                {history}

                [Stay focused on the main topic, but feel free to explore different aspects of it. 
                Only move to closely related subjects if the current discussion has reached a natural conclusion.]
                """
            }
        ]
    
    async def respond(self, grok_api: GrokAPI, history: str, conversation_type: str, topic: str, setting: str, mood: str) -> str:
        """Generate a response from this character"""
        messages = self.create_prompt(history, conversation_type, topic, setting, mood)
        return await grok_api.send_request(self.model, messages, disable_search=False)
