"""
Test-Client für AutoGraph REST API

Demonstriert die Verwendung der REST API Endpunkte
"""

import asyncio
import json
import time
from pathlib import Path
import aiohttp
import aiofiles


class AutoGraphAPIClient:
    """Client für AutoGraph REST API"""

    def __init__(self, base_url: str = "http://127.0.0.1:8000"):
        self.base_url = base_url
        self.session = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def health_check(self):
        """Überprüft ob API erreichbar ist"""
        async with self.session.get(f"{self.base_url}/health") as response:
            return await response.json()

    async def process_text(
        self, text: str, domain: str = None, mode: str = "both", use_cache: bool = True
    ):
        """Verarbeitet Text über API"""
        data = {"text": text, "mode": mode, "use_cache": use_cache}
        if domain:
            data["domain"] = domain

        async with self.session.post(
            f"{self.base_url}/process/text", json=data
        ) as response:
            if response.status == 200:
                return await response.json()
            else:
                error = await response.text()
                raise Exception(f"API Error {response.status}: {error}")

    async def process_table(
        self,
        file_path: str,
        domain: str = None,
        processing_mode: str = "combined",
        max_rows: int = 1000,
    ):
        """Verarbeitet Tabellendatei über API"""
        data = aiohttp.FormData()

        # Datei hinzufügen
        async with aiofiles.open(file_path, "rb") as f:
            file_content = await f.read()
            data.add_field("file", file_content, filename=Path(file_path).name)

        # Parameter hinzufügen
        if domain:
            data.add_field("domain", domain)
        data.add_field("processing_mode", processing_mode)
        data.add_field("max_rows", str(max_rows))
        data.add_field("use_cache", "true")

        async with self.session.post(
            f"{self.base_url}/process/table", data=data
        ) as response:
            if response.status == 200:
                return await response.json()
            else:
                error = await response.text()
                raise Exception(f"API Error {response.status}: {error}")

    async def process_batch(
        self,
        file_paths: list,
        domain: str = None,
        mode: str = "both",
        max_concurrent: int = 3,
    ):
        """Startet Batch-Verarbeitung"""
        data = aiohttp.FormData()

        # Dateien hinzufügen
        for file_path in file_paths:
            async with aiofiles.open(file_path, "rb") as f:
                file_content = await f.read()
                data.add_field("files", file_content, filename=Path(file_path).name)

        # Parameter hinzufügen
        if domain:
            data.add_field("domain", domain)
        data.add_field("mode", mode)
        data.add_field("max_concurrent", str(max_concurrent))
        data.add_field("use_cache", "true")

        async with self.session.post(
            f"{self.base_url}/process/batch", data=data
        ) as response:
            if response.status == 200:
                return await response.json()
            else:
                error = await response.text()
                raise Exception(f"API Error {response.status}: {error}")

    async def get_task_status(self, task_id: str):
        """Holt Task-Status"""
        async with self.session.get(f"{self.base_url}/tasks/{task_id}") as response:
            if response.status == 200:
                return await response.json()
            else:
                error = await response.text()
                raise Exception(f"API Error {response.status}: {error}")

    async def list_tasks(self, status: str = None, limit: int = 50):
        """Listet Tasks auf"""
        params = {"limit": limit}
        if status:
            params["status"] = status

        async with self.session.get(
            f"{self.base_url}/tasks", params=params
        ) as response:
            if response.status == 200:
                return await response.json()
            else:
                error = await response.text()
                raise Exception(f"API Error {response.status}: {error}")

    async def get_cache_stats(self):
        """Holt Cache-Statistiken"""
        async with self.session.get(f"{self.base_url}/cache/stats") as response:
            if response.status == 200:
                return await response.json()
            else:
                error = await response.text()
                raise Exception(f"API Error {response.status}: {error}")

    async def clear_cache(self):
        """Leert alle Caches"""
        async with self.session.delete(f"{self.base_url}/cache") as response:
            if response.status == 200:
                return await response.json()
            else:
                error = await response.text()
                raise Exception(f"API Error {response.status}: {error}")

    async def get_pipeline_status(self):
        """Holt Pipeline-Status"""
        async with self.session.get(f"{self.base_url}/pipeline/status") as response:
            if response.status == 200:
                return await response.json()
            else:
                error = await response.text()
                raise Exception(f"API Error {response.status}: {error}")


