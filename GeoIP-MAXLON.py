

from core .geo_utils import display_results, is_daemon_running
from core .geo_client import get_daemon_stats, send_query
from core .geo_web_api import GeoWebAPI
from core .geo_lookup_service import GeoLookupService
from core .geo_cli_server import GeoCliServer
from core .db_updater import DBUpdater
import os
import signal
import sys
import threading
import time
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()


DAEMON_PIDFILE = os .getenv('DAEMON_PIDFILE', 'geo_daemon.pid')


def cleanup_pidfile() -> None:
    try:
        if os .path .exists(DAEMON_PIDFILE):
            os .remove(DAEMON_PIDFILE)
            print("[INFO] File PID rimosso.")
    except OSError as e:
        print(f"[WARNING] Impossibile rimuovere il file PID: {e}")


def signal_handler(signum, frame) -> None:
    print(f"\n[INFO] Ricevuto segnale {signum}. Shutdown in corso...")
    cleanup_pidfile()
    sys .exit(0)


def is_process_running(pid: int) -> bool:
    try:

        os .kill(pid, 0)
        return True
    except OSError:
        return False


def validate_pidfile() -> bool:

    if not os .path .exists(DAEMON_PIDFILE):
        return False

    try:
        with open(DAEMON_PIDFILE, 'r', encoding='utf-8')as f:
            pid = int(f .read().strip())

        if is_process_running(pid):
            return True
        else:

            print(
                f"[WARNING] Trovato PID file stantio (processo {pid} non esiste). Rimozione...")
            try:
                os .remove(DAEMON_PIDFILE)
            except OSError as e:
                print(
                    f"[WARNING] Impossibile rimuovere il PID file stantio: {e}")
            return False
    except (IOError, ValueError)as e:
        print(f"[WARNING] PID file corrotto: {e}. Rimozione...")
        try:
            os .remove(DAEMON_PIDFILE)
        except OSError:
            pass
        return False


