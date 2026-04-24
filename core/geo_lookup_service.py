import ipaddress
import time
import threading
import bisect
from .geo_data_manager import GeoDataManager


class GeoLookupService:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(GeoLookupService, cls).__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if not self._initialized:
            self.data_manager = GeoDataManager()
            self.total_queries = 0
            self.start_time = time.time()
            self._initialized = True

    def find_matching_cidr(self, ip_address):
        self.total_queries += 1
        try:
            target_ip = ipaddress.ip_address(ip_address)
            ip_int = int(target_ip)
            is_ipv4 = target_ip.version == 4
        except ValueError:
            return None
        networks = self.data_manager.get_networks(is_ipv4)
        ranges = self.data_manager.get_octet_ranges(is_ipv4)
        start_idx, end_idx = (None, None)
        if is_ipv4:
            octet = ip_int >> 24
            start_idx, end_idx = ranges.get(octet, (None, None))
        else:
            block = ip_int >> 112
            start_idx, end_idx = ranges.get(block, (None, None))
        if start_idx is None or start_idx >= end_idx:
            return None
        best_match = None
        best_prefix = -1
        idx = bisect.bisect_right(
            networks, ip_int, lo=start_idx, hi=end_idx, key=lambda x: x.network_int
        )
        for i in range(idx - 1, start_idx - 1, -1):
            network = networks[i]
            if network.contains_ip(ip_int, is_ipv4):
                if network.prefix_len > best_prefix:
                    best_match = network.row_data
                    best_prefix = network.prefix_len
            else:
                pass
        return best_match

    def get_asn_cidrs(self, asn):
        full_data = self.data_manager.get_asn_cidrs_data(asn)
        return [item["network"] for item in full_data]

    def get_stats(self):
        uptime = time.time() - self.start_time
        return {
            "status": "running",
            "uptime": uptime,
            "total_networks": self.data_manager.get_total_networks_count(),
            "ipv4_networks": self.data_manager.get_ipv4_networks_count(),
            "ipv6_networks": self.data_manager.get_ipv6_networks_count(),
            "total_asn": self.data_manager.get_total_asn_count(),
            "total_queries": self.total_queries,
            "queries_per_second": self.total_queries / uptime if uptime > 0 else 0,
            "load_time": self.data_manager.load_time,
        }
