"""
MapScout v2.5 — Configuration & System Utilities
Handles terminal encodings, path resolution, constants, and settings loaders.
"""

import os
import sys
import io
import re
import json
import urllib3

# Suppress SSL / insecure request warnings from external target websites
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


# ---------------------------------------------------------------------------
# Constants & Validation Patterns
# ---------------------------------------------------------------------------

SOCIAL_DOMAINS = [
    "instagram.com", "facebook.com", "fb.com", "twitter.com",
    "x.com", "tiktok.com", "linkedin.com", "youtube.com",
    "pinterest.com", "yelp.com", "tripadvisor.com",
    "discord.gg", "discord.com", "t.me", "telegram.me",
    "snapchat.com", "wa.me", "whatsapp.com", "spotify.com",
    "threads.net"
]

AGGREGATOR_DOMAINS = [
    "linktr.ee", "linktree.com", "beacons.ai", "beacons.page",
    "bio.link", "taplink.cc", "campsite.bio", "flowcode.com"
]

WHOIS_PRIVACY_TERMS = (
    "abuse@", "noc@", "whoisguard", "privacyprotect", "contactprivacy",
    "domainsbyproxy", "withheldforprivacy", "redacted", "anonymouse",
    "not.disclosed", "gdpr", "superprivacy", "proxy", "markmonitor",
    "namecheap", "godaddy", "registrar", "networksolutions", "cloudflare",
    "pir.org", "icann.org", "verisign", "iana.org", "arin.net", "apnic",
    "ripe.net", "registry", "whoisrequest@"
)

EMAIL_REGEX = re.compile(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+')
PHONE_REGEX = re.compile(r'(?:\+?1[-.\s]?)?\(?([2-9][0-9]{2})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})')

JUNK_EXTS = (
    '.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp', '.ico',
    '.css', '.js', '.woff', '.woff2', '.ttf', '.mp4', '.avi'
)

JUNK_SUBSTRINGS = (
    'sentry.io', 'wixpress.com', 'example.com', 'yourdomain.com',
    'company.com', 'mycompany.com', 'placeholder', 'schema.org',
    'bootstrap', 'cloudflare.com', 'wordpress.org', 'wix-fonts',
    'fancybox', 'react@', 'vue@', 'core-js@', 'babel@', 'webpack@',
    'lodash@', 'fontawesome@', 'jquery@', 'npm@', 'git@', 'test@test',
    'your@email.com', 'email@email.com', 'user@domain.com'
)


# ---------------------------------------------------------------------------
# Path Resolution
# ---------------------------------------------------------------------------

def get_junk_dir() -> str:
    """Returns absolute path to junk_files folder, creating it if needed."""
    d = os.path.abspath("./junk_files")
    os.makedirs(d, exist_ok=True)
    return d


def get_profile_dir() -> str:
    """Returns path for Chrome profile inside junk_files/chrome_profile to keep root clean."""
    p = os.path.join(get_junk_dir(), "chrome_profile")
    os.makedirs(p, exist_ok=True)
    return p


def get_csv_dir() -> str:
    """Returns absolute path to scrapped_csv directory."""
    d = os.path.abspath("./scrapped_csv")
    os.makedirs(d, exist_ok=True)
    return d


def load_saved_sheet_url() -> str:
    """
    Checks configuration locations for saved Google Apps Script webhook URL.
    Scans other_files/config, config, and root.
    """
    candidates = [
        "other_files/config/sheet_config.json",
        "config/sheet_config.json",
        "sheet_config.json"
    ]
    for config_file in candidates:
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


def get_screaming_frog_cli() -> str:
    """Finds path to Screaming Frog SEO Spider CLI executable."""
    candidates = [
        r"X:\APPS\Screaming Frog SEO Spider\ScreamingFrogSEOSpiderCli.exe",
        r"C:\Program Files\Screaming Frog SEO Spider\ScreamingFrogSEOSpiderCli.exe",
        r"C:\Program Files (x86)\Screaming Frog SEO Spider\ScreamingFrogSEOSpiderCli.exe",
    ]
    for c in candidates:
        if os.path.isfile(c):
            return c
    return None
