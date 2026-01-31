import os
import time
import ipaddress
import pickle
import gzip
from collections import defaultdict
from pathlib import Path

try:
    import polars as pl
except ImportError:
    print("[ERROR] Errore: Polars non è installato")
    print("Installalo con: pip install polars")
    import sys
    sys .exit(1)


class PrecomputedNetwork:
    __slots__ = ['network_int', 'prefix_len', 'is_ipv4', 'row_data']

    def __init__(self, network_str, row_data):
        self .row_data = row_data
        network = ipaddress .ip_network(network_str, strict=False)
        self .network_int = int(network .network_address)
        self .prefix_len = network .prefixlen
        self .is_ipv4 = network .version == 4

    def contains_ip(self, ip_int, is_ipv4):
        if self .is_ipv4 != is_ipv4:
            return False
        if self .is_ipv4:
            mask = (0xFFFFFFFF << (32 - self .prefix_len)) & 0xFFFFFFFF
        else:
            mask = (0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF << (
                128 - self .prefix_len)) & 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF
        return (ip_int & mask) == self .network_int


class GeoDataManager:
    def __init__(self):
        self .filename = os .getenv('DATA_FILENAME', 'networks.csv')
        self .cache_version = os .getenv('CACHE_VERSION', '4.0')
        self .cache_filename = self ._get_cache_filename()
        self .ipv4_networks = []
        self .ipv6_networks = []
        self .ipv4_octet_ranges = {}
        self .ipv6_block_ranges = {}
        self .asn_cache = defaultdict(list)
        self .load_time = 0
        print("[INFO] GeoIP Data Manager - Avvio caricamento dati...")
        self .load_data()
        print(f"[INFO] Dati caricati in {self .load_time:.2f}s")

    def _get_cache_filename(self):
        csv_path = Path(self .filename)
        return csv_path .parent / \
            f"{csv_path .stem}_daemon_v{self .cache_version}.cache"

    def _get_csv_modification_time(self):
        try:
            return os .path .getmtime(self .filename)
        except FileNotFoundError:
            return 0

    def _get_cache_modification_time(self):
        try:
            return os .path .getmtime(self .cache_filename)
        except FileNotFoundError:
            return 0

    def _is_cache_valid(self):
        csv_time = self ._get_csv_modification_time()
        cache_time = self ._get_cache_modification_time()
        if not (cache_time > csv_time and cache_time > 0):
            return False
        try:
            with gzip .open(self .cache_filename, 'rb')as f:
                pass
            return True
        except Exception:
            return False

    def _create_optimized_structures(self):
        print("[INFO] Ottimizzazione strutture dati...")
        self .ipv4_networks .sort(
            key=lambda x: (
                x .network_int >> 24, x .network_int, -x .prefix_len))
        self .ipv6_networks .sort(
            key=lambda x: (
                x .network_int >> 112, x .network_int, -x .prefix_len))
        current_octet = None
        start_idx = 0
        for i, network in enumerate(self .ipv4_networks):
            octet = network .network_int >> 24
            if current_octet is None:
                current_octet = octet
                start_idx = i
            elif octet != current_octet:
                self .ipv4_octet_ranges[current_octet] = (start_idx, i)
                current_octet = octet
                start_idx = i
        if current_octet is not None:
            self .ipv4_octet_ranges[current_octet] = (
                start_idx, len(self .ipv4_networks))
        current_block = None
        start_idx = 0
        for i, network in enumerate(self .ipv6_networks):
            block = network .network_int >> 112
            if current_block is None:
                current_block = block
                start_idx = i
            elif block != current_block:
                self .ipv6_block_ranges[current_block] = (start_idx, i)
                current_block = block
                start_idx = i
        if current_block is not None:
            self .ipv6_block_ranges[current_block] = (
                start_idx, len(self .ipv6_networks))

    def _save_cache(self):
        print("[INFO] Salvando cache...")
        cache_data = {
            'ipv4_networks': self .ipv4_networks,
            'ipv6_networks': self .ipv6_networks,
            'ipv4_octet_ranges': self .ipv4_octet_ranges,
            'ipv6_block_ranges': self .ipv6_block_ranges,
            'asn_cache': dict(self .asn_cache),
            'csv_modification_time': self ._get_csv_modification_time(),
            'version': self .cache_version
        }
        try:
            with gzip .open(self .cache_filename, 'wb', compresslevel=6)as f:
                pickle .dump(cache_data, f, protocol=pickle .HIGHEST_PROTOCOL)
            print("[INFO] Cache salvato")
        except Exception as e:
            print(f"[ERROR] Errore salvataggio cache: {e}")

    def _load_cache(self):
        print("[INFO] Caricamento cache...")
        start_time = time .time()
        try:
            with gzip .open(self .cache_filename, 'rb')as f:
                cache_data = pickle .load(f)
            if cache_data .get('version') != self .cache_version:
                print(
                    f"[INFO] Cache obsoleto (versione corrente: {
                        self .cache_version}, versione cache: {
                        cache_data .get('version')}), rigenerazione...")
                return False
            self .ipv4_networks = cache_data['ipv4_networks']
            self .ipv6_networks = cache_data['ipv6_networks']
            self .ipv4_octet_ranges = cache_data['ipv4_octet_ranges']
            self .ipv6_block_ranges = cache_data['ipv6_block_ranges']
            self .asn_cache = defaultdict(list, cache_data['asn_cache'])
            self .load_time = time .time()-start_time
            total_networks = len(self .ipv4_networks)+len(self .ipv6_networks)
            print(
                f"[INFO] Cache caricato: {
                    total_networks:,} reti in {
                    self .load_time:.3f}s")
            return True
        except Exception as e:
            print(f"[ERROR] Errore caricamento cache: {e}")
            return False

    def load_data(self):
        start_time = time .time()
        if self ._is_cache_valid() and self ._load_cache():
            return
        print("[INFO] Caricamento CSV con Polars...")
        self ._load_csv_with_polars()
        self ._create_optimized_structures()
        self ._save_cache()
        self .load_time = time .time()-start_time

    def _load_csv_with_polars(self):
        try:
            print("[INFO] Lettura CSV...")
            df = pl .read_csv(
                self .filename,
                encoding='utf-8',
                ignore_errors=True,
                null_values=['', 'NULL', 'null', 'N/A', 'n/a'],
                truncate_ragged_lines=True,
                dtypes={
                    'network': pl .String, 'asn': pl .String,
                    'organization': pl .String, 'country': pl .String
                }
            )
            print("[INFO] Pulizia dati...")
            df = df .with_columns([
                pl .col('network').cast(pl .String).str .strip_chars(),
                pl .col('asn').cast(pl .String).str .strip_chars(),
                pl .col('organization').cast(pl .String).str .strip_chars(),
                pl .col('country').cast(pl .String).str .strip_chars()
            ])
            df = df .filter(
                pl .col('network').is_not_null() &
                pl .col('asn').is_not_null() &
                pl .col('organization').is_not_null() &
                pl .col('country').is_not_null()
            )
            print(f"[INFO] Processando {len(df):,} righe...")
            rows = df .to_dicts()
            ipv4_temp = []
            ipv6_temp = []
            for row in rows:
                try:
                    network_str = row['network']
                    cleaned_row = {
                        'network': network_str,
                        'asn': row['asn'],
                        'organization': row['organization'],
                        'country': row['country']
                    }
                    precomputed = PrecomputedNetwork(network_str, cleaned_row)
                    if precomputed .is_ipv4:
                        ipv4_temp .append(precomputed)
                    else:
                        ipv6_temp .append(precomputed)
                    self .asn_cache[row['asn']].append(cleaned_row)
                except (ValueError, KeyError, AttributeError):
                    continue
            self .ipv4_networks = ipv4_temp
            self .ipv6_networks = ipv6_temp
            total_networks = len(self .ipv4_networks)+len(self .ipv6_networks)
            print(f"[INFO] Processate {total_networks:,} reti")
        except Exception as e:
            print(f"[ERROR] Errore CSV: {e}")
            raise

    def get_networks(self, is_ipv4):
        return self .ipv4_networks if is_ipv4 else self .ipv6_networks

    def get_octet_ranges(self, is_ipv4):
        return self .ipv4_octet_ranges if is_ipv4 else self .ipv6_block_ranges

    def get_asn_cidrs_data(self, asn):
        return self .asn_cache .get(asn, [])

    def get_total_networks_count(self):
        return len(self .ipv4_networks)+len(self .ipv6_networks)

    def get_ipv4_networks_count(self):
        return len(self .ipv4_networks)

    def get_ipv6_networks_count(self):
        return len(self .ipv6_networks)

    def get_total_asn_count(self):
        return len(self .asn_cache)
