# 🤖 GrokParty

**Terminal-based AI Character Conversations powered by Grok models**

GrokParty is a Python application that creates dynamic conversations between AI characters using Grok's powerful language models. Watch as different personalities interact, debate, and discuss topics in real-time!

## Features

- **Multiple AI Characters**: Create 2-4 unique characters with different personalities
- **Grok-Powered**: Uses all available Grok models (Grok 2, Grok 3, Grok 3 Mini, etc.)
- **Rich Terminal UI**: Beautiful terminal interface with colors, panels, and markdown
- **Dynamic Conversations**: AI-driven speaker selection for natural conversation flow
- **Multiple Conversation Types**: Debates, meetings, brainstorming, therapy sessions, and more
- **Export Functionality**: Save conversations as JSON files
- **Real-time Display**: Watch conversations unfold with typing indicators

## Installation

1. **Clone or download** the GrokParty directory
2. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
3. **Get a Grok API key** from [X.AI](https://x.ai/)
4. **Set your API key** (optional):
   ```bash
   export GROK_API_KEY="your-api-key-here"
   ```

## Usage

Run GrokParty from the terminal:

```bash
python main.py
```

### Step-by-Step Process

1. **Enter API Key**: If not set as environment variable, you'll be prompted
2. **Choose Conversation Type**: Select from 8 different conversation styles
3. **Set Topic & Setting**: Define what they'll discuss and where
4. **Select Decision Model**: Choose which Grok model decides who speaks next
5. **Create Characters**: Add 2-4 characters with unique personalities and models
6. **Watch the Conversation**: Sit back and enjoy the AI interaction!

### Conversation Types

- **Conversation**: General discussion
- **Debate**: Structured argument with opposing views
- **Argument**: More heated disagreement
- **Meeting**: Professional discussion
- **Brainstorming**: Creative idea generation
- **Lighthearted**: Casual, fun conversation
- **Joking**: Comedy and humor focus
- **Therapy**: Supportive, therapeutic dialogue

### Available Grok Models

- **Grok 4**: Latest flagship model
- **Grok 3 Mini**: Efficient next-generation model
- **Grok 3 Fast**: High-speed processing model
- **Grok 3 Mini Fast**: Optimized for speed and efficiency
- **Grok 3**: Advanced conversational model

## Controls

- **p**: Pause or resume the conversation (no Enter needed)
- **s**: Stop the conversation (no Enter needed)
- **e**: Export the conversation history as JSON (no Enter needed)
- **Ctrl+C**: Quit immediately
- **New Conversation**: Start fresh with new parameters

## Example Usage

```bash
$ python main.py

🤖 Welcome to GrokParty!

Create conversations between AI characters powered by Grok models.

Select conversation type:
  1. Conversation
  2. Debate
  3. Argument
  ...

What should they talk about? [anything interesting]: The future of AI
Where is this conversation taking place? [a comfortable room]: A tech conference

Available Grok models:
  1. Grok 4 - Latest flagship model
  2. Grok 3 Mini - Efficient next-generation model
  ...

How many characters? (2-4) [2]: 3

Character 1:
Describe character 1's personality [Character 1]: An optimistic AI researcher
Select model for An optimistic AI researcher (1-5) [1]: 1

Character 2:
Describe character 2's personality [Character 2]: A cautious ethicist
Select model for A cautious ethicist (1-5) [1]: 2

Character 3:
Describe character 3's personality [Character 3]: A pragmatic engineer
Select model for A pragmatic engineer (1-5) [1]: 3

Starting conversation...
Press 'p' to pause, 's' to stop, 'e' to export or Ctrl+C to quit
```

## File Structure

```
grokparty/
├── main.py              # Simplified entry point
├── requirements.txt     # Python dependencies
├── README.md           # This file
├── __init__.py         # Package initialization
├── app.py              # Main application class
├── core/               # Core functionality
│   ├── __init__.py     # Core module initialization
│   └── grok_api.py    # Grok API communication
├── models/             # Data models
│   ├── __init__.py     # Models module initialization
│   ├── character.py    # Character model
│   └── conversation.py # Conversation model
└── cli/                # Command line interface
    ├── __init__.py     # CLI module initialization
    └── cli.py         # Command line argument parsing and main function
```

## Requirements

- Python 3.7+
- Internet connection for Grok API
- Valid Grok API key
- Terminal with color support (most modern terminals)

## API Key Setup

You can provide your Grok API key in several ways:

1. **Environment variable** (recommended):
   ```bash
   export GROK_API_KEY="your-key-here"
   ```

2. **Enter when prompted**: The app will ask for your key if not found

3. **Command line** (for scripts):
   ```bash
   GROK_API_KEY="your-key" python main.py
   ```

## Troubleshooting

### Common Issues

- **"API key required"**: Make sure you have a valid Grok API key
- **Connection errors**: Check your internet connection
- **Import errors**: Run `pip install -r requirements.txt`
- **Terminal display issues**: Use a modern terminal with color support

### Getting Help

If you encounter issues:
1. Check that all dependencies are installed
2. Verify your API key is valid
3. Ensure you have a stable internet connection
4. Try with a simpler conversation setup first

## Tips for Better Conversations

- **Diverse Personalities**: Create characters with contrasting viewpoints
- **Specific Topics**: More specific topics lead to more engaging discussions
- **Mix Models**: Use different Grok models for varied response styles
- **Interesting Settings**: Creative settings can influence conversation tone

## Export Format

Conversations are exported as JSON with this structure:

```json
{
  "type": "debate",
  "topic": "The future of AI",
  "setting": "A tech conference",
  "participants": ["An optimistic AI researcher", "A cautious ethicist"],
  "messages": [
    {
      "speaker": "An optimistic AI researcher",
      "content": "I believe AI will revolutionize how we solve global challenges...",
      "timestamp": "2025-01-10T17:30:00"
    }
  ]
}
```

---

**Enjoy creating amazing AI conversations with GrokParty!** 🎉
