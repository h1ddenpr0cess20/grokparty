"""FastMCP server wrapper around the standalone GrokParty conversation generator."""

from __future__ import annotations

from typing import List

from fastmcp import FastMCP, Response, Schema
from pydantic import Field, model_validator

from standalone_generate_conversation import generate_conversation as standalone_generate


app = FastMCP(
    "grokparty",
    summary="Generate GrokParty conversations via MCP",
    description=(
        "Expose the standalone GrokParty conversation generator as an MCP tool "
        "compatible with clients that speak the Model Context Protocol."
    ),
)


class GenerateConversationArgs(Schema):
    """Arguments for the GrokParty `generate_conversation` MCP tool."""

    model: str = Field(
        default="grok-3-mini",
        description="Model ID to use for the conversation.",
    )
    characters: List[str] = Field(
        description="List of character descriptions to include in the conversation.",
        min_length=2,
    )
    conversation_type: str = Field(
        default="conversation",
        description="Style of interaction, such as conversation or debate.",
    )
    topic: str = Field(
        default="anything",
        description="Topic the participants should discuss.",
    )
    setting: str = Field(
        default="anywhere",
        description="Setting for the conversation.",
    )
    turns: int = Field(
        default=10,
        ge=1,
        le=50,
        description="Number of turns (messages) to generate.",
    )

    @model_validator(mode="after")
    def _validate_characters(self) -> "GenerateConversationArgs":
        if len(self.characters) < 2:
            raise ValueError("At least two characters are required to generate a conversation.")
        return self


@app.tool()
async def generate_conversation(args: GenerateConversationArgs) -> Response:
    """Proxy to the existing standalone conversation generator."""

    conversation = await standalone_generate(
        model=args.model,
        characters=args.characters,
        conversation_type=args.conversation_type,
        topic=args.topic,
        setting=args.setting,
        turns=args.turns,
    )
    return Response.json(conversation)


if __name__ == "__main__":
    app.run()
