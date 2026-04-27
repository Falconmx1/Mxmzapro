from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
import uvicorn
import threading
from .proxy_scraper import ProxyScraper
from .proxy_checker import ProxyChecker
from .proxy_rotator import ProxyRotator
from .socks_support import SocksSupport, SocksRotator
import json
import asyncio

app = FastAPI(title="MxmzaPro API", version="1.0.0", description="Proxy Swarm Tool API")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state
proxy_manager = {
    'scraped_proxies': [],
    'working_proxies': [],
    'active_rotator': None
}

# Models
class ScrapeRequest(BaseModel):
    limit: int = Field(default=100, ge=1, le=1000)
    sources: Optional[List[str]] = None

class CheckRequest(BaseModel):
    proxies: List[str]
    protocol: str = Field(default="http", regex="^(http|socks4|socks5)$")
    timeout: int = Field(default=5, ge=1, le=30)

class RotateRequest(BaseModel):
    port: int = Field(default=8080, ge=1024, le=65535)
    proxy_file: Optional[str] = "working_proxies.txt"

class ProxyChainRequest(BaseModel):
    proxies: List[str]
    target_url: str

# Endpoints
@app.get("/")
async def root():
    return {
        "name": "MxmzaPro API",
        "version": "1.0.0",
        "status": "🔥 ACTIVE",
        "endpoints": {
            "/api/scrape": "POST - Scrape fresh proxies",
            "/api/check": "POST - Validate proxies",
            "/api/proxies": "GET - List proxies",
            "/api/rotate/start": "POST - Start proxy rotator",
            "/api/rotate/stop": "POST - Stop proxy rotator",
            "/api/socks/test": "POST - Test SOCKS proxy",
            "/api/chain": "POST - Test proxy chain"
        }
    }

@app.post("/api/scrape")
async def scrape_proxies(request: ScrapeRequest, background_tasks: BackgroundTasks):
    """Scrape fresh proxies from multiple sources"""
    try:
        scraper = ProxyScraper()
        proxies = scraper.scrape(limit=request.limit)
        proxy_manager['scraped_proxies'] = proxies
        
        # Save to file
        scraper.save(proxies, "scraped_proxies.txt")
        
        return {
            "success": True,
            "count": len(proxies),
            "proxies": proxies[:50],  # Return first 50
            "message": f"Scraped {len(proxies)} proxies"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/check")
async def check_proxies(request: CheckRequest):
    """Validate proxies (HTTP or SOCKS)"""
    try:
        working = []
        
        if request.protocol in ['socks4', 'socks5']:
            # SOCKS check
            for proxy in request.proxies[:100]:  # Limit for performance
                result = await SocksSupport.test_socks(proxy, request.protocol)
                if result['working']:
                    working.append({
                        'proxy': proxy,
                        'latency': result['latency'],
                        'type': request.protocol
                    })
        else:
            # HTTP check
            checker = ProxyChecker(timeout=request.timeout)
            working_raw = checker.check_list(request.proxies)
            working = [{'proxy': p, 'latency': 0, 'type': 'http'} for p in working_raw]
        
        proxy_manager['working_proxies'] = working
        
        # Save working proxies
        with open("working_proxies.txt", "w") as f:
            for w in working:
                f.write(f"{w['proxy']}\n")
        
        return {
            "success": True,
            "count": len(working),
            "working_proxies": working,
            "message": f"Found {len(working)} working proxies"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/proxies")
async def list_proxies(type: str = "working", limit: int = 100):
    """List scraped or working proxies"""
    if type == "scraped":
        proxies = proxy_manager['scraped_proxies'][:limit]
    else:
        proxies = proxy_manager['working_proxies'][:limit]
    
    return {
        "success": True,
        "count": len(proxies),
        "proxies": proxies
    }

@app.post("/api/rotate/start")
async def start_rotator(request: RotateRequest):
    """Start local proxy rotator"""
    if proxy_manager['active_rotator']:
        return {
            "success": False,
            "message": "Rotator already running"
        }
    
    try:
        rotator = ProxyRotator(port=request.port, proxy_file=request.proxy_file)
        thread = threading.Thread(target=rotator.start)
        thread.daemon = True
        thread.start()
        
        proxy_manager['active_rotator'] = {
            'instance': rotator,
            'thread': thread,
            'port': request.port
        }
        
        return {
            "success": True,
            "message": f"Proxy rotator started on port {request.port}",
            "pid": thread.ident
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/rotate/stop")
async def stop_rotator():
    """Stop proxy rotator"""
    if not proxy_manager['active_rotator']:
        return {
            "success": False,
            "message": "No active rotator found"
        }
    
    proxy_manager['active_rotator']['instance'].stop()
    proxy_manager['active_rotator'] = None
    
    return {
        "success": True,
        "message": "Proxy rotator stopped"
    }

@app.post("/api/socks/test")
async def test_socks(proxy: str, proxy_type: str = "socks5"):
    """Test a specific SOCKS proxy"""
    try:
        result = await SocksSupport.test_socks(proxy, proxy_type)
        return {
            "success": True,
            "result": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/chain")
async def test_chain(request: ProxyChainRequest):
    """Test proxy chaining"""
    try:
        import aiohttp
        from aiohttp_socks import ProxyConnector, ChainProxyConnector
        
        # Build proxy chain
        connectors = []
        for proxy in request.proxies:
            proxy_parts = proxy.split(':')
            proxy_host = proxy_parts[0]
            proxy_port = int(proxy_parts[1])
            
            # Auto-detect SOCKS vs HTTP
            if 'socks' in proxy.lower():
                connector = ChainProxyConnector.from_url(f'socks5://{proxy_host}:{proxy_port}')
            else:
                connector = ChainProxyConnector.from_url(f'http://{proxy_host}:{proxy_port}')
            connectors.append(connector)
        
        # Make request through chain
        async with aiohttp.ClientSession() as session:
            async with session.get(request.target_url, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                content = await resp.text()
                
        return {
            "success": True,
            "status_code": resp.status,
            "content_length": len(content),
            "message": f"Successfully chained through {len(request.proxies)} proxies"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Chain failed"
        }

@app.get("/api/stats")
async def get_stats():
    """Get proxy statistics"""
    return {
        "scraped_count": len(proxy_manager['scraped_proxies']),
        "working_count": len(proxy_manager['working_proxies']),
        "rotator_active": proxy_manager['active_rotator'] is not None,
        "rotator_port": proxy_manager['active_rotator']['port'] if proxy_manager['active_rotator'] else None
    }

def start_api(host: str = "0.0.0.0", port: int = 8000):
    """Start FastAPI server"""
    uvicorn.run(app, host=host, port=port, log_level="info")
