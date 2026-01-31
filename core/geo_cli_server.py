import socket
import json
import threading
import time
import os
from .geo_lookup_service import GeoLookupService


class GeoCliServer:
    def __init__(self, lookup_service: GeoLookupService):
        self .lookup_service = lookup_service
        self .server_socket = None
        self .running = False
        self .daemon_host = os .getenv('DAEMON_HOST', '127.0.0.1')
        self .daemon_port = int(os .getenv('DAEMON_PORT', 8888))

    def start(self):
        print(
            f"[INFO] Avvio server CLI su {
                self .daemon_host}:{
                self .daemon_port}")
        self .server_socket = socket .socket(
            socket .AF_INET, socket .SOCK_STREAM)
        self .server_socket .setsockopt(
            socket .SOL_SOCKET, socket .SO_REUSEADDR, 1)
        try:
            self .server_socket .bind((self .daemon_host, self .daemon_port))
            self .server_socket .listen(5)
            self .running = True
            while self .running:
                try:
                    client_socket, addr = self .server_socket .accept()
                    threading .Thread(
                        target=self ._handle_client, args=(
                            client_socket,), daemon=True).start()
                except Exception as e:
                    if self .running:
                        print(f"[ERROR] Errore server CLI: {e}")
        except OSError as e:
            print(
                f"[ERROR] Errore avvio server CLI: {e} - Probabilmente la porta {
                    self .daemon_port} è già in uso.")
            raise
        except Exception as e:
            print(f"[ERROR] Errore generico server CLI: {e}")
        finally:
            if self .server_socket:
                self .server_socket .close()

    def _handle_client(self, client_socket):
        try:
            data = client_socket .recv(1024).decode('utf-8')
            request = json .loads(data)
            if request['action'] == 'lookup':
                ip_address = request['ip']
                start_time = time .time()
                matching_row = self .lookup_service .find_matching_cidr(
                    ip_address)
                query_time = time .time()-start_time

                response = {
                    'success': True,
                    'ip': ip_address,
                    'result': matching_row,
                    'query_time_seconds': f"{query_time:.18f}"
                }
                if matching_row:
                    response['asn_cidrs'] = self .lookup_service .get_asn_cidrs(
                        matching_row['asn'])
            elif request['action'] == 'stats':
                response = self .lookup_service .get_stats()
            else:
                response = {'success': False, 'error': 'Unknown action'}
            client_socket .send(json .dumps(response).encode('utf-8'))
        except Exception as e:
            error_response = {'success': False, 'error': str(e)}
            client_socket .send(json .dumps(error_response).encode('utf-8'))
        finally:
            client_socket .close()

    def stop(self):
        print("[INFO] Fermando server CLI...")
        self .running = False
        if self .server_socket:
            self .server_socket .close()
        print("[INFO] Server CLI fermato.")
