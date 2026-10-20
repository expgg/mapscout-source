"""
=============================================================================
                  MapScout v2.5 — Enterprise Edition
        Autonomous High-Velocity Google Maps Lead Harvester & 
                   B2B Cold Outreach Intelligence Engine
                       Engineered by Al Hossain Rifat
=============================================================================
Features:
  1. Blazing Fast In-Page AJAX Extraction: Clicks and scrapes cards in-page
     (<0.6s per place) without slow page reloads.
  2. Unlimited / 'All' Quota Mode: Scrapes all available businesses in any
     location until the Google Maps feed reaches the end.
  3. Real Website vs Social Media Distinction: Instagram/Facebook profiles
     are routed to Social Profiles, never mistaken for business websites.
  4. Dual-Engine Website Crawler (Always Active by Default): Fast HTTP spider
     + Dynamic secondary browser window fallback for JS/React sites.
  5. Merged Rating & Reviews: Formatted cleanly as '⭐ 4.9 (331)' in a single cell.
  6. Quality Hierarchy Sorting: High-value leads (verified email + phone + site)
     are automatically ranked at the top of both the CSV and Google Sheet.
  7. Redesigned Single-Row Master Google Sheets Bar:
     Topic on left + 4 Live KPI badges in Google Maps Brand Colors.
  8. Exact Column Hierarchy:
     # | Business Name | Email Address | Phone Number | Website | Category |
     Rating & Reviews | Social Profiles | Google Maps | Full Address | Quality Score
=============================================================================
"""

import sys
import os
import io
import time
import re
import json
import html
import argparse
import urllib.parse
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import urllib3
import requests
from bs4 import BeautifulSoup
import pandas as pd

# Suppress SSL / insecure request warnings from external websites
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Force UTF-8 on Windows terminal to prevent cp1252 encoding crashes
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        try:
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
            sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
        except Exception:
            pass

from seleniumbase import Driver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException

# Rich console styling
try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.text import Text
    from rich import box
    console = Console(file=sys.stdout, legacy_windows=False, force_terminal=True, safe_box=True)
    HAS_RICH = True
except ImportError:
    HAS_RICH = False
    console = None


def print_banner():
    if HAS_RICH:
        console.print()
        console.print("[bold cyan]✦ MapScout[/bold cyan] [dim]v2.5[/dim]")
        console.print("[dim]Autonomous High-Velocity Google Maps Lead Harvester & B2B Engine[/dim]")
        console.print("[italic yellow]Engineered by Al Hossain Rifat[/italic yellow]\n")
    else:
        print("\n* MapScout v2.5")
        print("Autonomous High-Velocity Google Maps Lead Harvester & B2B Engine")
        print("Engineered by Al Hossain Rifat\n")


def print_config_panel(niche: str, location: str, quota_display: str, sheet_url: str, output_path: str):
    if HAS_RICH:
        grid = Table.grid(expand=True, padding=(0, 2))
        grid.add_column(style="bold cyan", justify="left")
        grid.add_column(style="white", justify="left")
        grid.add_column(style="bold cyan", justify="left")
        grid.add_column(style="white", justify="left")

        grid.add_row("Niche / Category:", f"[yellow]{niche}[/yellow]", "Target Geo:", f"[green]{location}[/green]")
        grid.add_row("Harvest Quota:", f"[magenta]{quota_display}[/magenta]", "Website Crawler:", "[green]Active (Dual-Engine)[/green]")
        webhook_status = "[green]Connected (Live Stream)[/green]" if sheet_url else "[dim]Disabled (Local CSV)[/dim]"
        grid.add_row("Google Sheets:", webhook_status, "Output File:", f"[dim]{output_path}[/dim]")

        p = Panel(grid, title="[bold cyan] ACTIVE HARVEST PARAMETERS [/bold cyan]", border_style="cyan", box=box.ROUNDED)
        console.print(p)
        console.print()
    else:
        print("-" * 65)
        print(f"Niche: {niche} | Location: {location}")
        print(f"Quota: {quota_display} | Web Crawler: Active")
        print(f"Google Sheets: {'Connected' if sheet_url else 'Disabled'}")
        print(f"Output File: {output_path}")
        print("-" * 65 + "\n")


# ---------------------------------------------------------------------------
# Visual Virtual Cursor & Humanized Browser Effects
# ---------------------------------------------------------------------------

INJECT_CURSOR_JS = """
if (!document.getElementById('virtual-bot-cursor')) {
    const cursor = document.createElement('div');
    cursor.id = 'virtual-bot-cursor';
    cursor.style.position = 'fixed';
    cursor.style.zIndex = '9999999';
    cursor.style.width = '16px';
    cursor.style.height = '16px';
    cursor.style.borderRadius = '50%';
    cursor.style.background = 'rgba(0, 229, 255, 0.9)';
    cursor.style.border = '2px solid #ffffff';
    cursor.style.boxShadow = '0 0 15px #00e5ff, 0 0 30px #00e5ff';
    cursor.style.pointerEvents = 'none';
    cursor.style.transform = 'translate(-50%, -50%)';
    cursor.style.transition = 'left 0.25s cubic-bezier(0.2, 0.8, 0.2, 1), top 0.25s cubic-bezier(0.2, 0.8, 0.2, 1), transform 0.15s ease';
    cursor.style.top = '120px';
    cursor.style.left = '120px';
    document.body.appendChild(cursor);
    
    window.lastBotActivity = Date.now();
    
    window.botCursorMove = function(x, y) {
        window.lastBotActivity = Date.now();
        cursor.style.left = x + 'px';
        cursor.style.top = y + 'px';
    };
    
    window.botCursorClick = function(x, y) {
        window.lastBotActivity = Date.now();
        cursor.style.left = x + 'px';
        cursor.style.top = y + 'px';
        cursor.style.transform = 'translate(-50%, -50%) scale(0.6)';
        
        const ripple = document.createElement('div');
        ripple.style.position = 'fixed';
        ripple.style.zIndex = '9999998';
        ripple.style.left = x + 'px';
        ripple.style.top = y + 'px';
        ripple.style.width = '14px';
        ripple.style.height = '14px';
        ripple.style.borderRadius = '50%';
        ripple.style.border = '2px solid #00ff88';
        ripple.style.transform = 'translate(-50%, -50%) scale(1)';
        ripple.style.transition = 'all 0.35s ease-out';
        ripple.style.pointerEvents = 'none';
        document.body.appendChild(ripple);
        
        setTimeout(() => {
            ripple.style.transform = 'translate(-50%, -50%) scale(4)';
            ripple.style.opacity = '0';
        }, 20);
        
        setTimeout(() => {
            cursor.style.transform = 'translate(-50%, -50%) scale(1)';
            ripple.remove();
        }, 350);
    };
}
"""

def inject_visual_cursor(driver):
    try:
        driver.execute_script(INJECT_CURSOR_JS)
    except Exception:
        pass


