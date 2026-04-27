import asyncio
import aiohttp
from bs4 import BeautifulSoup
from typing import List
import re

class ProxyScraper:
    SOURCES = [
        "https://free-proxy-list.net/",
        "https://www.sslproxies.org/",
        "https://www.us-proxy.org/",
        "https://socks-proxy.net/",
    ]
    
    def __init__(self):
        self.proxies = []
    
    def scrape(self, limit: int = 100) -> List[str]:
        """Scrape proxies from multiple sources"""
        import requests
        
        for url in self.SOURCES:
            try:
                response = requests.get(url, timeout=10)
                soup = BeautifulSoup(response.text, 'html.parser')
                table = soup.find('table')
                
                if table:
                    rows = table.find_all('tr')[1:]
                    for row in rows:
                        if len(self.proxies) >= limit:
                            break
                        cols = row.find_all('td')
                        if len(cols) >= 2:
                            ip = cols[0].text.strip()
                            port = cols[1].text.strip()
                            proxy = f"{ip}:{port}"
                            if proxy not in self.proxies:
                                self.proxies.append(proxy)
                print(f"[+] Scraped {len(self.proxies)} proxies from {url}")
            except Exception as e:
                print(f"[-] Failed {url}: {e}")
        
        return self.proxies
    
    def save(self, proxies: List[str], filename: str):
        with open(filename, 'w') as f:
            for proxy in proxies:
                f.write(f"{proxy}\n")
