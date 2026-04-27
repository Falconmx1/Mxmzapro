import random
import time
import threading
from typing import List, Dict, Optional, Callable
from collections import defaultdict
from datetime import datetime, timedelta
import heapq

class ProxyLoadBalancer:
    """Advanced load balancer for proxy rotation with multiple algorithms"""
    
    ALGORITHMS = ['round_robin', 'least_connections', 'fastest_response', 'weighted', 'random', 'adaptive']
    
    def __init__(self, algorithm: str = 'adaptive'):
        self.algorithm = algorithm
        self.proxies: List[Dict] = []
        self.current_index = 0
        self.connections: Dict[str, int] = defaultdict(int)
        self.response_times: Dict[str, List[float]] = defaultdict(list)
        self.failures: Dict[str, int] = defaultdict(int)
        self.weights: Dict[str, int] = defaultdict(lambda: 1)
        self.lock = threading.Lock()
        self.stats = {
            'total_requests': 0,
            'failed_requests': 0,
            'avg_response_time': 0
        }
        
    def add_proxy(self, proxy: str, weight: int = 1, protocol: str = 'http'):
        """Add a proxy to the load balancer"""
        with self.lock:
            self.proxies.append({
                'address': proxy,
                'weight': weight,
                'protocol': protocol,
                'failures': 0,
                'successes': 0
            })
            self.weights[proxy] = weight
    
    def remove_proxy(self, proxy: str):
        """Remove a proxy from rotation"""
        with self.lock:
            self.proxies = [p for p in self.proxies if p['address'] != proxy]
            if proxy in self.connections:
                del self.connections[proxy]
            if proxy in self.response_times:
                del self.response_times[proxy]
    
    def update_response_time(self, proxy: str, response_time: float):
        """Track response time for adaptive balancing"""
        with self.lock:
            self.response_times[proxy].append(response_time)
            # Keep last 10 response times
            if len(self.response_times[proxy]) > 10:
                self.response_times[proxy].pop(0)
            
            # Update weight based on response time (inverse relationship)
            avg_time = sum(self.response_times[proxy]) / len(self.response_times[proxy])
            if avg_time > 0:
                self.weights[proxy] = max(1, int(1000 / avg_time))
    
    def record_failure(self, proxy: str):
        """Record a proxy failure"""
        with self.lock:
            self.failures[proxy] += 1
            self.stats['failed_requests'] += 1
            
            # Reduce weight on failures
            self.weights[proxy] = max(1, self.weights[proxy] - 5)
            
            # Auto-remove after 5 consecutive failures
            if self.failures[proxy] >= 5:
                self.remove_proxy(proxy)
    
    def record_success(self, proxy: str):
        """Record a successful request"""
        with self.lock:
            self.failures[proxy] = 0
            self.stats['total_requests'] += 1
            
            # Gradually increase weight on success
            if self.weights[proxy] < 100:
                self.weights[proxy] += 1
    
    def get_next_proxy(self) -> Optional[str]:
        """Get next proxy based on selected algorithm"""
        with self.lock:
            if not self.proxies:
                return None
            
            if self.algorithm == 'round_robin':
                return self._round_robin()
            elif self.algorithm == 'least_connections':
                return self._least_connections()
            elif self.algorithm == 'fastest_response':
                return self._fastest_response()
            elif self.algorithm == 'weighted':
                return self._weighted()
            elif self.algorithm == 'random':
                return self._random()
            else:  # adaptive
                return self._adaptive()
    
    def _round_robin(self) -> str:
        """Simple round-robin rotation"""
        proxy = self.proxies[self.current_index]['address']
        self.current_index = (self.current_index + 1) % len(self.proxies)
        return proxy
    
    def _least_connections(self) -> str:
        """Pick proxy with fewest active connections"""
        best_proxy = min(self.proxies, key=lambda p: self.connections.get(p['address'], 0))
        self.connections[best_proxy['address']] += 1
        return best_proxy['address']
    
    def _fastest_response(self) -> str:
        """Pick proxy with best average response time"""
        def get_avg_time(proxy):
            times = self.response_times.get(proxy['address'], [1000])
            return sum(times) / len(times)
        
        best_proxy = min(self.proxies, key=get_avg_time)
        return best_proxy['address']
    
    def _weighted(self) -> str:
        """Weighted round-robin based on assigned weights"""
        total_weight = sum(p['weight'] for p in self.proxies)
        if total_weight == 0:
            return self.proxies[0]['address']
        
        random_point = random.randint(1, total_weight)
        cumulative = 0
        for proxy in self.proxies:
            cumulative += proxy['weight']
            if cumulative >= random_point:
                return proxy['address']
        return self.proxies[0]['address']
    
    def _random(self) -> str:
        """Random selection"""
        return random.choice(self.proxies)['address']
    
    def _adaptive(self) -> str:
        """Adaptive algorithm combining speed, success rate, and load"""
        scores = []
        for proxy in self.proxies:
            addr = proxy['address']
            
            # Speed score (lower response time = higher score)
            avg_time = sum(self.response_times.get(addr, [500])) / max(1, len(self.response_times.get(addr, [1])))
            speed_score = max(0, min(100, 5000 / avg_time))
            
            # Success rate score
            total = proxy['successes'] + proxy['failures']
            success_rate = (proxy['successes'] / max(1, total)) * 100
            
            # Connection load score
            load_score = max(0, 100 - (self.connections.get(addr, 0) * 10))
            
            # Weight score
            weight_score = self.weights.get(addr, 1)
            
            # Combined score
            total_score = (speed_score * 0.4) + (success_rate * 0.3) + (load_score * 0.2) + (weight_score * 0.1)
            scores.append((total_score, addr))
        
        if not scores:
            return None
        
        scores.sort(reverse=True)
        return scores[0][1]
    
    def release_connection(self, proxy: str):
        """Release a connection (for least_connections algorithm)"""
        with self.lock:
            if proxy in self.connections and self.connections[proxy] > 0:
                self.connections[proxy] -= 1
    
    def get_stats(self) -> Dict:
        """Get load balancer statistics"""
        with self.lock:
            return {
                'total_proxies': len(self.proxies),
                'algorithm': self.algorithm,
                'total_requests': self.stats['total_requests'],
                'failed_requests': self.stats['failed_requests'],
                'success_rate': (self.stats['total_requests'] - self.stats['failed_requests']) / max(1, self.stats['total_requests']) * 100,
                'proxies': [
                    {
                        'address': p['address'],
                        'weight': self.weights.get(p['address'], 1),
                        'connections': self.connections.get(p['address'], 0),
                        'failures': self.failures.get(p['address'], 0),
                        'avg_response': sum(self.response_times.get(p['address'], [0])) / max(1, len(self.response_times.get(p['address'], [1])))
                    }
                    for p in self.proxies
                ]
            }
    
    def set_algorithm(self, algorithm: str):
        """Change load balancing algorithm on the fly"""
        if algorithm in self.ALGORITHMS:
            self.algorithm = algorithm
            return True
        return False


