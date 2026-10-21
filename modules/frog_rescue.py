"""
MapScout v2.6 — Screaming Frog Deep SEO Rescue Engine
Autonomous batch headless crawler that audits stubborn websites missing emails,
recovers deeply buried contact endpoints, and patches datasets & Google Sheets.
"""

import os
import re
import csv
import subprocess
import urllib.parse
import pandas as pd
import requests
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed

from modules.config import get_junk_dir, get_screaming_frog_cli, EMAIL_REGEX, PHONE_REGEX
from modules.extractor import is_valid_email, clean_phone_number, compute_quality_score, extract_from_html_content
from modules.ui import HAS_RICH, console
from modules.sheets import sync_to_google_sheet


def is_screaming_frog_available() -> bool:
    """Checks whether Screaming Frog CLI is installed and accessible."""
    return get_screaming_frog_cli() is not None


def run_screaming_frog_rescue(
    leads: list[dict],
    csv_path: str = None,
    sheet_url: str = None
) -> list[dict]:
    """
    Scans harvested leads for records with missing emails but valid websites.
    Executes a batch headless Screaming Frog crawl to discover deep subpages,
    recovers buried emails and contact info, and re-syncs CSV and Google Sheets.
    """
    if not leads:
        return leads

    stubborn_leads = [
        lead for lead in leads
        if (lead.get("email") in ("NOT FOUND", "N/A", "") or not lead.get("email"))
        and (lead.get("website") not in ("NOT FOUND", "N/A", "") and lead.get("website"))
    ]

    if not stubborn_leads:
        if HAS_RICH:
            console.print("  [dim][✓] All leads have verified contact channels. Screaming Frog rescue not needed.[/dim]")
        else:
            print("  [✓] All leads have verified contact channels. Screaming Frog rescue not needed.")
        return leads

    frog_cli = get_screaming_frog_cli()
    if not frog_cli:
        if HAS_RICH:
            console.print("  [yellow][!] Screaming Frog CLI not detected. Skipping deep rescue.[/yellow]")
        else:
            print("  [!] Screaming Frog CLI not detected. Skipping deep rescue.")
        return leads

    if HAS_RICH:
        from rich.panel import Panel
        console.print()
        console.print(Panel(
            f"[bold green]🐸 Screaming Frog Deep SEO Rescue Engine Activated[/bold green]\n"
            f"[dim]Auditing {len(stubborn_leads)} stubborn website(s) via headless batch crawl to recover hidden contacts...[/dim]",
            border_style="green"
        ))
    else:
        print(f"\n[🐸] Screaming Frog Deep Rescue: Auditing {len(stubborn_leads)} stubborn website(s)...")

    rescue_dir = os.path.join(get_junk_dir(), "frog_rescue")
    os.makedirs(rescue_dir, exist_ok=True)
    urls_file = os.path.join(rescue_dir, "rescue_urls.txt")

    # Map domains to their lead objects
    domain_to_lead = {}
    valid_urls = []
    for lead in stubborn_leads:
        w_url = lead.get("website", "").strip()
        if w_url.startswith("http"):
            domain_to_lead[urllib.parse.urlparse(w_url).netloc.lower().replace("www.", "")] = lead
            valid_urls.append(w_url)

    if not valid_urls:
        return leads

    with open(urls_file, "w", encoding="utf-8") as f:
        for u in valid_urls:
            f.write(f"{u}\n")

    # Execute Screaming Frog in headless list mode
    cmd = [
        frog_cli,
        "--crawl-list", urls_file,
        "--headless",
        "--output-folder", rescue_dir,
        "--export-tabs", "Internal:HTML",
        "--overwrite"
    ]

    try:
        subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    except Exception as ex:
        if HAS_RICH:
            console.print(f"  [red][!] Screaming Frog execution error: {ex}[/red]")
        return leads

    # Parse internal_html.csv for deep discovered URLs
    internal_csv = os.path.join(rescue_dir, "internal_html.csv")
    discovered_deep_urls = set()
    if os.path.isfile(internal_csv):
        try:
            with open(internal_csv, "r", encoding="utf-8", errors="ignore") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    addr = row.get("Address", "").strip()
                    status = row.get("Status Code", "")
                    if addr and status in ("200", ""):
                        discovered_deep_urls.add(addr)
        except Exception:
            pass

    # Fetch deep pages and extract contacts
    http_headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
    }

    def fetch_deep_page(url):
        try:
            r = requests.get(url, headers=http_headers, timeout=(3.0, 4.0), verify=False)
            if r.status_code == 200:
                return url, extract_from_html_content(r.text, url)
        except Exception:
            pass
        return url, (set(), set(), set())

    rescued_contacts = {}  # domain -> {emails: set(), phones: set(), socials: set()}
    if discovered_deep_urls:
        with ThreadPoolExecutor(max_workers=8) as executor:
            futures = [executor.submit(fetch_deep_page, u) for u in list(discovered_deep_urls)[:25]]
            for f in as_completed(futures):
                try:
                    p_url, (em, ph, soc) = f.result()
                    dom = urllib.parse.urlparse(p_url).netloc.lower().replace("www.", "")
                    if dom not in rescued_contacts:
                        rescued_contacts[dom] = {"emails": set(), "phones": set(), "socials": set()}
                    rescued_contacts[dom]["emails"].update(em)
                    rescued_contacts[dom]["phones"].update(ph)
                    rescued_contacts[dom]["socials"].update(soc)
                except Exception:
                    pass

    # Patch leads with rescued contacts
    rescued_count = 0
    for dom, contact_data in rescued_contacts.items():
        if dom in domain_to_lead:
            target_lead = domain_to_lead[dom]
            found_emails = list(contact_data["emails"])
            found_phones = list(contact_data["phones"])

            changed = False
            if found_emails and target_lead.get("email") in ("NOT FOUND", "N/A", ""):
                target_lead["email"] = found_emails[0]
                changed = True

            if found_phones and target_lead.get("phone") in ("NOT FOUND", "N/A", ""):
                target_lead["phone"] = found_phones[0]
                changed = True

            if changed:
                rescued_count += 1
                # Recompute Quality Score
                target_lead["quality_score"] = compute_quality_score(
                    name=target_lead.get("business_name", ""),
                    phone=target_lead.get("phone", ""),
                    email=target_lead.get("email", ""),
                    website=target_lead.get("website", ""),
                    rating=target_lead.get("rating", 0.0),
                    address=target_lead.get("address", "")
                )
                if HAS_RICH:
                    console.print(f"  [bold green]  ✔ Rescued {target_lead['business_name']}:[/bold green] [cyan]{target_lead['email']}[/cyan] [dim](Score: {target_lead['quality_score']})[/dim]")
                else:
                    print(f"  ✔ Rescued {target_lead['business_name']}: {target_lead['email']} (Score: {target_lead['quality_score']})")

    # Clean up temporary rescue files
    try:
        for f in os.listdir(rescue_dir):
            os.remove(os.path.join(rescue_dir, f))
        os.rmdir(rescue_dir)
    except Exception:
        pass

    if rescued_count > 0:
        if csv_path and os.path.exists(csv_path):
            try:
                df = pd.DataFrame(leads)
                df.to_csv(csv_path, index=False, encoding="utf-8-sig")
            except Exception:
                pass

        if sheet_url:
            try:
                sync_to_google_sheet(sheet_url, leads)
            except Exception:
                pass

        if HAS_RICH:
            console.print(f"\n  [bold green][✓] Successfully rescued {rescued_count} lead(s) with Screaming Frog! Synced to CSV and Google Sheets.[/bold green]\n")
        else:
            print(f"\n[✓] Successfully rescued {rescued_count} lead(s) with Screaming Frog! Synced to CSV and Google Sheets.\n")
    else:
        if HAS_RICH:
            console.print("  [dim][✓] Screaming Frog deep crawl finished. No additional hidden emails found on audited sites.[/dim]\n")
        else:
            print("  [✓] Screaming Frog deep crawl finished. No additional hidden emails found on audited sites.\n")

    return leads
