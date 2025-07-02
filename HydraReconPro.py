import requests
from bs4 import BeautifulSoup
import urllib3
from urllib.parse import urljoin, urlparse, urlencode
import tldextract
import re
import json
import time
import random
from colorama import Fore, Style, init
from concurrent.futures import ThreadPoolExecutor, as_completed
from subprocess import getoutput

# Initialize coloring and disable warnings
init(autoreset=True)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- Global State ---
visited = set()
site_map = []              # list of (url, status)
hidden_params = set()
emails = set()
phones = set()
sensitive_data = set()
dirs_found = []
subdomains = set()
tech_detected = set()
proxies = []
use_proxies = False

# Wordlists & Agents
file_discovery_list = [
    "admin", "login", "dashboard", "config", "uploads", "backup", ".git",
    "server-status", "hidden", "test", "dev", "staging", "private", "secret"
]
fuzz_payloads = ["' OR '1'='1", "<script>alert(1)</script>", "../../etc/passwd"]
user_agents = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
    "Mozilla/5.0 (X11; Linux x86_64)",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X)"
]

# --- Helpers ---
def normalize_url(url):
    p = urlparse(url)
    return f"{p.scheme}://{p.netloc}{p.path.rstrip('/')}"

def is_same_domain(url, root):
    try:
        e = tldextract.extract(url)
        return f"{e.domain}.{e.suffix}" == root
    except:
        return False

def get_proxy():
    if use_proxies and proxies:
        p = random.choice(proxies)
        return {"http": p, "https": p}
    return None

def load_proxies(path):
    global proxies
    try:
        with open(path, 'r') as f:
            proxies = [l.strip() for l in f if l.strip()]
        print(f"{Fore.GREEN}[+] Loaded {len(proxies)} proxies{Style.RESET_ALL}")
    except Exception as e:
        print(f"{Fore.RED}[ERROR] Could not load proxies: {e}{Style.RESET_ALL}")