async def test_api_endpoints():
    """Testet alle API Endpunkte"""

    print("🧪 Teste AutoGraph REST API")
    print("=" * 50)

    async with AutoGraphAPIClient() as client:
        try:
            # 1. Health Check
            print("🔍 Health Check...")
            health = await client.health_check()
            print(f"   Status: {health['status']}")

            # 2. Pipeline Status
            print("\n🔧 Pipeline Status...")
            pipeline_status = await client.get_pipeline_status()
            print(f"   Status: {pipeline_status['status']}")
            print(
                f"   Processors: {', '.join(pipeline_status['config']['processors'])}"
            )

            # 3. Text Processing
            print("\n📄 Text-Verarbeitung...")
            test_text = "Max Mustermann arbeitet bei Microsoft in Berlin. Anna Schmidt leitet das Projekt bei Google."

            start_time = time.time()
            result = await client.process_text(
                text=test_text, domain="wirtschaft", mode="both"
            )
            processing_time = time.time() - start_time

            print(f"   Verarbeitungszeit: {processing_time:.2f}s")
            print(f"   Entitäten: {len(result['entities'])}")
            print(f"   Beziehungen: {len(result['relationships'])}")
            print(f"   Cache verwendet: {result['cache_used']}")

            if result["entities"]:
                print("   Beispiel-Entitäten:")
                for entity in result["entities"][:3]:
                    print(
                        f"     • {entity.get('text', 'N/A')} ({entity.get('label', 'N/A')})"
                    )

            # 4. Gleicher Text nochmal (Cache-Test)
            print("\n🎯 Cache-Test (gleicher Text)...")
            start_time = time.time()
            result2 = await client.process_text(
                text=test_text, domain="wirtschaft", mode="both"
            )
            cache_time = time.time() - start_time

            print(f"   Verarbeitungszeit: {cache_time:.2f}s")
            print(f"   Speedup: {processing_time / cache_time:.1f}x")

            # 5. Tabellen-Verarbeitung (falls test_data.csv existiert)
            if Path("test_data.csv").exists():
                print("\n📊 Tabellen-Verarbeitung...")
                table_result = await client.process_table(
                    file_path="test_data.csv",
                    domain="wirtschaft",
                    processing_mode="combined",
                )
                print(f"   Entitäten: {len(table_result['entities'])}")
                print(f"   Beziehungen: {len(table_result['relationships'])}")
                print(f"   Verarbeitungszeit: {table_result['processing_time']:.2f}s")

            # 6. Cache-Statistiken
            print("\n📊 Cache-Statistiken...")
            cache_stats = await client.get_cache_stats()
            print(f"   Gesamt Einträge: {cache_stats['total_entries']}")
            print(f"   NER Hit-Rate: {cache_stats['hit_rates']['ner']:.1%}")
            print(f"   Relations Hit-Rate: {cache_stats['hit_rates']['relations']:.1%}")

            # 7. Tasks auflisten
            print("\n📋 Tasks...")
            tasks = await client.list_tasks(limit=5)
            print(f"   Aktuelle Tasks: {len(tasks['tasks'])}")

            # 8. Batch-Verarbeitung (falls mehrere Dateien vorhanden)
            test_files = list(Path(".").glob("test_*.csv"))
            if len(test_files) > 1:
                print(f"\n📚 Batch-Verarbeitung ({len(test_files)} Dateien)...")
                batch_response = await client.process_batch(
                    file_paths=[str(f) for f in test_files[:2]],  # Nur erste 2
                    domain="wirtschaft",
                    max_concurrent=2,
                )
                print(f"   Task ID: {batch_response['task_id']}")
                print(f"   Status: {batch_response['status']}")

                # Task-Status verfolgen
                task_id = batch_response["task_id"]
                for i in range(10):  # Max 10 Versuche
                    await asyncio.sleep(1)
                    task_status = await client.get_task_status(task_id)
                    print(
                        f"   Status: {task_status['status']}, Fortschritt: {task_status['progress']:.1%}"
                    )

                    if task_status["status"] in ["completed", "failed"]:
                        break

                if task_status["status"] == "completed" and task_status["result"]:
                    print(
                        f"   Batch-Ergebnis: {task_status['result']['entities']} Entitäten"
                    )

            print("\n✅ API-Tests abgeschlossen!")

        except Exception as e:
            print(f"\n❌ API-Test Fehler: {e}")
            raise


async def demo_interactive_api():
    """Interaktive API-Demo"""

    print("\n🎮 Interaktive API-Demo")
    print("=" * 30)

    async with AutoGraphAPIClient() as client:
        while True:
            print("\nVerfügbare Aktionen:")
            print("1. Text verarbeiten")
            print("2. Cache-Statistiken")
            print("3. Pipeline-Status")
            print("4. Cache leeren")
            print("0. Beenden")

            try:
                choice = input("\nIhre Wahl: ")

                if choice == "0":
                    break
                elif choice == "1":
                    text = input("Text eingeben: ")
                    domain = input("Domäne (optional): ") or None

                    result = await client.process_text(text, domain=domain)
                    print(f"\n✅ Ergebnis:")
                    print(f"   Entitäten: {len(result['entities'])}")
                    print(f"   Beziehungen: {len(result['relationships'])}")
                    print(f"   Zeit: {result['processing_time']:.2f}s")

                elif choice == "2":
                    stats = await client.get_cache_stats()
                    print(f"\n📊 Cache-Statistiken:")
                    print(f"   Gesamt: {stats['total_entries']} Einträge")
                    print(f"   NER Hit-Rate: {stats['hit_rates']['ner']:.1%}")
                    print(
                        f"   Relations Hit-Rate: {stats['hit_rates']['relations']:.1%}"
                    )

                elif choice == "3":
                    status = await client.get_pipeline_status()
                    print(f"\n🔧 Pipeline-Status:")
                    print(f"   Status: {status['status']}")
                    print(f"   Processors: {', '.join(status['config']['processors'])}")

                elif choice == "4":
                    await client.clear_cache()
                    print("\n🗑️ Cache geleert")

            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"\n❌ Fehler: {e}")


async def main():
    """Hauptfunktion"""
    print("🚀 AutoGraph API Client")
    print("=" * 50)

    # Überprüfe ob Server läuft
    try:
        async with AutoGraphAPIClient() as client:
            await client.health_check()
            print("✅ API Server erreichbar")
    except Exception as e:
        print("❌ API Server nicht erreichbar!")
        print("   Starte den Server mit: uv run python -m autograph.cli serve")
        return

    # Wähle Test-Modus
    print("\nTest-Modi:")
    print("1. Automatische Tests")
    print("2. Interaktive Demo")

    choice = input("Wahl (1/2): ")

    if choice == "1":
        await test_api_endpoints()
    elif choice == "2":
        await demo_interactive_api()
    else:
        print("Ungültige Wahl")


if __name__ == "__main__":
    # Install aiohttp falls nicht vorhanden
    try:
        import aiohttp
        import aiofiles
    except ImportError:
        print("❌ Fehlende Dependencies. Installiere mit:")
        print("   uv add aiohttp aiofiles")
        exit(1)

    asyncio.run(main())