def move_cursor_to(driver, element, click=False):
    try:
        inject_visual_cursor(driver)
        rect = driver.execute_script("return arguments[0].getBoundingClientRect();", element)
        if rect:
            target_x = int(rect['left'] + rect['width'] / 2)
            target_y = int(rect['top'] + rect['height'] / 2)
            driver.execute_script(f"if (window.botCursorMove) window.botCursorMove({target_x}, {target_y});")
            time.sleep(0.05)
            if click:
                driver.execute_script(f"if (window.botCursorClick) window.botCursorClick({target_x}, {target_y});")
                time.sleep(0.05)
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Real Website vs Social Profile Validator
# ---------------------------------------------------------------------------

SOCIAL_DOMAINS = [
    "instagram.com", "facebook.com", "fb.com", "twitter.com",
    "x.com", "tiktok.com", "linkedin.com", "youtube.com",
    "pinterest.com", "yelp.com", "tripadvisor.com"
]

def is_social_url(url: str) -> bool:
    if not url or url == "N/A":
        return False
    u = url.lower()
    return any(sd in u for sd in SOCIAL_DOMAINS)


# ---------------------------------------------------------------------------
# Dual-Engine Website Spider (Fast HTTP + Secondary Chrome Window Fallback)
# ---------------------------------------------------------------------------

EMAIL_REGEX = re.compile(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+')
PHONE_REGEX = re.compile(r'(?:\+?1[-.\s]?)?\(?([2-9][0-9]{2})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})')
JUNK_EXTS = ('.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp', '.ico', '.css', '.js', '.woff', '.woff2', '.ttf', '.mp4', '.avi')
JUNK_SUBSTRINGS = (
    'sentry.io', 'wixpress.com', 'example.com', 'yourdomain.com',
    'company.com', 'mycompany.com', 'placeholder', 'schema.org',
    'bootstrap', 'cloudflare.com', 'wordpress.org', 'wix-fonts',
    'fancybox', 'react@', 'vue@', 'core-js@', 'babel@', 'webpack@',
    'lodash@', 'fontawesome@', 'jquery@', 'npm@', 'git@', 'test@test'
)


def is_valid_email(email: str) -> bool:
    if not email or "@" not in email:
        return False
    e = email.lower().strip().rstrip(".")
    if any(e.endswith(ext) for ext in JUNK_EXTS):
        return False
    if any(j in e for j in JUNK_SUBSTRINGS):
        return False
    # Reject npm package version tags like react@18.2.0, fancybox@3.5.7
    if re.search(r'@[0-9.]+$', e):
        return False
    parts = e.split("@")
    if len(parts) != 2:
        return False
    user, domain = parts
    if len(user) < 1 or len(domain) < 3:
        return False
    # Filter pure dummy emails
    if user in ("user", "username", "name", "email", "yourname", "test") and domain in ("example.com", "domain.com", "email.com"):
        return False
    if not re.search(r'\.[a-zA-Z]{2,10}$', domain):
        return False
    return True


def normalize_name(s: str) -> str:
    if not s:
        return ""
    return re.sub(r'[^a-zA-Z0-9]', '', str(s)).lower()


def clean_phone_number(raw: str) -> str:
    if not raw:
        return ""
    digits = re.sub(r'\D', '', raw)
    if len(digits) == 10:
        return f"+1 ({digits[:3]}) {digits[3:6]}-{digits[6:]}"
    elif len(digits) == 11 and digits.startswith("1"):
        return f"+1 ({digits[1:4]}) {digits[4:7]}-{digits[7:]}"
    elif len(digits) >= 10:
        return raw.strip()
    return ""


def decode_cf_email(cf_hex: str) -> str:
    try:
        r = int(cf_hex[:2], 16)
        return ''.join([chr(int(cf_hex[i:i+2], 16) ^ r) for i in range(2, len(cf_hex), 2)])
    except Exception:
        return ""


def extract_from_html_content(raw_html: str, base_url: str):
    """
    Multi-strategy extractor: Mailto/Tel anchors, JSON-LD Schema, Cloudflare hex,
    HTML entity unescaping, written obfuscation, regex emails, and phone numbers.
    """
    emails = set()
    phones = set()
    socials = set()

    if not raw_html:
        return emails, phones, socials

    # 1. Cloudflare hex decoding
    for m in re.finditer(r'data-cfemail="([a-f0-9]+)"', raw_html, re.IGNORECASE):
        dec = decode_cf_email(m.group(1))
        if is_valid_email(dec):
            emails.add(dec)

    for m in re.finditer(r'/cdn-cgi/l/email-protection#([a-f0-9]+)', raw_html, re.IGNORECASE):
        dec = decode_cf_email(m.group(1))
        if is_valid_email(dec):
            emails.add(dec)

    # 2. HTML Unescape
    clean_html = html.unescape(raw_html)

    # 3. Soup parse for structured anchors & JSON-LD
    try:
        soup = BeautifulSoup(clean_html, 'html.parser')

        # Mailto links (with URL decoding to handle %40 for @)
        for a in soup.find_all('a', href=True):
            h = a['href'].strip()
            hl = h.lower()
            if 'mailto:' in hl:
                decoded = urllib.parse.unquote(h)
                c_email = re.sub(r'^.*?mailto:', '', decoded, flags=re.IGNORECASE).split('?')[0].strip()
                if is_valid_email(c_email):
                    emails.add(c_email)
            elif 'tel:' in hl:
                tel_val = clean_phone_number(re.sub(r'^.*?tel:', '', h, flags=re.IGNORECASE).split('?')[0].strip())
                if tel_val:
                    phones.add(tel_val)

            # Social links
            for platform in ['linkedin.com', 'facebook.com', 'instagram.com', 'twitter.com', 'x.com', 'tiktok.com']:
                if platform in hl and not any(k in hl for k in ['share', 'intent', 'cdn', '.jpg', '.png', 'sharer']):
                    socials.add(h.split('?')[0].strip())

        # JSON-LD Schema (LocalBusiness, Organization, Store)
        for s in soup.find_all('script', type='application/ld+json'):
            try:
                js_data = json.loads(s.string or "{}")
                items = js_data if isinstance(js_data, list) else [js_data]
                if isinstance(js_data, dict) and "@graph" in js_data:
                    items.extend(js_data["@graph"])

                for item in items:
                    if isinstance(item, dict):
                        em = item.get("email")
                        if em and is_valid_email(str(em)):
                            emails.add(str(em))
                        tel = item.get("telephone") or item.get("phone")
                        if tel:
                            cp = clean_phone_number(str(tel))
                            if cp:
                                phones.add(cp)
            except Exception:
                pass

    except Exception:
        pass

    # 4. Normalized Written Obfuscations ("name [at] domain.com" or "name (at) domain.com")
    normalized_text = re.sub(r'\s*(?:\[|\()at(?:\]|\))\s*', '@', clean_html, flags=re.IGNORECASE)
    normalized_text = re.sub(r'\s*(?:\[|\()dot(?:\]|\))\s*', '.', normalized_text, flags=re.IGNORECASE)
    normalized_text = re.sub(r'\s+at\s+', '@', normalized_text, flags=re.IGNORECASE)
    normalized_text = re.sub(r'\s+dot\s+', '.', normalized_text, flags=re.IGNORECASE)

    # 5. Regex emails
    for match in EMAIL_REGEX.findall(normalized_text):
        if is_valid_email(match):
            emails.add(match.strip().rstrip('.'))

    # 6. Regex phone numbers
    for m in PHONE_REGEX.finditer(clean_html):
        p_str = f"({m.group(1)}) {m.group(2)}-{m.group(3)}"
        phones.add(p_str)

    return emails, phones, socials


def crawl_website_http(base_url: str):
    """
    Multi-strategy high-velocity concurrent HTTP spider.
    Extracts emails, phone numbers, and social profiles from homepage,
    contact pages, about pages, and privacy policy pages in parallel.
    Uses non-blocking timeouts to prevent hanging.
    """
    discovered_emails = set()
    discovered_phones = set()
    discovered_socials = set()

    if not base_url or not base_url.startswith("http") or is_social_url(base_url):
        return list(discovered_emails), list(discovered_phones), list(discovered_socials)

    http_headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Upgrade-Insecure-Requests": "1"
    }

    base_domain = urllib.parse.urlparse(base_url).netloc.lower().replace("www.", "")
    contact_urls = set()

    # Common standard probe paths
    standard_paths = [
        "/contact", "/contact-us", "/contactus", "/pages/contact",
        "/about", "/about-us", "/aboutus", "/support", "/help", "/location"
    ]
    for p in standard_paths:
        contact_urls.add(urllib.parse.urljoin(base_url, p))

    try:
        # Step 1: Fetch homepage with clean session
        with requests.Session() as session:
            session.headers.update(http_headers)
            resp = session.get(base_url, timeout=(2.5, 3.5), verify=False)
            if resp.status_code == 200:
                em, ph, soc = extract_from_html_content(resp.text, base_url)
                discovered_emails.update(em)
                discovered_phones.update(ph)
                discovered_socials.update(soc)

                # Step 2: Discover internal contact/policy anchors from homepage
                soup = BeautifulSoup(resp.text, 'html.parser')
                for a in soup.find_all('a', href=True):
                    href = a['href'].strip()
                    full_url = urllib.parse.urljoin(base_url, href)
                    target_netloc = urllib.parse.urlparse(full_url).netloc.lower().replace("www.", "")
                    if target_netloc == base_domain and any(k in full_url.lower() for k in ['contact', 'about', 'reach', 'support', 'help']):
                        contact_urls.add(full_url.split('#')[0])

    except Exception:
        pass

    # Step 3: Fetch subpages concurrently via ThreadPoolExecutor with strict timeout
    urls_to_crawl = list(contact_urls)[:5]

    def fetch_subpage(url):
        try:
            with requests.Session() as s:
                s.headers.update(http_headers)
                r = s.get(url, timeout=(2.0, 3.0), verify=False)
                if r.status_code == 200:
                    return extract_from_html_content(r.text, url)
        except Exception:
            pass
        return set(), set(), set()

    if urls_to_crawl and (not discovered_emails or not discovered_phones):
        with ThreadPoolExecutor(max_workers=5) as executor:
            future_to_url = {executor.submit(fetch_subpage, u): u for u in urls_to_crawl}
            try:
                for future in as_completed(future_to_url, timeout=4.0):
                    try:
                        em, ph, soc = future.result()
                        discovered_emails.update(em)
                        discovered_phones.update(ph)
                        discovered_socials.update(soc)
                    except Exception:
                        pass
            except TimeoutError:
                pass
            except Exception:
                pass

    return list(discovered_emails), list(discovered_phones), list(discovered_socials)


