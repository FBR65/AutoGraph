#!/usr/bin/env python3
"""
AutoGraph - Main Entry Point

Automatisierte Knowledge Graph Generierung aus verschiedenen Datenquellen.
Zentraler Entry Point für alle AutoGraph-Funktionen.
"""

import sys
import argparse
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Direct CLI import - bypass problematic imports
try:
    from autograph.cli import main as cli_main
except ImportError as e:
    print(f"❌ Fehler beim Import der CLI: {e}")
    print("Stellen Sie sicher, dass alle Abhängigkeiten installiert sind:")
    print("  uv pip install -e .")
    sys.exit(1)


def main():
    """
    Hauptfunktion für AutoGraph

    Delegiert an das CLI-System für alle Funktionen:
    - Text-Verarbeitung (NER + Relation Extraction)
    - YAML-Generierung (Entity-Kataloge & Ontologien)
    - API-Server
    - Datenbank-Management
    - Konfiguration
    """
    parser = argparse.ArgumentParser(
        description="AutoGraph - Automated Knowledge Graph Generation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Interactive Menu
  python main.py menu
  
  # Process text with NER and relations
  python main.py run document.txt --processor both
  
  # Generate YAML entity catalog
  python main.py yaml entity-from-text --domain medizin --files *.txt
  
  # Start REST API server
  python main.py serve --port 8000
  
  # Initialize configuration
  python main.py init
  
For detailed help on any command:
  python main.py <command> --help
        """,
    )

    # Add version
    parser.add_argument("--version", action="version", version="AutoGraph 0.1.0")

    # If no arguments provided, show help
    if len(sys.argv) == 1:
        parser.print_help()
        print("\n🚀 Quick Start:")
        print("  python main.py menu     # Interactive menu")
        print("  python main.py --help   # Full help")
        return

    # Parse arguments and delegate to CLI
    parser.parse_known_args()[1]

    # Delegate to CLI system
    sys.argv = ["autograph"] + sys.argv[1:]
    cli_main()


if __name__ == "__main__":
    main()
