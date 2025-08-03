import argparse
import sys
import os
import asyncio
from rich.console import Console
from rich.table import Table
from grokparty.app import GrokParty

console = Console(width=120)

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
    console.print("[bold blue]Available Models:[/bold blue]\n")
    
    models = [
            {"id": "grok-4", "name": "Grok 4"},
            {"id": "grok-3-mini", "name": "Grok 3 Mini"},
            {"id": "grok-3-fast", "name": "Grok 3 Fast"},
            {"id": "grok-3-mini-fast", "name": "Grok 3 Mini Fast"},
            {"id": "grok-3", "name": "Grok 3"}
    ]
    
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Model ID", style="cyan")
    table.add_column("Name", style="green")
    
    for model in models:
        table.add_row(model["id"], model["name"])
    
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
    except Exception as e:
        console.print(f"\n[yellow]Goodbye! {e}[/yellow]")
        sys.exit(1)

if __name__ == "__main__":
    main()