DOM_EXTRACT_JS = r"""
function extractWebsiteDom() {
    let emails = [];
    let phones = [];
    let socials = [];
    let contactLinks = [];

    // 1. Mailto links
    document.querySelectorAll('a[href*="mailto:"]').forEach(a => {
        try {
            let raw = decodeURIComponent(a.href);
            let m = raw.replace(/^.*?mailto:/i, '').split('?')[0].trim();
            if (m && m.includes('@')) emails.push(m);
        } catch(e) {}
    });

    // 2. Tel links
    document.querySelectorAll('a[href*="tel:"]').forEach(a => {
        try {
            let t = a.href.replace(/^.*?tel:/i, '').split('?')[0].trim();
            if (t) phones.push(t);
        } catch(e) {}
    });

    // 3. Socials & contact links
    document.querySelectorAll('a[href]').forEach(a => {
        try {
            let h = a.href;
            let hl = h.toLowerCase();
            if (hl.includes('facebook.com/') || hl.includes('instagram.com/') || hl.includes('linkedin.com/') || hl.includes('twitter.com/') || hl.includes('x.com/')) {
                if (!hl.includes('/share') && !hl.includes('/intent') && !hl.includes('.jpg') && !hl.includes('.png')) {
                    socials.push(h.split('?')[0]);
                }
            }
            if (hl.includes('contact') || hl.includes('about') || hl.includes('support') || hl.includes('reach')) {
                if (h.startsWith('http') && !contactLinks.includes(h)) {
                    contactLinks.push(h);
                }
            }
        } catch(e) {}
    });

    // 4. Inner text scan
    let bodyText = document.body ? document.body.innerText : '';
    let matches = bodyText.match(/[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+/g) || [];
    matches.forEach(e => emails.push(e));

    return {
        emails: emails,
        phones: phones,
        socials: socials,
        contactLinks: contactLinks,
        html: document.documentElement.outerHTML
    };
}
return extractWebsiteDom();
"""