def main() -> None:
    if len(sys .argv) < 2:
        sys .argv .append('--server')

    elif sys .argv[1] in ['--help', '-h']:
        print("GeoIP-MAXLON - Cache in RAM per query istantanee")
        print("\nUso:")
        print("   python GeoIP-MAXLON.py                    Avvia daemon (resta in background e abilita Web API)")
        print(
            "   python GeoIP-MAXLON.py <IP>               Query istantanea (usa daemon CLI)")
        print("   python GeoIP-MAXLON.py --standalone <IP>  Modalità standalone (non usa il daemon, caricamento dati al avvio modalità più lenta)")
        print("   python GeoIP-MAXLON.py --status           Stato daemon")
        print("   python GeoIP-MAXLON.py --stop             Ferma daemon")
        print("   python GeoIP-MAXLON.py --dbupdate         Aggiorna il file networks.csv e la cache")
        print("   python GeoIP-MAXLON.py -h/--help          Ottieni info sul uso del programma")
        print("\nEsempi:")
        print("   python GeoIP-MAXLON.py")
        print("   python GeoIP-MAXLON.py 8.8.8.8")
        print("   curl http://<il-tuo-ip>:" +
              str(os .getenv('DAEMON_WEB_PORT', 8888))+"/8.8.8.8")
        print("\nIl daemon carica tutto in RAM una volta e risponde istantaneamente!")
        sys .exit(0)

    command: str = sys .argv[1]

    if command == '--server':
        if validate_pidfile():
            print("[WARNING] Daemon già in esecuzione!")
            sys .exit(1)
        try:
            lookup_service = GeoLookupService()
        except FileNotFoundError:
            print(
                "[ERROR] File 'networks.csv' non trovato. Tentativo di aggiornamento del database...")
            updater = DBUpdater()
            if updater .update_database():
                print(
                    "[INFO] Aggiornamento database completato. Riprovo ad avviare il daemon.")
                try:
                    lookup_service = GeoLookupService()
                except FileNotFoundError:
                    print(
                        "[ERROR] Impossibile caricare il database anche dopo l'aggiornamento. Uscita.")
                    sys .exit(1)
            else:
                print(
                    "[ERROR] Aggiornamento database fallito. Impossibile avviare il daemon.")
                sys .exit(1)

        cli_server = GeoCliServer(lookup_service)
        web_api = GeoWebAPI()

        Path(DAEMON_PIDFILE).parent .mkdir(parents=True, exist_ok=True)
        try:
            with open(DAEMON_PIDFILE, 'w', encoding='utf-8')as f:
                f .write(str(os .getpid()))
            print(f"[INFO] Daemon PID: {os .getpid()}")
        except IOError as e:
            print(f"[ERROR] Errore nella scrittura del file PID: {e}")
            sys .exit(1)

        signal .signal(signal .SIGTERM, signal_handler)
        signal .signal(signal .SIGINT, signal_handler)

        cli_thread = threading .Thread(target=cli_server .start, daemon=True)
        web_api_thread = threading .Thread(target=web_api .start, daemon=True)

        cli_thread .start()
        web_api_thread .start()

        print("\n[INFO] Daemon in esecuzione. Premi Ctrl+C per fermare.")
        try:
            while cli_thread .is_alive() or web_api_thread .is_alive():
                time .sleep(1)
        except KeyboardInterrupt:
            print("\n[INFO] Shutdown richiesto...")
        finally:
            print("[INFO] Inizializzazione spegnimento...")
            cli_server .stop()
            web_api .stop()
            cleanup_pidfile()
            print("[INFO] Daemon completamente spento.")

    elif command == '--status':
        if not validate_pidfile():
            print("[ERROR] Daemon non in esecuzione")
            sys .exit(1)

        stats = get_daemon_stats()
        if stats .get('success', True):
            print("[INFO] Daemon Status:")
            print(f"   Uptime: {stats .get('uptime', 0.0):.1f}s")
            print(f"   Reti totali: {stats .get('total_networks', 0):,}")
            print(f"   IPv4: {stats .get('ipv4_networks', 0):,}")
            print(f"   IPv6: {stats .get('ipv6_networks', 0):,}")
            print(f"   ASN: {stats .get('total_asn', 0):,}")
            print(f"   Query totali: {stats .get('total_queries', 0):,}")
            print(f"   Query/sec: {stats .get('queries_per_second', 0.0):.1f}")
            print(f"   Tempo caricamento: {stats .get('load_time', 0.0):.2f}s")
        else:
            print(
                f"[ERROR] Errore: {
                    stats .get(
                        'error',
                        'Errore sconosciuto')}")

    elif command == '--stop':
        if not validate_pidfile():
            print("[ERROR] Daemon non in esecuzione")
            sys .exit(1)

        try:
            with open(DAEMON_PIDFILE, 'r', encoding='utf-8')as f:
                pid = int(f .read().strip())
            os .kill(pid, signal .SIGTERM)
            print("[INFO] Daemon fermato.")
        except (IOError, ValueError)as e:
            print(f"[ERROR] Errore nella lettura o parsing del PID file: {e}")
        except ProcessLookupError:
            print(
                "[ERROR] Il processo del daemon non è stato trovato. Potrebbe essere già terminato.")
        except Exception as e:
            print(f"[ERROR] Errore fermando daemon: {e}")

    elif command == '--dbupdate':
        if validate_pidfile():
            print(
                "[WARNING] Il daemon è in esecuzione. Si consiglia di fermarlo prima di aggiornare il DB.")
            print(
                "   Per favore, ferma il daemon con 'python GeoIP-MAXLON.py --stop' e riprova.")
            sys .exit(1)

        updater = DBUpdater()
        if updater .update_database():
            print(
                "[INFO] Aggiornamento database completato. Riavvia il daemon per caricare i nuovi dati.")
        else:
            print("[ERROR] Aggiornamento database fallito.")

    elif command == '--standalone':
        if len(sys .argv) < 3:
            print("[ERROR] Specifica IP per modalità standalone")
            sys .exit(1)

        ip_address: str = sys .argv[2]
        try:
            lookup_service = GeoLookupService()
        except FileNotFoundError:
            print(
                "[ERROR] File 'networks.csv' non trovato. Tentativo di aggiornamento del database...")
            updater = DBUpdater()
            if updater .update_database():
                print(
                    "[INFO] Aggiornamento database completato. Riprovo a caricare il database.")
                try:
                    lookup_service = GeoLookupService()
                except FileNotFoundError:
                    print(
                        "[ERROR] Impossibile caricare il database anche dopo l'aggiornamento. Uscita.")
                    sys .exit(1)
            else:
                print(
                    "[ERROR] Aggiornamento database fallito. Impossibile procedere in modalità standalone.")
                sys .exit(1)

        start_time = time .time()
        matching_row = lookup_service .find_matching_cidr(ip_address)
        query_time = time .time()-start_time

        asn_cidrs = []
        if matching_row:
            asn_cidrs = lookup_service .get_asn_cidrs(matching_row['asn'])

        display_results(ip_address, matching_row, asn_cidrs)
        print(f"\nTempo query: {query_time:.4f}s")

    else:
        ip_address: str = command
        if not validate_pidfile():
            print("[ERROR] Daemon non in esecuzione!")
            print("Avvia con: python GeoIP-MAXLON.py --server")
            sys .exit(1)

        start_time = time .time()
        response = send_query(ip_address)
        total_time = time .time()-start_time

        if response .get('success'):
            matching_row = response .get('result')
            asn_cidrs = response .get('asn_cidrs', [])

            display_results(ip_address, matching_row, asn_cidrs)
            print(
                f"\nTempo query (daemon): {
                    response .get(
                        'query_time',
                        0.0):.4f}s")
            print(f"Tempo totale (client + daemon): {total_time:.4f}s")
        else:
            print(
                f"[ERROR] Errore: {
                    response .get(
                        'error',
                        'Errore sconosciuto')}")


if __name__ == "__main__":
    main()
