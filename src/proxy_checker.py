import concurrent.futures
import requests
from typing import List, Tuple
import time

class ProxyChecker:
    def __init__(self, timeout: int = 5):
        self.timeout = timeout
        self.working = []
    
    def check_single(self, proxy: str, protocol: str = "http") -> Tuple[str, bool, float]:
        """Check if a single proxy works"""
        proxies = {
            "http": f"{protocol}://{proxy}",
            "https": f"{protocol}://{proxy}"
        }
        
        start = time.time()
        try:
            response = requests.get(
                "http://httpbin.org/ip",
                proxies=proxies,
                timeout=self.timeout
            )
            latency = time.time() - start
            if response.status_code == 200:
                return proxy, True, latency
        except:
            pass
        return proxy, False, 0
    
    def check_file(self, filename: str, protocol: str = "http", max_workers: int = 50) -> List[str]:
        """Check all proxies from a file"""
        with open(filename, 'r') as f:
            proxies = [line.strip() for line in f if line.strip()]
        
        working = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(self.check_single, proxy, protocol): proxy for proxy in proxies}
            
            for future in concurrent.futures.as_completed(futures):
                proxy, is_working, latency = future.result()
                if is_working:
                    print(f"[+] WORKING: {proxy} ({latency:.2f}s)")
                    working.append(proxy)
                else:
                    print(f"[-] DEAD: {proxy}")
        
        self.working = working
        return working
    
    def save_working(self, working: List[str], filename: str):
        with open(filename, 'w') as f:
            for proxy in working:
                f.write(f"{proxy}\n")
