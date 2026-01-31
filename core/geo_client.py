import socket
import json
import os


def send_query(ip_address):
    daemon_host = os .getenv('DAEMON_HOST', '127.0.0.1')
    daemon_port = int(os .getenv('DAEMON_PORT', 8888))
    try:
        sock = socket .socket(socket .AF_INET, socket .SOCK_STREAM)
        sock .settimeout(5)
        sock .connect((daemon_host, daemon_port))
        request = {'action': 'lookup', 'ip': ip_address}
        sock .send(json .dumps(request).encode('utf-8'))
        response = sock .recv(8192 * 4).decode('utf-8')
        sock .close()
        return json .loads(response)
    except Exception as e:
        return {
            'success': False,
            'error': f'Errore connessione daemon CLI: {e}'}


def get_daemon_stats():
    daemon_host = os .getenv('DAEMON_HOST', '127.0.0.1')
    daemon_port = int(os .getenv('DAEMON_PORT', 8888))
    try:
        sock = socket .socket(socket .AF_INET, socket .SOCK_STREAM)
        sock .settimeout(5)
        sock .connect((daemon_host, daemon_port))

        request = {'action': 'stats'}
        sock .send(json .dumps(request).encode('utf-8'))

        response = sock .recv(4096).decode('utf-8')
        sock .close()
        return json .loads(response)
    except Exception as e:
        return {
            'success': False,
            'error': f'Errore connessione daemon CLI: {e}'}
