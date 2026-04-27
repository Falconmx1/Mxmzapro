# 🔥 MxmzaPro - Proxy Swarm Tool

[![License: MIT](https://img.shields.io/badge/License-MIT-red.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://python.org)

## ⚡ Features
- 🌐 Multi-protocol (HTTP/HTTPS/SOCKS4/SOCKS5)
- 🔄 Auto-proxy rotation
- 🕵️ Proxy scraper from 4+ sources
- ✅ Proxy validator with latency check
- 🔗 Proxy chaining support
- 🪟 Windows & 🐧 Linux compatible
- ⚡ Async & multi-threaded

## 📦 Installation

```bash
git clone https://github.com/Falconmx1/Mxmzapro.git
cd Mxmzapro
pip install -r requirements.txt

🚀 Usage
Scrape fresh proxies:
bash

python mxmza.py --scrape --limit 100

Check working proxies:
bash

python mxmza.py --check proxies.txt --protocol http

Start proxy rotator:
bash

python mxmza.py --rotate --port 8080

🎯 Complete workflow:
bash

# 1. Get proxies
python mxmza.py --scrape --limit 200 -o raw.txt

# 2. Verify them
python mxmza.py --check raw.txt --protocol http -o working.txt

# 3. Start rotating
python mxmza.py --rotate --port 8888
