#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import signal
import sys
import threading
import time
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

from core.db_updater import DBUpdater
from core.geo_cli_server import GeoCliServer
from core.geo_client import get_daemon_stats, send_query
from core.geo_lookup_service import GeoLookupService
from core.geo_utils import display_results, is_daemon_running
from core.geo_web_api import GeoWebAPI

DAEMON_PIDFILE = os.getenv('DAEMON_PIDFILE', 'geo_daemon.pid')


def main() -> None:
    if len(sys.argv) < 2:
        sys.argv.append('--server')

    elif sys.argv[1] in ['--help', '-h']:
        print("🚀 GeoIP-MAXLON - Cache in RAM per query istantanee")
        print("\nUso:")
        print("   python GeoIP-MAXLON.py                    🔥 Avvia daemon (resta in background e abilita Web API)")
        print("   python GeoIP-MAXLON.py <IP>               ⚡ Query istantanea (usa daemon CLI)")
        print("   python GeoIP-MAXLON.py --standalone <IP>  🔧 Modalità standalone (non usa il daemon, caricamento dati al avvio modalità più lenta)")
        print("   python GeoIP-MAXLON.py --status           📊 Stato daemon")
        print("   python GeoIP-MAXLON.py --stop             🛑 Ferma daemon")
        print("   python GeoIP-MAXLON.py --dbupdate         🔄 Aggiorna il file networks.csv e la cache")
        print("   python GeoIP-MAXLON.py -h/--help          ℹ️  Ottieni info sul uso del programma")
        print("\nEsempi:")
        print("   python GeoIP-MAXLON.py")
        print("   python GeoIP-MAXLON.py 8.8.8.8")
        print("   curl http://<il-tuo-ip>:<porta-servizio>/8.8.8.8")
        print("\n💡 Il daemon carica tutto in RAM una volta e risponde istantaneamente!")
        sys.exit(0)

    command: str = sys.argv[1]

    if command == '--server':
        if is_daemon_running():
            print("⚠️  Daemon già in esecuzione!")
            sys.exit(1)
        try:
            lookup_service = GeoLookupService()
        except FileNotFoundError:
            print("❌ File 'networks.csv' non trovato. Tentativo di aggiornamento del database...")
            updater = DBUpdater()
            if updater.update_database():
                print("✨ Aggiornamento database completato. Riprovo ad avviare il daemon.")
                try:
                    lookup_service = GeoLookupService()
                except FileNotFoundError:
                    print("❌ Impossibile caricare il database anche dopo l'aggiornamento. Uscita.")
                    sys.exit(1)
            else:
                print("❌ Aggiornamento database fallito. Impossibile avviare il daemon.")
                sys.exit(1)

        cli_server = GeoCliServer(lookup_service)
        web_api = GeoWebAPI()

        Path(DAEMON_PIDFILE).parent.mkdir(parents=True, exist_ok=True)
        try:
            with open(DAEMON_PIDFILE, 'w', encoding='utf-8') as f:
                f.write(str(os.getpid()))
            print(f"✅ Daemon PID: {os.getpid()}")
        except IOError as e:
            print(f"❌ Errore nella scrittura del file PID: {e}")
            sys.exit(1)

        cli_thread = threading.Thread(target=cli_server.start, daemon=True)
        web_api_thread = threading.Thread(target=web_api.start, daemon=True)

        cli_thread.start()
        web_api_thread.start()

        print("\nDaemon in esecuzione. Premi Ctrl+C per fermare.")
        try:
            while cli_thread.is_alive() or web_api_thread.is_alive():
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n🛑 Shutdown richiesto...")
        finally:
            print("Inizializzazione spegnimento...")
            cli_server.stop()
            web_api.stop()
            try:
                os.remove(DAEMON_PIDFILE)
            except OSError as e:
                print(f"⚠️  Impossibile rimuovere il file PID: {e}")
            print("🛑 Daemon completamente spento.")

    elif command == '--status':
        if not is_daemon_running():
            print("❌ Daemon non in esecuzione")
            sys.exit(1)

        stats = get_daemon_stats()
        if stats.get('success', True):
            print("✅ Daemon Status:")
            print(f"   🔄 Uptime: {stats.get('uptime', 0.0):.1f}s")
            print(f"   📊 Reti totali: {stats.get('total_networks', 0):,}")
            print(f"   🔢 IPv4: {stats.get('ipv4_networks', 0):,}")
            print(f"   🔢 IPv6: {stats.get('ipv6_networks', 0):,}")
            print(f"   🏢 ASN: {stats.get('total_asn', 0):,}")
            print(f"   🔍 Query totali: {stats.get('total_queries', 0):,}")
            print(f"   ⚡ Query/sec: {stats.get('queries_per_second', 0.0):.1f}")
            print(f"   ⏱️  Tempo caricamento: {stats.get('load_time', 0.0):.2f}s")
        else:
            print(f"❌ Errore: {stats.get('error', 'Errore sconosciuto')}")

    elif command == '--stop':
        if not is_daemon_running():
            print("❌ Daemon non in esecuzione")
            sys.exit(1)

        try:
            with open(DAEMON_PIDFILE, 'r', encoding='utf-8') as f:
                pid = int(f.read().strip())
            os.kill(pid, signal.SIGTERM)
            print("🛑 Daemon fermato.")
        except (IOError, ValueError) as e:
            print(f"❌ Errore nella lettura o parsing del PID file: {e}")
        except ProcessLookupError:
            print("❌ Il processo del daemon non è stato trovato. Potrebbe essere già terminato.")
        except Exception as e:
            print(f"❌ Errore fermando daemon: {e}")

    elif command == '--dbupdate':
        if is_daemon_running():
            print("⚠️  Il daemon è in esecuzione. Si consiglia di fermarlo prima di aggiornare il DB.")
            print("   Per favor, ferma il daemon con 'python GeoIP-MAXLON.py --stop' e riprova.")
            sys.exit(1)

        updater = DBUpdater()
        if updater.update_database():
            print("✨ Aggiornamento database completato. Riavvia il daemon per caricare i nuovi dati.")
        else:
            print("❌ Aggiornamento database fallito.")

    elif command == '--standalone':
        if len(sys.argv) < 3:
            print("❌ Specifica IP per modalità standalone")
            sys.exit(1)

        ip_address: str = sys.argv[2]
        try:
            lookup_service = GeoLookupService()
        except FileNotFoundError:
            print("❌ File 'networks.csv' non trovato. Tentativo di aggiornamento del database...")
            updater = DBUpdater()
            if updater.update_database():
                print("✨ Aggiornamento database completato. Riprovo a caricare il database.")
                try:
                    lookup_service = GeoLookupService()
                except FileNotFoundError:
                    print("❌ Impossibile caricare il database anche dopo l'aggiornamento. Uscita.")
                    sys.exit(1)
            else:
                print("❌ Aggiornamento database fallito. Impossibile procedere in modalità standalone.")
                sys.exit(1)

        start_time = time.time()
        matching_row = lookup_service.find_matching_cidr(ip_address)
        query_time = time.time() - start_time

        asn_cidrs = []
        if matching_row:
            asn_cidrs = lookup_service.get_asn_cidrs(matching_row['asn'])

        display_results(ip_address, matching_row, asn_cidrs)
        print(f"\n⚡ Tempo query: {query_time:.4f}s")

    else:
        ip_address: str = command
        if not is_daemon_running():
            print("❌ Daemon non in esecuzione!")
            print("💡 Avvia con: python GeoIP-MAXLON.py --server")
            sys.exit(1)

        start_time = time.time()
        response = send_query(ip_address)
        total_time = time.time() - start_time

        if response.get('success'):
            matching_row = response.get('result')
            asn_cidrs = response.get('asn_cidrs', [])

            display_results(ip_address, matching_row, asn_cidrs)
            print(f"\n⚡ Tempo query (daemon): {response.get('query_time', 0.0):.4f}s")
            print(f"🌐 Tempo totale (client + daemon): {total_time:.4f}s")
        else:
            print(f"❌ Errore: {response.get('error', 'Errore sconosciuto')}")


if __name__ == "__main__":
    main()