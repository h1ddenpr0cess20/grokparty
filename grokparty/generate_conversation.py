import random
from typing import List, Dict

from grokparty.core.grok_api import GrokAPI
from grokparty.models.character import Character


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
and an explanation of your reasoning in the format of \"<name>|<reason>\" and nothing else.
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
    api_key: str,
    model: str,
    characters: List[str],
    conversation_type: str,
    topic: str,
    setting: str,
    turns: int,
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

    grok_api = GrokAPI(api_key)
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
            grok_api, char_objs, current_speaker, history, conversation_type, model
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