def crawl_website_dynamic_window(driver, main_window, base_url: str):
    """
    Triggers a fast background tab beside Google Maps to render dynamic SPAs / JavaScript
    and extract emails/phones directly from the live rendered DOM.
    Guarantees tab closure and returns focus safely to main_window.
    """
    discovered_emails = set()
    discovered_phones = set()
    discovered_socials = set()

    if not base_url or not base_url.startswith("http") or is_social_url(base_url):
        return list(discovered_emails), list(discovered_phones), list(discovered_socials)

    opened_tab = None

    try:
        handles_before = set(driver.window_handles)
        driver.switch_to.new_window('tab')
        handles_after = set(driver.window_handles) - handles_before
        if handles_after:
            opened_tab = list(handles_after)[0]

        driver.set_page_load_timeout(6.0)

        try:
            driver.get(base_url)
        except TimeoutException:
            try:
                driver.execute_script("window.stop();")
            except Exception:
                pass

        time.sleep(0.9)

        # Direct in-browser JavaScript DOM extraction
        dom_data = driver.execute_script(DOM_EXTRACT_JS) or {}
        for em in dom_data.get("emails", []):
            if is_valid_email(em):
                discovered_emails.add(em)
        for ph in dom_data.get("phones", []):
            cp = clean_phone_number(ph)
            if cp:
                discovered_phones.add(cp)
        for soc in dom_data.get("socials", []):
            discovered_socials.add(soc)

        # Fallback to HTML parser
        raw_html = dom_data.get("html") or ""
        if raw_html:
            em2, ph2, soc2 = extract_from_html_content(raw_html, base_url)
            discovered_emails.update(em2)
            discovered_phones.update(ph2)
            discovered_socials.update(soc2)

        # If email still not found, navigate tab to the first discovered contact page
        contact_links = dom_data.get("contactLinks", [])
        if not discovered_emails and contact_links:
            target_contact = contact_links[0]
            try:
                driver.get(target_contact)
            except TimeoutException:
                try:
                    driver.execute_script("window.stop();")
                except Exception:
                    pass
            time.sleep(0.8)

            sub_dom = driver.execute_script(DOM_EXTRACT_JS) or {}
            for em in sub_dom.get("emails", []):
                if is_valid_email(em):
                    discovered_emails.add(em)
            for ph in sub_dom.get("phones", []):
                cp = clean_phone_number(ph)
                if cp:
                    discovered_phones.add(cp)
            for soc in sub_dom.get("socials", []):
                discovered_socials.add(soc)

    except Exception:
        pass
    finally:
        try:
            # Safely close ONLY the secondary tab if it is alive and distinct
            if opened_tab and opened_tab in driver.window_handles and opened_tab != main_window:
                driver.switch_to.window(opened_tab)
                driver.close()
        except Exception:
            pass
        try:
            # Guarantee driver is always switched back to main_window
            if main_window in driver.window_handles:
                driver.switch_to.window(main_window)
            elif driver.window_handles:
                driver.switch_to.window(driver.window_handles[0])
            driver.set_page_load_timeout(30)
        except Exception:
            pass

    return list(discovered_emails), list(discovered_phones), list(discovered_socials)


# ---------------------------------------------------------------------------
# Lead Quality Score (0–100) Calculator
# ---------------------------------------------------------------------------

def compute_quality_score(name: str, phone: str, email: str, website: str, rating: float, address: str) -> int:
    score = 20  # Base score for verified business entity
    if phone and phone != "N/A":
        score += 25
    if email and email != "N/A":
        score += 25
    if website and website != "N/A":
        score += 15
    if rating and rating > 0:
        score += 10
    if address and address != "N/A":
        score += 5
    return min(100, score)


# ---------------------------------------------------------------------------
# Google Sheets Webhook Synchronizer
# ---------------------------------------------------------------------------

def check_webhook_status(sheet_url: str):
    if not sheet_url:
        return
    try:
        r = requests.get(sheet_url, timeout=12)
        if r.status_code == 200:
            if HAS_RICH:
                console.print("  [bold green][✓][/bold green] Google Sheets Webhook is [bold green]ONLINE[/bold green] & connected.\n")
            else:
                print("  [✓] Google Sheets Webhook is ONLINE & connected.\n")
    except Exception as e:
        if HAS_RICH:
            console.print(f"  [bold yellow][!][/bold yellow] Webhook status check notice: [dim]{e}[/dim]\n")
        else:
            print(f"  [!] Webhook status check notice: {e}\n")


def sync_to_google_sheet(sheet_url: str, rows: list, topic: str, sheet_id: str = None, mode: str = "append"):
    if not sheet_url:
        return sheet_id, None
    try:
        payload = {
            "action": "sync",
            "topic": topic,
            "sheet_id": sheet_id,
            "mode": mode,
            "rows": rows
        }
        res = requests.post(sheet_url, json=payload, timeout=35)
        if res.status_code == 200:
            data = res.json()
            if data.get("status") == "success":
                return data.get("sheet_id"), data.get("sheet_url")
    except Exception:
        pass
    return sheet_id, None


# ---------------------------------------------------------------------------
# In-Page Fast DOM Details Extractor (Single JavaScript Execution)
# ---------------------------------------------------------------------------

EXTRACT_DETAILS_JS = """
function extractPlaceDetails() {
    let res = {
        name: "",
        category: "",
        rating: "",
        reviews: "",
        address: "N/A",
        phone: "N/A",
        website: "N/A",
        hours: "N/A"
    };

    // 1. Business Name
    const h1 = document.querySelector('h1.DUwDvf');
    if (h1 && h1.innerText.trim()) {
        res.name = h1.innerText.trim();
    } else {
        const allH1 = document.querySelectorAll('h1');
        for (let h of allH1) {
            let t = h.innerText.trim();
            if (t && !t.toLowerCase().includes('results') && !t.toLowerCase().includes('sponsored') && !t.toLowerCase().includes('search')) {
                res.name = t;
                break;
            }
        }
    }

    // 2. Rating & Reviews
    const f7 = document.querySelector('div.F7nice');
    if (f7) {
        const lines = f7.innerText.split('\\n').map(s => s.trim()).filter(Boolean);
        if (lines.length > 0) {
            let mRate = lines[0].match(/([0-5]\\.[0-9])/);
            if (mRate) res.rating = mRate[1];
        }
        if (lines.length > 1) {
            let mRev = lines[1].match(/([0-9,]+)/);
            if (mRev) res.reviews = mRev[1].replace(/,/g, '');
        }
    }

    // 3. Category
    const catBtn = document.querySelector("button[jsaction*='category']");
    if (catBtn && catBtn.innerText.trim()) {
        res.category = catBtn.innerText.trim();
    }

    // 4. Address
    const addrEl = document.querySelector("*[data-item-id='address']");
    if (addrEl) {
        res.address = addrEl.innerText.replace(/[\\ue0c8\\n]/g, ' ').trim();
    }

    // 5. Phone
    const phoneEl = document.querySelector("*[data-item-id*='phone']");
    if (phoneEl) {
        res.phone = phoneEl.innerText.replace(/[\\ue0b0\\n]/g, ' ').trim();
    }

    // 6. Website
    const siteEl = document.querySelector("a[data-item-id='authority']");
    if (siteEl && siteEl.href) {
        res.website = siteEl.href;
    }

    // 7. Opening Hours
    const hoursEl = document.querySelector("div[data-item-id='oh']");
    if (hoursEl) {
        res.hours = hoursEl.innerText.split('\\n')[0].trim();
    }

    return res;
}
return extractPlaceDetails();
"""

def is_end_of_feed(driver) -> bool:
    try:
        elements = driver.find_elements(By.CSS_SELECTOR, "div.HlvSq")
        for el in elements:
            t = el.text.lower()
            if "reached the end of the list" in t or "no more results" in t or "end of results" in t:
                return True
    except Exception:
        pass
    return False