class SmartProxyBalancer(ProxyLoadBalancer):
    """Extended load balancer with health checks and auto-scaling"""
    
    def __init__(self, algorithm: str = 'adaptive', health_check_interval: int = 60):
        super().__init__(algorithm)
        self.health_check_interval = health_check_interval
        self.health_check_thread = None
        self.running = False
    
    def start_health_checks(self):
        """Start background health check thread"""
        self.running = True
        self.health_check_thread = threading.Thread(target=self._health_check_loop, daemon=True)
        self.health_check_thread.start()
    
    def _health_check_loop(self):
        """Periodically check proxy health"""
        while self.running:
            time.sleep(self.health_check_interval)
            self._check_all_proxies()
    
    def _check_all_proxies(self):
        """Check health of all proxies"""
        import aiohttp
        import asyncio
        
        async def check_proxy(proxy_info):
            proxy = proxy_info['address']
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get('http://httpbin.org/ip', proxy=f'http://{proxy}', timeout=5) as resp:
                        if resp.status == 200:
                            self.record_success(proxy)
                            return True
            except:
                self.record_failure(proxy)
            return False
        
        # Run async checks
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        tasks = [check_proxy(p) for p in self.proxies]
        loop.run_until_complete(asyncio.gather(*tasks))
        loop.close()
    
    def stop(self):
        """Stop health checker"""
        self.running = False
