import os
import signal
import sys


def is_daemon_running():
    daemon_pidfile = os .getenv('DAEMON_PIDFILE', 'geo_daemon.pid')
    try:
        with open(daemon_pidfile, 'r')as f:
            pid = int(f .read().strip())
        os .kill(pid, 0)
        return True
    except (FileNotFoundError, OSError, ProcessLookupError):
        return False


def display_results(ip_address, result, asn_cidrs=None):
    print("="*60)
    print(f"🌐 ANALISI IP: {ip_address}")
    print("="*60)
    if result:
        print(f"📍 IP trovato nel CIDR: {result['network']}")
        print(f"🏢 ASN: {result['asn']}")
        print(f"🏛️  Organizzazione: {result['organization']}")
        print(f"🌍 Paese: {result['country']}")
        if asn_cidrs is not None:
            print(
                f"\n📋 TUTTI I CIDR PER ASN {
                    result['asn']}: {
                    len(asn_cidrs):,}")
            ipv4_count = sum(1 for c in asn_cidrs if ':'not in c)
            ipv6_count = len(asn_cidrs)-ipv4_count
            print(f"   🔢 IPv4: {ipv4_count:,} reti")
            print(f"   🔢 IPv6: {ipv6_count:,} reti")
            if asn_cidrs:
                print("\n📋 Elenco Completo CIDR:")
                for cidr_str in asn_cidrs:
                    print(f"   - {cidr_str}")
            else:
                print("   Nessun CIDR aggiuntivo trovato per questo ASN.")
    else:
        print(f"❌ IP {ip_address} non trovato")
