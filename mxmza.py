#!/usr/bin/env python3
"""
🔥 MxmzaPro - Proxy Swarm Tool
Complete proxy management suite
"""

import argparse
import sys
import threading
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()

def banner():
    banner_text = """
███╗   ███╗ ██╗  ██╗ ███╗   ███╗ ███████╗ ███████╗ ██████╗ 
████╗ ████║ ╚██╗██╔╝ ████╗ ████║ ██╔════╝ ██╔════╝ ██╔══██╗
██╔████╔██║  ╚███╔╝  ██╔████╔██║ █████╗   █████╗   ██████╔╝
██║╚██╔╝██║  ██╔██╗  ██║╚██╔╝██║ ██╔══╝   ██╔══╝   ██╔══██╗
██║ ╚═╝ ██║ ██╔╝ ██╗ ██║ ╚═╝ ██║ ██║      ███████╗ ██║  ██║
╚═╝     ╚═╝ ╚═╝  ╚═╝ ╚═╝     ╚═╝ ╚═╝      ╚══════╝ ╚═╝  ╚═╝
                                                     v2.0.0
    """
    console.print(Panel(banner_text, style="bold red", border_style="red"))
    console.print("[bold yellow]⚡ Complete Proxy Swarm Tool - SOCKS | Web UI | API[/bold yellow]\n")

def main():
    banner()
    
    parser = argparse.ArgumentParser(description="MxmzaPro - Advanced Proxy Suite")
    parser.add_argument("-s", "--scrape", action="store_true", help="Scrape fresh proxies")
    parser.add_argument("-c", "--check", metavar="FILE", help="Check proxies from file")
    parser.add_argument("-r", "--rotate", action="store_true", help="Start proxy rotator")
    parser.add_argument("--api", action="store_true", help="Start REST API server")
    parser.add_argument("--web", action="store_true", help="Start web dashboard")
    parser.add_argument("-p", "--port", type=int, default=8080, help="Local proxy port (default: 8080)")
    parser.add_argument("--api-port", type=int, default=8000, help="API server port (default: 8000)")
    parser.add_argument("--web-port", type=int, default=8081, help="Web UI port (default: 8081)")
    parser.add_argument("-o", "--output", default="proxies.txt", help="Output file")
    parser.add_argument("--limit", type=int, default=100, help="Max proxies to scrape")
    parser.add_argument("--protocol", choices=["http", "socks4", "socks5"], default="http", help="Proxy protocol")
    
    args = parser.parse_args()
    
    if args.api:
        console.print("[cyan]🚀 Starting REST API server...[/cyan]")
        from src.api_server import start_api
        console.print(f"[green]✅ API running on http://localhost:{args.api_port}[/green]")
        console.print("[yellow]📖 API docs available at /docs[/yellow]")
        start_api(port=args.api_port)
    
    elif args.web:
        console.print("[cyan]🌐 Starting web dashboard...[/cyan]")
        from web.app import start_web
        console.print(f"[green]✅ Web UI running on http://localhost:{args.web_port}[/green]")
        start_web(port=args.web_port)
    
    elif args.scrape:
        console.print("[cyan]🔍 Scraping fresh proxies...[/cyan]")
        from src.proxy_scraper import ProxyScraper
        scraper = ProxyScraper()
        proxies = scraper.scrape(limit=args.limit)
        scraper.save(proxies, args.output)
        console.print(f"[green]✅ Saved {len(proxies)} proxies to {args.output}[/green]")
    
    elif args.check:
        console.print(f"[cyan]🔍 Checking proxies from {args.check}...[/cyan]")
        from src.proxy_checker import ProxyChecker
        checker = ProxyChecker()
        working = checker.check_file(args.check, protocol=args.protocol)
        checker.save_working(working, f"working_{args.output}")
        console.print(f"[green]✅ Found {len(working)} working proxies[/green]")
    
    elif args.rotate:
        console.print(f"[cyan]🔄 Starting proxy rotator on localhost:{args.port}[/cyan]")
        from src.proxy_rotator import ProxyRotator
        rotator = ProxyRotator(port=args.port)
        rotator.start()
    
    else:
        # Show help menu
        table = Table(title="🔥 MxmzaPro Usage Examples", style="red")
        table.add_column("Mode", style="cyan")
        table.add_column("Command", style="green")
        table.add_row("CLI Scraper", "python mxmza.py --scrape --limit 200")
        table.add_row("CLI Checker", "python mxmza.py --check proxies.txt --protocol socks5")
        table.add_row("CLI Rotator", "python mxmza.py --rotate --port 8888")
        table.add_row("API Server", "python mxmza.py --api --api-port 8000")
        table.add_row("Web UI", "python mxmza.py --web --web-port 8081")
        console.print(table)
        
        console.print("\n[bold yellow]💡 Quick start with Web UI:[/bold yellow]")
        console.print("  1. python mxmza.py --web")
        console.print("  2. Open http://localhost:8081")
        console.print("  3. Use the dashboard to scrape, check, and rotate!\n")

if __name__ == "__main__":
    main()
