import socket
import select
import threading
import requests
from typing import List

class ProxyRotator:
    def __init__(self, port: int = 8080, proxy_file: str = "working_proxies.txt"):
        self.port = port
        self.proxy_file = proxy_file
        self.proxies = []
        self.current_index = 0
        self.running = False
        
    def load_proxies(self):
        try:
            with open(self.proxy_file, 'r') as f:
                self.proxies = [line.strip() for line in f if line.strip()]
            print(f"[+] Loaded {len(self.proxies)} proxies")
        except:
            print("[-] No proxy file found. Run --check first")
            self.proxies = []
    
    def get_next_proxy(self) -> str:
        if not self.proxies:
            return None
        proxy = self.proxies[self.current_index]
        self.current_index = (self.current_index + 1) % len(self.proxies)
        return proxy
    
    def handle_client(self, client_socket):
        """Forward client requests through rotating proxies"""
        proxy = self.get_next_proxy()
        if not proxy:
            client_socket.close()
            return
        
        print(f"[→] Using proxy: {proxy}")
        
        # Simple HTTP forwarder
        request = client_socket.recv(4096)
        if not request:
            client_socket.close()
            return
        
        try:
            # Parse host
            lines = request.decode('utf-8').split('\n')
            first_line = lines[0]
            url_part = first_line.split(' ')[1]
            
            if url_part.startswith('http://'):
                url_part = url_part[7:]
            
            host = url_part.split('/')[0].split(':')[0]
            port = 80
            
            # Forward through proxy
            proxy_parts = proxy.split(':')
            proxy_host = proxy_parts[0]
            proxy_port = int(proxy_parts[1])
            
            # Connect to proxy
            proxy_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            proxy_socket.connect((proxy_host, proxy_port))
            
            # Send original request
            proxy_socket.send(request)
            
            # Get response
            response = proxy_socket.recv(4096)
            client_socket.send(response)
            
            proxy_socket.close()
        except Exception as e:
            print(f"[-] Error: {e}")
        
        client_socket.close()
    
    def start(self):
        self.load_proxies()
        if not self.proxies:
            print("[-] No proxies available. Run --scrape and --check first")
            return
        
        self.running = True
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.bind(('0.0.0.0', self.port))
        server.listen(100)
        
        print(f"[+] Proxy rotator listening on 0.0.0.0:{self.port}")
        print(f"[+] Rotating through {len(self.proxies)} proxies")
        
        while self.running:
            client, addr = server.accept()
            print(f"[→] Connection from {addr}")
            threading.Thread(target=self.handle_client, args=(client,)).start()
    
    def stop(self):
        self.running = False