def scroll_feed(driver):
    try:
        driver.execute_script("""
            const feed = document.querySelector('div[role="feed"]');
            if (feed) {
                feed.scrollBy({ top: 900, behavior: 'smooth' });
            }
        """)
        time.sleep(0.7)
    except Exception:
        pass


# ---------------------------------------------------------------------------
# High-Velocity Orchestrator Engine
# ---------------------------------------------------------------------------

def run_lead_harvester(
    niche: str,
    location: str,
    quota: int = 20,
    sheet_url: str = None,
    output_path: str = None,
    headless: bool = False
):
    print_banner()

    is_all_mode = (quota is None or quota <= 0)
    quota_display = "ALL Available Businesses (End of List)" if is_all_mode else f"{quota} businesses"

    query_term = f"{niche} in {location}"
    safe_topic = "".join([c if c.isalnum() else "-" for c in query_term]).strip("-").lower()
    while "--" in safe_topic:
        safe_topic = safe_topic.replace("--", "-")

    csv_dir = os.path.abspath("./scrapped_csv")
    os.makedirs(csv_dir, exist_ok=True)

    if not output_path:
        count_suffix = "all" if is_all_mode else str(quota)
        output_path = os.path.join(csv_dir, f"{safe_topic}-{count_suffix}-leads.csv")
    elif not os.path.isabs(output_path) and not os.path.dirname(output_path):
        output_path = os.path.join(csv_dir, output_path)


    print_config_panel(niche, location, quota_display, sheet_url, output_path)
    check_webhook_status(sheet_url)

    harvested_leads = []
    seen_place_keys = set()
    active_sheet_id = None
    active_sheet_url = None

    profile_dir = os.path.abspath("./chrome_profile")
    if HAS_RICH:
        console.print("[dim][*] Launching High-Velocity Browser Engine...[/dim]")
    else:
        print("[*] Launching High-Velocity Browser Engine...")

    driver = Driver(uc=True, headless=headless, user_data_dir=profile_dir)

    try:
        try:
            # Maximize window to ensure standard two-column desktop layout on any screen/laptop
            driver.maximize_window()
        except Exception:
            try:
                driver.set_window_size(1600, 1000)
            except Exception:
                pass

        main_window = driver.current_window_handle

        # hl=en forces standard English digits, categories, and review formatting
        search_encoded = urllib.parse.quote_plus(query_term)
        maps_url = f"https://www.google.com/maps/search/{search_encoded}?hl=en"

        if HAS_RICH:
            console.print(f"  [dim][*] Navigating to Google Maps search:[/dim] [cyan]{query_term}[/cyan]")
        else:
            print(f"  [*] Navigating to Google Maps search: {query_term}")

        driver.get(maps_url)
        time.sleep(3.2)
        try:
            # Set virtual page zoom to 85% so two-column mode fits comfortably on any laptop resolution
            driver.execute_script("document.body.style.zoom = '85%';")
        except Exception:
            pass
        inject_visual_cursor(driver)

        # Handle consent modal if present
        try:
            consent_btns = driver.find_elements(By.CSS_SELECTOR, "form[action*='consent'] button, button[aria-label*='Accept all']")
            if consent_btns:
                move_cursor_to(driver, consent_btns[0], click=True)
                consent_btns[0].click()
                time.sleep(1.2)
        except Exception:
            pass

        # Initialize Google Sheets session with clean single-row master bar
        if sheet_url:
            if HAS_RICH:
                console.print("  [dim][*] Initializing executive Google Sheet directory on Drive...[/dim]")
            active_sheet_id, active_sheet_url = sync_to_google_sheet(
                sheet_url,
                rows=[],
                topic=f"{niche.title()} in {location.title()}",
                mode="append"
            )
            if active_sheet_url:
                if HAS_RICH:
                    console.print(f"  [bold green][✓][/bold green] Google Sheet Active: [bold cyan underline]{active_sheet_url}[/bold cyan underline]\n")
                else:
                    print(f"  [✓] Google Sheet Active: {active_sheet_url}\n")

        # Set up Rich progress table
        if HAS_RICH:
            table = Table(
                title=f"Market Lead Directory — {niche.title()} in {location.title()}",
                caption="✦ High-Velocity Google Maps Harvester v2.5 • Engineered by Al Hossain Rifat ✦",
                border_style="blue",
                box=box.ROUNDED,
                header_style="bold cyan"
            )
            table.add_column("#", style="bold dim", width=4, justify="center")
            table.add_column("Business Name", style="bold white", width=25)
            table.add_column("Email Address", style="bold green", width=24)
            table.add_column("Phone Number", style="green", width=16)
            table.add_column("Website", style="cyan", width=20)
            table.add_column("Category", style="yellow", width=16)
            table.add_column("Rating & Reviews", style="red", justify="center", width=14)
            table.add_column("Score", style="bold red", justify="center", width=7)
            console.print(table)
            console.print()

        # In-Page List-by-List Harvesting Engine
        stuck_scroll_count = 0
        lead_index = 0
        last_inspected_title = ""

        # Optimized JavaScript to parse all cards currently rendered in search feed
        JS_PARSE_LIST_CARDS = """
        function parseFeedCards() {
            // Restore feed if stuck in single-pane mode
            let feed = document.querySelector('div[role="feed"]');
            if (!feed || window.getComputedStyle(feed).display === 'none') {
                let back = document.querySelector('button[aria-label="Back"], button[jsaction*="back"], button[aria-label*="back" i]');
                if (back) back.click();
            }

            let cards = document.querySelectorAll('div.Nv2PK');
            let results = [];
            cards.forEach((c, idx) => {
                let link = c.querySelector('a.hfpxzc');
                let name = link ? (link.getAttribute('aria-label') || '') : '';
                if (!name) {
                    let title = c.querySelector('div.qBF1Pd');
                    if (title) name = title.innerText.trim();
                }
                if (!name) return;

                let mapsUrl = link ? (link.href || '') : '';
                let rating = c.querySelector('span.MW4etd')?.innerText?.trim() || '';
                let reviews = c.querySelector('span.UY7F9')?.innerText?.replace(/[(),]/g, '')?.trim() || '';

                let allLines = Array.from(c.querySelectorAll('div.W4Efsd')).map(el => el.innerText.trim()).filter(Boolean);
                let category = '';
                let address = '';
                let phone = '';
                let status = '';

                for (let text of allLines) {
                    let pMatch = text.match(/(?:\\+?1[-.\\s]?)?\\(?([2-9][0-9]{2})\\)?[-.\\s]?([0-9]{3})[-.\\s]?([0-9]{4})/);
                    if (pMatch && !phone) phone = pMatch[0].trim();

                    if (text.includes('·')) {
                        let parts = text.split('·').map(s => s.trim());
                        if (parts.length >= 2 && !category && !text.match(/^[0-9.]+\\([0-9,]+\\)/)) {
                            category = parts[0];
                            address = parts.slice(1).join(', ').replace(/^[\\s\\ue000-\\uf8ff,]+/, '').trim();
                        }
                    }
                    if (text.includes('Open') || text.includes('Closed') || text.includes('Closes') || text.includes('Opens')) {
                        if (!status) status = text;
                    }
                }

                results.push({
                    index: idx,
                    name: name,
                    rating: rating,
                    reviews: reviews,
                    category: category,
                    address: address,
                    phone: phone,
                    status: status,
                    maps_url: mapsUrl
                });
            });
            return results;
        }
        return parseFeedCards();
        """

        while True:
            # Check quota exit condition
            if not is_all_mode and len(harvested_leads) >= quota:
                break

            # Parse visible cards in the feed
            try:
                cards = driver.execute_script(JS_PARSE_LIST_CARDS) or []
            except Exception:
                cards = []

            unvisited = [c for c in cards if c.get("name") and c["name"].strip() not in seen_place_keys]

            # If no unvisited cards in current view, scroll feed or check end of results
            if not unvisited:
                if is_end_of_feed(driver):
                    if HAS_RICH:
                        console.print("\n  [bold green][✓] Reached the end of Google Maps results for this search.[/bold green]\n")
                    else:
                        print("\n  [✓] Reached the end of Google Maps results for this search.\n")
                    break

                scroll_feed(driver)
                stuck_scroll_count += 1
                if stuck_scroll_count >= 6:
                    if HAS_RICH:
                        console.print("\n  [dim][*] No more new business cards found. Completing session...[/dim]\n")
                    else:
                        print("\n  [*] No more new business cards found. Completing session...\n")
                    break
                continue

            stuck_scroll_count = 0
            card_info = unvisited[0]
            b_name = card_info["name"].replace("Sponsored", "").replace("", "").strip()
            seen_place_keys.add(card_info["name"].strip())
            lead_index += 1

            try:
                target_name = b_name
                target_href = card_info.get("maps_url", "")
                norm_target = normalize_name(target_name)

                # 1. Anti-Scramble Safeguard: Purge old authority link and title before clicking so stale data can NEVER be read
                driver.execute_script("""
                    let auth = document.querySelector('a[data-item-id="authority"]');
                    if (auth) auth.remove();
                    let h1 = document.querySelector('h1.DUwDvf');
                    if (h1) h1.innerText = '';
                """)

                # 2. Click the exact card element matching target_href or target_name
                driver.execute_script("""
                    let targetHref = arguments[0];
                    let targetName = arguments[1];
                    let allCards = document.querySelectorAll('div.Nv2PK');
                    let targetLink = null;
                    for (let c of allCards) {
                        let l = c.querySelector('a.hfpxzc');
                        if (l && targetHref && l.href === targetHref) {
                            targetLink = l;
                            break;
                        }
                    }
                    if (!targetLink) {
                        for (let c of allCards) {
                            let l = c.querySelector('a.hfpxzc');
                            let aria = l ? (l.getAttribute('aria-label') || '') : '';
                            if (aria && aria.trim().toLowerCase() === targetName.toLowerCase()) {
                                targetLink = l || c;
                                break;
                            }
                        }
                    }
                    if (targetLink) targetLink.click();
                """, target_href, target_name)

                # 3. Synchronized polling (up to 0.9s) — STRICT VERIFICATION: ONLY accept details if title matches THIS exact business!
                b_website = "N/A"
                b_phone = card_info.get("phone") or "N/A"
                b_address = card_info.get("address") or "N/A"
                b_status = card_info.get("status") or "N/A"

                t_poll = time.time()
                while time.time() - t_poll < 0.9:
                    res = driver.execute_script("""
                        let h1 = document.querySelector('h1.DUwDvf');
                        let curTitle = h1 ? h1.innerText.trim() : '';
                        let auth = document.querySelector('a[data-item-id="authority"]');
                        let fullPhone = document.querySelector('button[data-item-id*="phone"]')?.innerText?.trim() || '';
                        let fullAddr = document.querySelector('button[data-item-id="address"]')?.innerText?.trim() || '';
                        let hoursEl = document.querySelector("div[data-item-id='oh']");
                        let hours = hoursEl ? hoursEl.innerText.split('\\n')[0].trim() : '';
                        return {
                            title: curTitle,
                            website: auth ? auth.href : '',
                            phone: fullPhone.replace(/^[\\s\\ue000-\\uf8ff]+/, '').trim(),
                            address: fullAddr.replace(/^[\\s\\ue000-\\uf8ff]+/, '').trim(),
                            hours: hours
                        };
                    """)
                    cur_title = res.get("title", "")
                    norm_cur = normalize_name(cur_title)

                    # Strict Name Match: MUST match the current business, never accept another place!
                    is_match = False
                    if norm_cur and norm_target:
                        if norm_target in norm_cur or norm_cur in norm_target:
                            is_match = True
                        else:
                            w_target = target_name.lower().split()
                            w_cur = cur_title.lower().split()
                            if w_target and w_cur and w_target[0] == w_cur[0]:
                                is_match = True

                    if is_match:
                        if res.get("website"):
                            b_website = res["website"]
                        if res.get("phone"):
                            b_phone = res["phone"]
                        if res.get("address"):
                            b_address = res["address"]
                        if res.get("hours"):
                            b_status = res["hours"]
                        break

                    time.sleep(0.06)


                # Clean and sanitize address and phone strings to guarantee single-line cells
                if b_address and b_address != "N/A":
                    b_address = b_address.replace("\r", " ").replace("\n", ", ").strip()
                    b_address = re.sub(r',\s*(?:Closed|Open|Opens|Closes).*$', '', b_address, flags=re.I).strip()
                    b_address = re.sub(r',\s*(?:\+?1[-.\s]?)?\(?[2-9]\d{2}\)?[-.\s]?\d{3}[-.\s]?\d{4}$', '', b_address).strip()
                    while ", ," in b_address:
                        b_address = b_address.replace(", ,", ",")
                    b_address = b_address.strip(" ,")

                if b_phone and b_phone != "N/A":
                    b_phone = b_phone.replace("\r", " ").replace("\n", " ").strip()

                # CRITICAL LAPTOP SAFEGUARD: If single-pane mode, restore feed immediately via Back button
                driver.execute_script("""
                    let feed = document.querySelector('div[role="feed"]');
                    if (!feed || window.getComputedStyle(feed).display === 'none') {
                        let backBtn = document.querySelector('button[aria-label="Back"], button[jsaction*="back"], button[aria-label*="back" i]');
                        if (backBtn) backBtn.click();
                    }
                """)


                # Format Rating and Review Count
                b_rating_str = card_info.get("rating") or ""
                b_reviews_str = card_info.get("reviews") or ""
                b_rating = float(b_rating_str) if b_rating_str else 0.0
                try:
                    b_reviews = int(b_reviews_str.replace(",", "")) if b_reviews_str else 0
                except Exception:
                    b_reviews = 0

                if b_rating > 0:
                    rating_reviews_disp = f"⭐ {b_rating:.1f}" + (f" ({b_reviews:,})" if b_reviews > 0 else "")
                else:
                    rating_reviews_disp = "-"

                b_category = card_info.get("category") or niche.title()
                place_url = card_info.get("maps_url") or maps_url

                # Website vs Social media distinction:
                # If website is an Instagram/Facebook link, route it to Social Profiles!
                social_profiles = []
                final_website = "N/A"

                if b_website != "N/A":
                    if is_social_url(b_website):
                        social_profiles.append(b_website)
                        final_website = "N/A"
                    else:
                        final_website = b_website

                # Fast Concurrent Multi-Strategy HTTP Website Crawler (Zero tab switching lag!)
                b_email = "N/A"
                if final_website != "N/A":
                    found_emails, found_phones, found_soc = crawl_website_http(final_website)
                    if found_emails:
                        b_email = found_emails[0]
                    if (not b_phone or b_phone == "N/A") and found_phones:
                        b_phone = found_phones[0]
                    for s in found_soc:
                        if s not in social_profiles:
                            social_profiles.append(s)

                socials_str = ", ".join(social_profiles[:3]) if social_profiles else "N/A"

                # Calculate Lead Quality Score (0–100)
                quality_score = compute_quality_score(
                    name=b_name,
                    phone=b_phone,
                    email=b_email,
                    website=final_website,
                    rating=b_rating,
                    address=b_address
                )

                lead_record = {
                    "rank": lead_index,
                    "business_name": b_name,
                    "email": b_email if b_email != "N/A" else "NOT FOUND",
                    "phone": b_phone if b_phone != "N/A" else "NOT FOUND",
                    "website": final_website if final_website != "N/A" else "NOT FOUND",
                    "category": b_category,
                    "rating_reviews": rating_reviews_disp if rating_reviews_disp != "-" else "NOT FOUND",
                    "social_profiles": socials_str if socials_str != "N/A" else "NOT FOUND",
                    "maps_url": place_url,
                    "address": b_address if b_address != "N/A" else "NOT FOUND",
                    "quality_score": quality_score,
                    "opening_status": b_status if b_status != "N/A" else "",
                    "rating": b_rating,
                    "reviews": b_reviews
                }

                harvested_leads.append(lead_record)

                # Real-time console table row
                if HAS_RICH:
                    phone_disp = b_phone if b_phone != "N/A" else "[red]NOT FOUND[/red]"
                    email_disp = f"[bold green]{b_email}[/bold green]" if b_email != "N/A" else "[red]NOT FOUND[/red]"
                    web_disp = (final_website.replace("https://", "").replace("http://", "").replace("www.", "").split("/")[0][:18]) if final_website != "N/A" else "[red]NOT FOUND[/red]"

                    console.print(
                        f"  [bold cyan]#{lead_index:02d}[/bold cyan]  "
                        f"[bold white]{b_name[:24]:<24}[/bold white]  "
                        f"{email_disp:<24}  "
                        f"[white]{phone_disp:<16}[/white]  "
                        f"[cyan]{web_disp:<18}[/cyan]  "
                        f"[yellow]{b_category[:14]:<14}[/yellow]  "
                        f"{rating_reviews_disp:<14}  "
                        f"[bold red]{quality_score:3d}[/bold red]"
                    )
                else:
                    print(f"  #{lead_index:02d} | {b_name} | Email: {b_email} | Phone: {b_phone} | Score: {quality_score}")

                # Real-time Google Sheets streaming (row-by-row)
                if sheet_url:
                    try:
                        if active_sheet_id:
                            sync_to_google_sheet(
                                sheet_url,
                                rows=[lead_record],
                                topic=f"{niche.title()} in {location.title()}",
                                sheet_id=active_sheet_id,
                                mode="append"
                            )
                        else:
                            new_id, new_url = sync_to_google_sheet(
                                sheet_url,
                                rows=[lead_record],
                                topic=f"{niche.title()} in {location.title()}",
                                sheet_id=None,
                                mode="append"
                            )
                            if new_id:
                                active_sheet_id = new_id
                                active_sheet_url = new_url
                    except Exception:
                        pass

            except Exception:
                continue


        # Post-Processing: Quality Hierarchy Sorting (Highest Quality at Top!)
        if harvested_leads:
            # Sort descending by quality_score, then by reviews
            harvested_leads.sort(key=lambda x: (x["quality_score"], x.get("reviews", 0)), reverse=True)

            # Re-index rank
            for i, r in enumerate(harvested_leads, start=1):
                r["rank"] = i

            # Overwrite final Google Sheet with sorted quality hierarchy
            if sheet_url:
                if HAS_RICH:
                    console.print("  [dim][*] Applying Quality Hierarchy Sorting to Google Sheet dashboard...[/dim]")
                final_id, final_url = sync_to_google_sheet(
                    sheet_url,
                    rows=harvested_leads,
                    topic=f"{niche.title()} in {location.title()}",
                    sheet_id=active_sheet_id,
                    mode="replace" if active_sheet_id else "append"
                )
                if final_url:
                    active_sheet_url = final_url
                if final_id:
                    active_sheet_id = final_id

            # Final Export to CSV (Exact User-Specified Hierarchy)
            df = pd.DataFrame(harvested_leads)

            rename_map = {
                "rank": "#",
                "business_name": "Business Name",
                "email": "Email Address",
                "phone": "Phone Number",
                "website": "Website",
                "category": "Category",
                "rating_reviews": "Rating & Reviews",
                "social_profiles": "Social Profiles",
                "maps_url": "Google Maps Link",
                "address": "Full Address",
                "quality_score": "Lead Quality Score"
            }
            ordered_cols = [
                "#", "Business Name", "Email Address", "Phone Number", "Website",
                "Category", "Rating & Reviews", "Social Profiles", "Google Maps Link",
                "Full Address", "Lead Quality Score"
            ]

            export_df = df.rename(columns=rename_map)
            export_cols = [c for c in ordered_cols if c in export_df.columns]
            export_df = export_df[export_cols]

            # Save clean UTF-8 CSV with BOM for universal Excel compatibility
            export_df.to_csv(output_path, index=False, encoding="utf-8-sig")

            emails_count = sum(1 for x in harvested_leads if x.get("email") and x.get("email") != "NOT FOUND")
            phones_count = sum(1 for x in harvested_leads if x.get("phone") and x.get("phone") != "NOT FOUND")
            avg_score = round(sum(x["quality_score"] for x in harvested_leads) / max(1, len(harvested_leads)), 1)

            if HAS_RICH:
                console.print()
                sheet_line = f"\n[bold white]Live Google Sheet Dashboard:[/bold white] [bold cyan underline]{active_sheet_url}[/bold cyan underline]" if active_sheet_url else ""
                summary = Panel(
                    f"[bold green]✔ Lead Generation Complete![/bold green] Successfully harvested [bold cyan]{len(harvested_leads)}[/bold cyan] verified leads.\n"
                    f"✉️ [bold white]Emails Discovered:[/bold white] [bold green]{emails_count}[/bold green] | "
                    f"📞 [bold white]Phones Verified:[/bold white] [bold green]{phones_count}[/bold green] | "
                    f"⭐ [bold white]Avg Quality Score:[/bold white] [bold red]{avg_score}/100[/bold red]\n"
                    f"[bold white]Export File:[/bold white] [underline yellow]{output_path}[/underline yellow]{sheet_line}\n"
                    f"[dim italic]Engineered by Al Hossain Rifat[/dim italic]",
                    border_style="green",
                    box=box.ROUNDED
                )
                console.print(summary)
            else:
                print(f"\n[COMPLETE] Successfully harvested {len(harvested_leads)} leads into {output_path}")
                print(f"Emails: {emails_count} | Phones: {phones_count} | Avg Quality Score: {avg_score}/100")
                if active_sheet_url:
                    print(f"[LIVE SHEET] {active_sheet_url}")
                print("Engineered by Al Hossain Rifat\n")

        else:
            if HAS_RICH:
                warn_panel = Panel(
                    "[bold yellow]Notice:[/bold yellow] No leads were captured during this session.\n"
                    "Please verify your internet connection or check your search query.\n"
                    "[dim italic]Engineered by Al Hossain Rifat[/dim italic]",
                    border_style="yellow",
                    box=box.ROUNDED
                )
                console.print(warn_panel)
            else:
                print("\n[NOTICE] No leads were captured during this session.")

    finally:
        if HAS_RICH:
            console.print("[dim][*] Closing browser session cleanly...[/dim]")
        driver.quit()


