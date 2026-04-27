import asyncio
import socks
import socket
import aiohttp
from aiohttp_socks import ProxyConnector
from typing import Optional, Tuple
import struct

class SocksSupport:
    """Full SOCKS4/SOCKS5 support"""
    
    @staticmethod
    async def create_connector(proxy: str, proxy_type: str = 'socks5'):
        """Create aiohttp connector with SOCKS support"""
        proxy_type_map = {
            'socks4': aiohttp_socks.ProxyType.SOCKS4,
            'socks5': aiohttp_socks.ProxyType.SOCKS5
        }
        
        proxy_parts = proxy.split(':')
        proxy_host = proxy_parts[0]
        proxy_port = int(proxy_parts[1]) if len(proxy_parts) > 1 else 1080
        
        connector = ProxyConnector(
            proxy_type=proxy_type_map.get(proxy_type, aiohttp_socks.ProxyType.SOCKS5),
            host=proxy_host,
            port=proxy_port,
            rdns=True
        )
        return connector
    
    @staticmethod
    def socks_connect(proxy: str, target_host: str, target_port: int, proxy_type: str = 'socks5') -> Optional[socket.socket]:
        """Connect through SOCKS proxy"""
        try:
            s = socks.socksocket()
            proxy_parts = proxy.split(':')
            proxy_host = proxy_parts[0]
            proxy_port = int(proxy_parts[1]) if len(proxy_parts) > 1 else 1080
            
            # Set proxy type
            if proxy_type == 'socks4':
                s.set_proxy(socks.SOCKS4, proxy_host, proxy_port)
            else:
                s.set_proxy(socks.SOCKS5, proxy_host, proxy_port)
            
            s.connect((target_host, target_port))
            return s
        except Exception as e:
            print(f"[-] SOCKS connection failed: {e}")
            return None
    
    @staticmethod
    async def test_socks(proxy: str, proxy_type: str = 'socks5') -> dict:
        """Test if SOCKS proxy is working"""
        result = {
            'proxy': proxy,
            'type': proxy_type,
            'working': False,
            'latency': 0,
            'country': 'Unknown',
            'anon_level': 'Unknown'
        }
        
        try:
            import time
            start = time.time()
            
            connector = await SocksSupport.create_connector(proxy, proxy_type)
            async with aiohttp.ClientSession(connector=connector) as session:
                async with session.get('http://httpbin.org/ip', timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    if resp.status == 200:
                        result['working'] = True
                        result['latency'] = round((time.time() - start) * 1000, 2)
                        
                        # Get IP info
                        ip_data = await resp.json()
                        result['external_ip'] = ip_data.get('origin', 'Unknown')
            await connector.close()
        except Exception as e:
            result['error'] = str(e)
        
        return result

class SocksRotator:
    """Rotate through SOCKS proxies"""
    
    def __init__(self):
        self.proxies = []
        self.current = 0
    
    def add_proxy(self, proxy: str, proxy_type: str = 'socks5'):
        self.proxies.append({'address': proxy, 'type': proxy_type})
    
    def get_next(self) -> dict:
        if not self.proxies:
            return None
        proxy = self.proxies[self.current]
        self.current = (self.current + 1) % len(self.proxies)
        return proxy
    
    async def request(self, url: str) -> bytes:
        """Make request through rotating SOCKS proxies"""
        proxy = self.get_next()
        if not proxy:
            raise Exception("No proxies available")
        
        connector = await SocksSupport.create_connector(proxy['address'], proxy['type'])
        async with aiohttp.ClientSession(connector=connector) as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                return await resp.read()
