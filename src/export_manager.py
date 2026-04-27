import requests
import aiohttp
import asyncio
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from collections import defaultdict
import json
import time

@dataclass
class GeoInfo:
    ip: str
    country: str
    country_code: str
    city: str
    latitude: float
    longitude: float
    isp: str
    organization: str
    asn: str
    timezone: str
    proxy_type: str
    risk_score: int

class GeoLocator:
    """Geolocation for proxies with multiple data sources"""
    
    def __init__(self, use_local_db: bool = False, db_path: str = "data/GeoLite2-Country.mmdb"):
        self.cache = {}
        self.use_local_db = use_local_db
        self.db_path = db_path
        
        # Try to load local GeoIP database
        if use_local_db:
            try:
                import geoip2.database
                self.reader = geoip2.database.Reader(db_path)
            except:
                print("[-] Local GeoIP database not found, using online APIs")
                self.use_local_db = False
    
    async def get_geo_info_async(self, ip: str) -> Optional[GeoInfo]:
        """Get geolocation info asynchronously"""
        if ip in self.cache:
            return self.cache[ip]
        
        # Try multiple APIs with fallback
        apis = [
            f"http://ip-api.com/json/{ip}",
            f"https://ipinfo.io/{ip}/json",
            f"http://freegeoip.app/json/{ip}"
        ]
        
        for api in apis:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(api, timeout=5) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            info = self._parse_geo_data(data, ip)
                            if info:
                                self.cache[ip] = info
                                return info
            except:
                continue
        
        return None
    
    def get_geo_info(self, ip: str) -> Optional[GeoInfo]:
        """Get geolocation info synchronously"""
        if self.use_local_db and hasattr(self, 'reader'):
            try:
                response = self.reader.country(ip)
                return GeoInfo(
                    ip=ip,
                    country=response.country.name,
                    country_code=response.country.iso_code,
                    city="Unknown",
                    latitude=0,
                    longitude=0,
                    isp="Unknown",
                    organization="Unknown",
                    asn="Unknown",
                    timezone="UTC",
                    proxy_type="Unknown",
                    risk_score=0
                )
            except:
                pass
        
        # Use async version synchronously
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(self.get_geo_info_async(ip))
        loop.close()
        return result
    
    def _parse_geo_data(self, data: Dict, ip: str) -> Optional[GeoInfo]:
        """Parse different API responses"""
        try:
            if 'country' in data:  # ip-api.com format
                return GeoInfo(
                    ip=ip,
                    country=data.get('country', 'Unknown'),
                    country_code=data.get('countryCode', 'XX'),
                    city=data.get('city', 'Unknown'),
                    latitude=data.get('lat', 0),
                    longitude=data.get('lon', 0),
                    isp=data.get('isp', 'Unknown'),
                    organization=data.get('org', 'Unknown'),
                    asn=data.get('as', 'Unknown'),
                    timezone=data.get('timezone', 'UTC'),
                    proxy_type=data.get('proxy', 'Unknown'),
                    risk_score=data.get('risk', 0)
                )
            elif 'loc' in data:  # ipinfo.io format
                loc = data.get('loc', '0,0').split(',')
                return GeoInfo(
                    ip=ip,
                    country=data.get('country', 'Unknown'),
                    country_code=data.get('country', 'XX')[:2],
                    city=data.get('city', 'Unknown'),
                    latitude=float(loc[0]) if len(loc) > 0 else 0,
                    longitude=float(loc[1]) if len(loc) > 1 else 0,
                    isp=data.get('org', 'Unknown'),
                    organization=data.get('org', 'Unknown'),
                    asn=data.get('asn', 'Unknown'),
                    timezone=data.get('timezone', 'UTC'),
                    proxy_type='Public' if 'proxy' in data else 'Residential',
                    risk_score=50 if 'proxy' in data else 0
                )
        except:
            return None
        return None
    
    async def get_multiple_geo(self, ips: List[str]) -> Dict[str, GeoInfo]:
        """Get geolocation for multiple IPs concurrently"""
        tasks = [self.get_geo_info_async(ip) for ip in ips]
        results = await asyncio.gather(*tasks)
        return {ips[i]: results[i] for i in range(len(ips)) if results[i]}
    
    def filter_by_country(self, proxies: List[str], countries: List[str]) -> List[str]:
        """Filter proxies by country codes"""
        filtered = []
        for proxy in proxies:
            ip = proxy.split(':')[0]
            geo = self.get_geo_info(ip)
            if geo and geo.country_code in countries:
                filtered.append(proxy)
        return filtered
    
    def filter_by_continent(self, proxies: List[str], continents: List[str]) -> List[str]:
        """Filter proxies by continent"""
        continent_map = {
            'AF': 'Africa', 'AN': 'Antarctica', 'AS': 'Asia', 
            'EU': 'Europe', 'NA': 'North America', 'OC': 'Oceania', 
            'SA': 'South America'
        }
        
        filtered = []
        for proxy in proxies:
            ip = proxy.split(':')[0]
            geo = self.get_geo_info(ip)
            if geo:
                for continent_code in continents:
                    if continent_map.get(continent_code) == geo.country:
                        filtered.append(proxy)
                        break
        return filtered
    
    def get_proxy_distribution(self, proxies: List[str]) -> Dict:
        """Get geographical distribution of proxies"""
        distribution = defaultdict(int)
        
        for proxy in proxies:
            ip = proxy.split(':')[0]
            geo = self.get_geo_info(ip)
            if geo:
                distribution[geo.country] += 1
        
        return dict(distribution)
    
    def generate_heatmap_data(self, proxies: List[str]) -> List[Dict]:
        """Generate data for geographical heatmap"""
        heatmap_data = []
        
        for proxy in proxies:
            ip = proxy.split(':')[0]
            geo = self.get_geo_info(ip)
            if geo and geo.latitude != 0:
                heatmap_data.append({
                    'lat': geo.latitude,
                    'lon': geo.longitude,
                    'ip': ip,
                    'country': geo.country
                })
        
        return heatmap_data
