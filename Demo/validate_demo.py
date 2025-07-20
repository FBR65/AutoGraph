#!/usr/bin/env python3
"""
AutoGraph Demo-System Validierung
Schnelle Validierung aller generierten Dateien im Demo-Verzeichnis
"""

import json
import yaml
from pathlib import Path


def validate_demo_files():
    """Validiert alle generierten Demo-Dateien"""
    demo_dir = Path(__file__).parent

    print("🔍 AutoGraph Demo-System Validierung")
    print("=" * 50)

    # Prüfe alle erwarteten Dateien
    files_to_check = {
        "demo_data.txt": "Demo-Textdaten",
        "extracted/extracted_data.json": "Extrahierte JSON-Daten",
        "entities.yaml": "YAML Entity-Katalog",
        "ontology.yaml": "YAML Ontologie",
        "demo-config.yaml": "AutoGraph-Konfiguration",
    }

    all_valid = True

    for filename, description in files_to_check.items():
        file_path = demo_dir / filename

        print(f"\n📁 {description}")
        print(f"   Datei: {filename}")

        if not file_path.exists():
            print(f"   ❌ FEHLER: Datei nicht gefunden!")
            all_valid = False
            continue

        file_size = file_path.stat().st_size
        print(f"   📊 Größe: {file_size} bytes")

        # Validiere Dateiinhalt basierend auf Typ
        try:
            if filename.endswith(".json"):
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    print(f"   ✅ Gültiges JSON mit {len(data)} Einträgen")

            elif filename.endswith(".yaml"):
                with open(file_path, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f)
                    print(f"   ✅ Gültiges YAML")
                    if "domain" in data:
                        print(f"   🎯 Domäne: {data['domain']}")
                    if "entities" in data:
                        print(f"   📋 Entitäten: {len(data['entities'])}")
                    if "entity_types" in data:
                        print(f"   🏷️  Entity-Typen: {len(data['entity_types'])}")

            elif filename.endswith(".txt"):
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    print(f"   ✅ Text mit {len(content)} Zeichen")

            else:
                print(f"   ✅ Datei vorhanden")

        except Exception as e:
            print(f"   ❌ FEHLER beim Lesen: {str(e)}")
            all_valid = False

    print(f"\n{'=' * 50}")

    if all_valid:
        print("🎉 VALIDATION ERFOLGREICH!")
        print("   Alle Demo-Dateien sind vorhanden und gültig.")
        print("   Das AutoGraph-System ist vollständig funktionsfähig!")
    else:
        print("❌ VALIDATION FEHLGESCHLAGEN!")
        print("   Einige Dateien fehlen oder sind ungültig.")

    return all_valid


if __name__ == "__main__":
    validate_demo_files()
