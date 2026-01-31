from http .server import BaseHTTPRequestHandler, HTTPServer
import json
import ipaddress
import time
import urllib .parse
import threading
import os
from .geo_lookup_service import GeoLookupService


class GeoIPLookupHandler (BaseHTTPRequestHandler):
    def _send_response(self, status_code, content_type, data):
        self .send_response(status_code)
        self .send_header('Content-type', content_type)
        self .end_headers()
        if isinstance(data, str):
            self .wfile .write(data .encode('utf-8'))
        else:
            self .wfile .write(data)

    def do_GET(self):
        path = urllib .parse .unquote(self .path)
        ip_address = path .lstrip('/')
        if ip_address == 'favicon.ico':
            try:
                with open('static/favicon.ico', 'rb')as f:
                    self .send_response(200)
                    self .send_header('Content-type', 'image/x-icon')
                    self .end_headers()
                    self .wfile .write(f .read())
            except FileNotFoundError:
                self .send_response(404)
                self .end_headers()
            return
        if not ip_address:
            self ._send_response(400, 'application/json', json .dumps({
                'success': False,
                'error': 'Missing IP address. Usage: /<IP_ADDRESS>'
            }))
            return
        lookup_service = GeoLookupService()
        try:
            parsed_ip = ipaddress .ip_address(ip_address)
            ip_address_normalized = str(parsed_ip)
        except ValueError:
            self ._send_response(400, 'application/json', json .dumps({
                'success': False,
                'error': 'Invalid IP address format.'
            }))
            return
        start_time = time .time()
        matching_row = lookup_service .find_matching_cidr(
            ip_address_normalized)
        query_time = time .time()-start_time
        if matching_row:
            response_data = {
                "success": True,
                "ip": ip_address_normalized,
                "query_time_seconds": f"{query_time:.18f}",
                "result": {
                    "network": matching_row['network'],
                    "asn": matching_row['asn'],
                    "organization": matching_row['organization'],
                    "country": matching_row['country']
                }
            }
            asn_cidrs_list = lookup_service .get_asn_cidrs(matching_row['asn'])
            response_data['asn_cidrs_count'] = len(asn_cidrs_list)
            response_data['asn_cidrs'] = asn_cidrs_list
            self ._send_response(
                200,
                'application/json',
                json .dumps(
                    response_data,
                    indent=2))
        else:
            response_data = {
                'success': False,
                'ip': ip_address_normalized,
                'query_time_seconds': f"{query_time:.18f}",
                'error': f'IP {ip_address_normalized} not found.'
            }
            self ._send_response(
                404,
                'application/json',
                json .dumps(
                    response_data,
                    indent=2))


class GeoWebAPI:
    def __init__(self):
        self .server = None
        self .server_thread = None
        self .daemon_web_host = os .getenv('DAEMON_WEB_HOST', '0.0.0.0')
        self .daemon_web_port = int(os .getenv('DAEMON_WEB_PORT', 8888))

    def start(self):
        print(
            f"[INFO] Avvio Web API server su http://{
                self .daemon_web_host}:{
                self .daemon_web_port}")
        print(
            f"[INFO] Esempio d'uso http://{
                self .daemon_web_host}:{
                self .daemon_web_port}/216.58.205.46")
        server_address = (self .daemon_web_host, self .daemon_web_port)
        try:
            self .server = HTTPServer(server_address, GeoIPLookupHandler)
            self .server_thread = threading .Thread(
                target=self .server .serve_forever, daemon=True)
            self .server_thread .start()
        except OSError as e:
            print(
                f"[ERROR] Errore Web API server: {e} - Probabilmente la porta {
                    self .daemon_web_port} è già in uso.")
            raise
        except Exception as e:
            print(f"[ERROR] Errore generico Web API server: {e}")

    def stop(self):
        print("[INFO] Fermando Web API server...")
        if self .server:
            self .server .shutdown()
            if self .server_thread and self .server_thread .is_alive():
                self .server_thread .join(timeout=1)
        print("[INFO] Web API server fermato.")
