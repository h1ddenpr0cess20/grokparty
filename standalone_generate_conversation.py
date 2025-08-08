import random
from typing import List, Dict
import os
import aiohttp

class GrokAPI:
    """Handles communication with Grok API"""

    def __init__(self):
        self.api_key = os.getenv("GROK_API_KEY")
        self.base_url = "https://api.x.ai/v1"

    async def send_request(
        self,
        model: str,
        messages: List[Dict],
        temperature: float = 0.8,
        disable_search: bool = False
    ) -> str:
        """Send a request to Grok API"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        search_params = (
            {
                "mode": "auto",
                "return_citations": True,
                "max_search_results": 10,
                "sources": [
                    {"type": "web", "country": "us"},
                    {"type": "news", "country": "us"},
                    {"type": "x"},
                ],
            }
            if not disable_search
            else None
        )
        payload = {
            "model": model,
            "messages": messages,
            "search_parameters": search_params,
            "temperature": temperature,
            "stream": False,
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
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

    def create_prompt(
        self,
        history: str,
        conversation_type: str,
        topic: str,
        setting: str,
    ) -> List[Dict]:
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
                """,
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
                """,
            },
        ]

    async def respond(
        self,
        grok_api: GrokAPI,
        history: str,
        conversation_type: str,
        topic: str,
        setting: str,
    ) -> str:
        """Generate a response from this character"""
        messages = self.create_prompt(history, conversation_type, topic, setting)
        return await grok_api.send_request(self.model, messages, disable_search=False)


async def _determine_next_speaker(
    grok_api: GrokAPI,
    characters: List[Character],
    current_speaker: Character,
    history: List[str],
    conversation_type: str,
    model: str,
) -> Character:
    """Determine who should speak next."""
    if len(characters) == 2:
        return next(c for c in characters if c is not current_speaker)

    participant_names = [c.personality for c in characters]
    history_string = "\n".join(history)
    messages = [
        {
            "role": "user",
            "content": f"""Based on this {conversation_type} history and listed participants,
reply with the name of the most likely next speaker as it appears before their line
and an explanation of your reasoning in the format of "<name>|<reason>" and nothing else.
Avoid a round-robin style conversation.

Participant names: {', '.join(participant_names)}

{history_string}
""",
        }
    ]
    try:
        response = await grok_api.send_request(model, messages, temperature=0.3, disable_search=True)
        speaker_name = response.split("|")[0].strip()
        for character in characters:
            if character.personality == speaker_name:
                return character
    except Exception:
        pass
    return random.choice([c for c in characters if c is not current_speaker])


async def generate_conversation(
    model: str = "grok-3-mini",
    characters: List[str] = None,
    conversation_type: str = "conversation",
    topic: str = "anything",
    setting: str = "anywhere",
    turns: int = 10,
) -> Dict[str, object]:
    """Generate a conversation between characters.


    Args:
        api_key: Grok API key.
        model: Model to use for all characters and decision making.
        characters: List of character personality descriptions.
        conversation_type: Type of conversation (e.g., conversation, debate).
        topic: Conversation topic.
        setting: Conversation setting.
        turns: Number of turns to generate.

    Returns:
        A dictionary representing the conversation with messages.
    """
        
    

    grok_api = GrokAPI()
    char_objs = [Character(personality=c, model=model, color="") for c in characters]

    history: List[str] = []
    current_speaker = random.choice(char_objs)
    other_participants = [c.personality for c in char_objs if c is not current_speaker]
    intro = (
        f"start a {conversation_type} about {topic} with {', '.join(other_participants)}."
        f" the setting is {setting}."
    )
    message = await current_speaker.respond(
        grok_api, intro, conversation_type, topic, setting
    )
    history.append(f"{current_speaker.personality}: {message}")

    for _ in range(turns - 1):
        next_speaker = await _determine_next_speaker(
            grok_api,
            char_objs,
            current_speaker,
            history,
            conversation_type,
            model,
        )
        history_string = "\n".join(history)
        msg = await next_speaker.respond(
            grok_api, history_string, conversation_type, topic, setting
        )
        history.append(f"{next_speaker.personality}: {msg}")
        current_speaker = next_speaker

    data = {
        "type": conversation_type,
        "topic": topic,
        "setting": setting,
        "participants": [c.personality for c in char_objs],
        "messages": [],
    }

    for entry in history:
        colon_index = entry.find(":")
        if colon_index > 0:
            speaker = entry[:colon_index].strip()
            content = entry[colon_index + 1 :].strip()
            data["messages"].append({"speaker": speaker, "content": content})

    return data