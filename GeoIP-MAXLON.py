from core.geo_web_api import GeoWebAPI
from core.geo_lookup_service import GeoLookupService
from core.db_updater import DBUpdater
import os
import signal
import sys
import threading
import time
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()


def signal_handler(signum, frame) -> None:
    print(f"\n[INFO] Ricevuto segnale {signum}. Shutdown in corso...")
    sys.exit(0)


def main() -> None:
    """Avvia il Web API server per GeoIP lookup."""
    print("[INFO] Avvio GeoIP-MAXLON Web API (Docker mode)")

    try:
        lookup_service = GeoLookupService()
        print("[INFO] Database caricato in memoria")
    except FileNotFoundError:
        print("[ERROR] File 'networks.csv' non trovato. Tentativo di aggiornamento...")
        updater = DBUpdater()
        if updater.update_database():
            print("[INFO] Aggiornamento database completato. Caricamento in memoria...")
            try:
                lookup_service = GeoLookupService()
            except FileNotFoundError:
                print("[ERROR] Impossibile caricare il database anche dopo l'aggiornamento.")
                sys.exit(1)
        else:
            print("[ERROR] Aggiornamento database fallito.")
            sys.exit(1)

    web_api = GeoWebAPI()

    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    web_api_thread = threading.Thread(target=web_api.start, daemon=True)
    web_api_thread.start()

    print("\n[INFO] Web API in esecuzione. Premi Ctrl+C per fermare.")
    try:
        while web_api_thread.is_alive():
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[INFO] Shutdown richiesto...")
    finally:
        print("[INFO] Arresto Web API...")
        web_api.stop()
        print("[INFO] Arresto completato.")


if __name__ == "__main__":
    main()
