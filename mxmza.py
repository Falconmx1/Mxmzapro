#!/usr/bin/env python3
"""
🔥 MxmzaPro - Proxy Swarm Tool
Multi-protocol proxy rotator + scraper + validator
"""

import argparse
import sys
import os
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from src.proxy_scraper import ProxyScraper
from src.proxy_checker import ProxyChecker
from src.proxy_rotator import ProxyRotator

console = Console()

def banner():
    banner_text = """
███╗   ███╗ ██╗  ██╗ ███╗   ███╗ ███████╗ ███████╗ ██████╗ 
████╗ ████║ ╚██╗██╔╝ ████╗ ████║ ██╔════╝ ██╔════╝ ██╔══██╗
██╔████╔██║  ╚███╔╝  ██╔████╔██║ █████╗   █████╗   ██████╔╝
██║╚██╔╝██║  ██╔██╗  ██║╚██╔╝██║ ██╔══╝   ██╔══╝   ██╔══██╗
██║ ╚═╝ ██║ ██╔╝ ██╗ ██║ ╚═╝ ██║ ██║      ███████╗ ██║  ██║
╚═╝     ╚═╝ ╚═╝  ╚═╝ ╚═╝     ╚═╝ ╚═╝      ╚══════╝ ╚═╝  ╚═╝
                                                     v1.0.0
    """
    console.print(Panel(banner_text, style="bold red", border_style="red"))
    console.print("[bold yellow]⚡ Proxy Swarm Tool - Windows/Linux Ready[/bold yellow]\n")

def main():
    banner()
    
    parser = argparse.ArgumentParser(description="MxmzaPro - Advanced Proxy Tool")
    parser.add_argument("-s", "--scrape", action="store_true", help="Scrape fresh proxies")
    parser.add_argument("-c", "--check", metavar="FILE", help="Check proxies from file")
    parser.add_argument("-r", "--rotate", action="store_true", help="Start proxy rotator")
    parser.add_argument("-p", "--port", type=int, default=8080, help="Local proxy port (default: 8080)")
    parser.add_argument("-o", "--output", default="proxies.txt", help="Output file")
    parser.add_argument("--limit", type=int, default=100, help="Max proxies to scrape")
    parser.add_argument("--protocol", choices=["http", "socks4", "socks5"], default="http", help="Proxy protocol")
    
    args = parser.parse_args()
    
    if args.scrape:
        console.print("[cyan]🔍 Scraping fresh proxies...[/cyan]")
        scraper = ProxyScraper()
        proxies = scraper.scrape(limit=args.limit)
        scraper.save(proxies, args.output)
        console.print(f"[green]✅ Saved {len(proxies)} proxies to {args.output}[/green]")
    
    elif args.check:
        console.print(f"[cyan]🔍 Checking proxies from {args.check}...[/cyan]")
        checker = ProxyChecker()
        working = checker.check_file(args.check, protocol=args.protocol)
        checker.save_working(working, f"working_{args.output}")
        console.print(f"[green]✅ Found {len(working)} working proxies[/green]")
    
    elif args.rotate:
        console.print(f"[cyan]🔄 Starting proxy rotator on localhost:{args.port}[/cyan]")
        rotator = ProxyRotator(port=args.port)
        rotator.start()
    
    else:
        console.print("[yellow]💡 Usage examples:[/yellow]")
        console.print("  python mxmza.py --scrape --limit 50")
        console.print("  python mxmza.py --check proxies.txt --protocol http")
        console.print("  python mxmza.py --rotate --port 8888")

if __name__ == "__main__":
    main()