# --- Extraction & Fingerprinting ---
def extract_data(html):
    emails.update(re.findall(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", html))
    phones.update(re.findall(r"\+?\d[\d\s\-\(\)]{7,}\d", html))
    hidden_params.update(re.findall(
        r'<input[^>]+type=["\']hidden["\'][^>]*name=["\']([^"\']+)["\']', html, re.I
    ))
    for kw in ["password","secret","apikey","token"]:
        if kw in html.lower():
            sensitive_data.add(kw)

def fingerprint(html, headers):
    patterns = {
        "WordPress":"wp-content","Joomla":"joomla","Drupal":"drupal",
        "Apache":"Apache","Nginx":"nginx","React":"React","Laravel":"laravel"
    }
    for tech, pat in patterns.items():
        if pat.lower() in html.lower() or pat.lower() in str(headers).lower():
            tech_detected.add(tech)

# --- Passive OSINT ---
def passive_osint(domain):
    print(f"\n{Fore.MAGENTA}[*] WHOIS:{Style.RESET_ALL}")
    print(getoutput(f"whois {domain}"))

    print(f"\n{Fore.MAGENTA}[*] crt.sh Subdomains:{Style.RESET_ALL}")
    try:
        r = requests.get(f"https://crt.sh/?q=%.{domain}&output=json", timeout=10)
        for entry in r.json():
            for name in entry.get("name_value","").split("\n"):
                subdomains.add(name.strip())
        for s in sorted(subdomains):
            print(f"{Fore.LIGHTBLACK_EX}{s}{Style.RESET_ALL}")
    except requests.exceptions.RequestException as e:
        print(f"{Fore.RED}[ERROR] crt.sh failed: {e}{Style.RESET_ALL}")

    print(f"\n{Fore.MAGENTA}[*] Reverse IP (hackertarget):{Style.RESET_ALL}")
    try:
        print(requests.get(
            f"https://api.hackertarget.com/reverseiplookup/?q={domain}", timeout=5
        ).text)
    except requests.exceptions.RequestException:
        print(f"{Fore.RED}[ERROR] Reverse IP failed{Style.RESET_ALL}")

# --- robots.txt & sitemap ---
def extract_robots(domain):
    url = f"https://{domain}/robots.txt"
    try:
        r = requests.get(url, timeout=5, verify=False)
        if r.status_code == 200:
            print(f"{Fore.YELLOW}[+] robots.txt:{Style.RESET_ALL}\n{r.text}")
    except requests.exceptions.RequestException:
        pass

def extract_sitemap(domain):
    url = f"https://{domain}/sitemap.xml"
    try:
        r = requests.get(url, timeout=5, verify=False)
        if r.status_code == 200:
            print(f"{Fore.YELLOW}[+] sitemap.xml:{Style.RESET_ALL}\n{r.text}")
            return True
    except requests.exceptions.RequestException:
        pass
    return False

# --- Directory Bruteforce ---
def test_directory(base, path):
    url = urljoin(base, path)
    try:
        r = requests.get(url, timeout=5, verify=False,
                         headers={"User-Agent":random.choice(user_agents)},
                         proxies=get_proxy())
        if r.status_code in (200,301,302):
            print(f"{Fore.GREEN}[{r.status_code}] Dir: {url}{Style.RESET_ALL}")
            dirs_found.append((url, r.status_code))
    except requests.exceptions.RequestException:
        pass

def dir_bruteforce(base, parallel=True):
    print(f"\n{Fore.MAGENTA}[*] Directory Bruteforce ({'parallel' if parallel else 'sequential'}){Style.RESET_ALL}")
    if parallel:
        with ThreadPoolExecutor(max_workers=10) as ex:
            list(ex.map(lambda p: test_directory(base, p), file_discovery_list))
    else:
        for p in file_discovery_list:
            test_directory(base, p)

# --- Hidden Parameter Fuzzing ---
def fuzz_params(base):
    print(f"\n{Fore.MAGENTA}[*] Fuzzing Hidden Parameters{Style.RESET_ALL}")
    for param in hidden_params:
        for payload in fuzz_payloads:
            url = f"{base}?{urlencode({param:payload})}"
            try:
                r = requests.get(url, timeout=5, verify=False,
                                 headers={"User-Agent":random.choice(user_agents)},
                                 proxies=get_proxy())
                print(f"{Fore.CYAN}[{r.status_code}] {param}={payload}{Style.RESET_ALL}")
            except requests.exceptions.RequestException:
                print(f"{Fore.RED}[ERROR] Fuzz {param}{Style.RESET_ALL}")

# --- Crawler ---
def crawl(url, domain, depth=0, max_depth=20):
    url = normalize_url(url)
    if url in visited or depth>max_depth:
        return
    visited.add(url)
    headers = {"User-Agent":random.choice(user_agents), "Accept-Language":"en-US"}
    time.sleep(random.uniform(0.5,1.5))
    try:
        r = requests.get(url, timeout=8, verify=False, headers=headers, proxies=get_proxy())
        status = r.status_code
        clr = Fore.GREEN if status<300 else Fore.YELLOW if status<400 else Fore.RED
        print(f"{clr}[{status}] {url}{Style.RESET_ALL}")
        site_map.append((url,status))
        extract_data(r.text); fingerprint(r.text,r.headers)
        soup = BeautifulSoup(r.text, "html.parser")
        for a in soup.find_all("a", href=True):
            link = urljoin(url,a["href"])
            if is_same_domain(link, domain):
                crawl(link, domain, depth+1, max_depth)
    except requests.exceptions.RequestException as e:
        print(f"{Fore.RED}[ERROR] {e}{Style.RESET_ALL}")

# --- Main Workflow ---
def start_scan(target):
    global use_proxies
    parsed = urlparse(target)
    domain = f"{tldextract.extract(target).domain}.{tldextract.extract(target).suffix}"
    print(f"{Fore.GREEN}[+] Scanning: {domain}{Style.RESET_ALL}")

    if input("Use proxies? (yes/no): ").lower()=="yes":
        load_proxies(input("Proxy file path: ").strip())
        use_proxies = True

    passive_osint(domain)
    extract_robots(domain)
    extract_sitemap(domain)

    base = normalize_url(target)
    dir_mode = input("Parallel dir bruteforce? (yes/no): ").lower()=="yes"
    dir_bruteforce(base, parallel=dir_mode)

    crawl_mode = input("Start crawl? (yes/no): ").lower()=="yes"
    if crawl_mode:
        crawl(base, domain)

    if hidden_params:
        if input("Fuzz hidden params? (yes/no): ").lower()=="yes":
            fuzz_params(base)

    # Summary & Report
    print(f"\n{Fore.GREEN}[+] Complete{Style.RESET_ALL}")
    print(f"Pages: {len(site_map)}, Dirs: {len(dirs_found)}, Params: {len(hidden_params)}")
    print(f"Emails: {len(emails)}, Phones: {len(phones)}, Tech: {tech_detected}")

    report = {
        "domain": domain,
        "pages": site_map,
        "dirs": dirs_found,
        "hidden_params": list(hidden_params),
        "emails": list(emails),
        "phones": list(phones),
        "sensitive": list(sensitive_data),
        "tech": list(tech_detected),
        "subdomains": list(subdomains),
        "used_proxies": use_proxies
    }
    with open(f"{domain}_elite_report.json","w") as f:
        json.dump(report, f, indent=2)
    print(f"{Fore.GREEN}[+] Report saved: {domain}_elite_report.json{Style.RESET_ALL}")

# --- CLI ---
if __name__ == "__main__":
    print(f"{Fore.BLUE}=== Hydra Recon Pro: Elite APT Edition ==={Style.RESET_ALL}")
    target = input("Enter target URL (https://...): ").strip()
    start_scan(target)
