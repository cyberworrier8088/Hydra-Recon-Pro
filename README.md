# 🐍 Hydra Recon Pro: V1

**Advanced Web Reconnaissance & OSINT Automation Framework for Red Teams, Bug Bounty Hunters, and Offensive Security Operators**  

---

## ⚔️ Overview  

**Hydra Recon Pro** is a modular, Python-powered web reconnaissance and OSINT automation suite designed for **real-world offensive security operations**. Whether you're part of an APT group, Red Team, Bug Bounty program, or a curious hacker, this tool equips you to map, fingerprint, and analyze your target's online footprint with **speed, stealth, and precision**.  

This isn't a toy—it's crafted for professionals who understand that effective reconnaissance forms the foundation of successful exploitation.  

---

## 🛠️ Key Features  

✔ **Passive Reconnaissance:** WHOIS, Subdomains, Reverse IP Lookups  
✔ **Automated Extraction:** `robots.txt` & `sitemap.xml` Retrieval  
✔ **Directory & File Bruteforce:** Parallel or Sequential (User-Selectable)  
✔ **Hidden Parameter Discovery:** Input Enumeration & Fuzzing with Payloads  
✔ **Deep Recursive Crawler:** Link Mapping, Asset Discovery, Sensitive Data Harvesting  
✔ **Technology Fingerprinting:** CMS, Servers, Frameworks Detection  
✔ **Sensitive Data Harvesting:** Emails, Phone Numbers, Secrets Detection  
✔ **Stealth Recon:** Proxy Support for Anonymized Scanning  
✔ **Clean JSON Report Generation:** Structured, Actionable Intelligence  

---

## 🧩 Technical Stack  

- `requests` — HTTP Interactions  
- `BeautifulSoup` — HTML Parsing  
- `tldextract` — Domain & Subdomain Intelligence  
- `colorama` — Terminal Output Coloring  
- `concurrent.futures` — Parallel Directory Bruteforcing  
- Standard Python 3.x Libraries  

---
## ⚠️ DISCLAIMER ⚠️  

**This tool is intended for _authorized security assessments_ and _educational research_ only.**  
**❗ Unauthorized scanning or targeting of systems you do not own or lack explicit permission to assess is strictly prohibited.**  
**💀 The author assumes _no responsibility_ for misuse, damages, or illegal activity stemming from this project.**
---
## 🤗 Creater: Muhammad Nabhan(Cyberworrier), GPT
## ⚙️ Installation  

### 1. Clone the Repository  

```bash  
git clone https://github.com/cyberworrier8088/Hydra-Recon-Pro.git  
cd Hydra-Recon-Pro
pip install -r requirements.txt
python3 HydraReconPro.py