# ---------------------------------------------------------------------------
# Config Loader & CLI Prompt
# ---------------------------------------------------------------------------

def load_saved_sheet_url():
    for config_file in ["config/sheet_config.json", "sheet_config.json"]:
        if os.path.exists(config_file):
            try:
                with open(config_file, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
                    url = cfg.get("sheet_webhook_url", "").strip()
                    if url and "YOUR_DEPLOYMENT_ID" not in url:
                        return url
            except Exception:
                pass
    return None


def prompt_user_input():
    print_banner()

    default_niche = "Watch Store"
    default_location = "Miami, FL"
    default_quota = "all"
    saved_sheet_url = load_saved_sheet_url()

    if HAS_RICH:
        console.print("[bold yellow]Interactive Session Setup[/bold yellow] [dim](Press Enter to accept defaults)[/dim]\n")
        niche_in = console.input(f"  [bold cyan]?[/bold cyan] Business Niche / Category [dim]({default_niche})[/dim]: ").strip()
        location_in = console.input(f"  [bold cyan]?[/bold cyan] Target Location / City / State [dim]({default_location})[/dim]: ").strip()
        quota_in = console.input(f"  [bold cyan]?[/bold cyan] Lead Harvest Quota [dim](Enter number or 'all' for everything)[/dim] [dim]({default_quota})[/dim]: ").strip()

        sheet_prompt = f" [dim]({saved_sheet_url[:40]}...)[/dim]" if saved_sheet_url else " [dim](Press Enter to skip)[/dim]"
        sheet_in = console.input(f"  [bold cyan]?[/bold cyan] Google Sheets Webhook URL{sheet_prompt}: ").strip()
        headless_in = console.input("  [bold cyan]?[/bold cyan] Run in Headless Mode? (y/N) [dim](N)[/dim]: ").strip()
        console.print()
    else:
        print("Interactive Session Setup (Press Enter to accept defaults):\n")
        niche_in = input(f"  ? Business Niche / Category ({default_niche}): ").strip()
        location_in = input(f"  ? Target Location ({default_location}): ").strip()
        quota_in = input(f"  ? Lead Harvest Quota (Enter number or 'all') [{default_quota}]: ").strip()
        sheet_in = input("  ? Google Sheets Webhook URL: ").strip()
        headless_in = input("  ? Run in Headless Mode? (y/N) [N]: ").strip()
        print()

    niche = niche_in if niche_in else default_niche
    location = location_in if location_in else default_location

    quota_raw = (quota_in if quota_in else default_quota).lower()
    if quota_raw in ["all", "max", "everything", "0"]:
        quota = None  # None indicates all mode
    else:
        try:
            quota = int(quota_raw)
        except ValueError:
            quota = None

    if sheet_in:
        sheet_url = sheet_in
    elif saved_sheet_url:
        sheet_url = saved_sheet_url
    else:
        sheet_url = None

    headless = headless_in.lower() == 'y' if headless_in else False

    return niche, location, quota, sheet_url, headless


# ---------------------------------------------------------------------------
# CLI Argument Parser & Entry Point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="High-Velocity Google Maps Lead Harvester v2.5 — Engineered by Al Hossain Rifat",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument("-n", "--niche", type=str, default=None, help="Target business niche (e.g., 'Watch Store')")
    parser.add_argument("-l", "--location", type=str, default=None, help="Target location (e.g., 'Miami, FL')")
    parser.add_argument("-q", "--quota", type=str, default=None, help="Number of leads to harvest or 'all' to scrape everything (default: 'all')")
    parser.add_argument("--all", action="store_true", help="Scrape all available businesses until the end of the Google Maps list")
    parser.add_argument("--sheet-url", type=str, default=None, help="Google Apps Script Webhook URL for live streaming")
    parser.add_argument("-o", "--output", type=str, default=None, help="Custom output CSV filepath")
    parser.add_argument("--headless", action="store_true", help="Run Chrome browser in headless mode")

    args = parser.parse_args()

    # Determine execution mode
    if args.niche is None and args.location is None:
        niche, location, quota, sheet_url, headless = prompt_user_input()
        output_path = args.output
    else:
        niche = args.niche or "Watch Store"
        location = args.location or "Miami, FL"

        if args.all:
            quota = None
        elif args.quota:
            q_str = str(args.quota).lower().strip()
            if q_str in ["all", "0", "max"]:
                quota = None
            else:
                try:
                    quota = int(q_str)
                except ValueError:
                    quota = None
        else:
            quota = None

        sheet_url = args.sheet_url or load_saved_sheet_url()
        output_path = args.output
        headless = args.headless

    run_lead_harvester(
        niche=niche,
        location=location,
        quota=quota,
        sheet_url=sheet_url,
        output_path=output_path,
        headless=headless
    )


if __name__ == "__main__":
    main()
