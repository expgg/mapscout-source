"""
MapScout v2.5 — Data Extraction, Sanitization & Intelligence Scoring
Handles email & phone extraction, Cloudflare decoding, HTML entity cleaning, and lead scoring.
"""

import re
import html
import json
import urllib.parse
from bs4 import BeautifulSoup
from modules.config import (
    SOCIAL_DOMAINS,
    AGGREGATOR_DOMAINS,
    WHOIS_PRIVACY_TERMS,
    EMAIL_REGEX,
    PHONE_REGEX,
    JUNK_EXTS,
    JUNK_SUBSTRINGS
)


def normalize_name(s: str) -> str:
    """Normalizes business name to alphanumeric lowercase for robust strict comparison."""
    if not s:
        return ""
    return re.sub(r'[^a-zA-Z0-9]', '', str(s)).lower()


def clean_phone_number(raw: str) -> str:
    """Cleans raw string into standard phone formatting."""
    if not raw:
        return ""
    raw_clean = raw.strip()
    if raw_clean.startswith("+") or raw_clean.startswith("01") or "+88" in raw_clean:
        return raw_clean
    digits = re.sub(r'\D', '', raw_clean)
    if len(digits) == 10 and not raw_clean.startswith("0"):
        return f"+1 ({digits[:3]}) {digits[3:6]}-{digits[6:]}"
    elif len(digits) == 11 and digits.startswith("1"):
        return f"+1 ({digits[1:4]}) {digits[4:7]}-{digits[7:]}"
    elif len(digits) >= 7:
        return raw_clean
    return ""


def decode_cf_email(cf_hex: str) -> str:
    """Decodes Cloudflare email protection obfuscated hex string."""
    try:
        r = int(cf_hex[:2], 16)
        return ''.join([chr(int(cf_hex[i:i+2], 16) ^ r) for i in range(2, len(cf_hex), 2)])
    except Exception:
        return ""


def is_valid_email(email: str) -> bool:
    """Rigorous validator ensuring email is legitimate and not code/asset artifacts."""
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


def is_social_url(url: str) -> bool:
    """Determines whether a URL points to a social network profile rather than a primary business website."""
    if not url or url == "N/A":
        return False
    u = url.lower()
    return any(sd in u for sd in SOCIAL_DOMAINS) or any(ad in u for ad in AGGREGATOR_DOMAINS)


def is_aggregator_url(url: str) -> bool:
    """Determines whether a URL points to a link-in-bio aggregator (Linktree, Beacons, etc.)."""
    if not url or url == "N/A":
        return False
    u = url.lower()
    return any(ad in u for ad in AGGREGATOR_DOMAINS)


def extract_clean_domain(url: str) -> str:
    """Extracts base registered domain name from URL (e.g. stores.nordstromrack.com -> nordstromrack.com)."""
    if not url or url == "N/A":
        return ""
    try:
        netloc = urllib.parse.urlparse(url).netloc.lower()
        if ":" in netloc:
            netloc = netloc.split(":")[0]
        netloc = netloc.replace("www.", "")
        parts = netloc.split(".")
        if len(parts) >= 2:
            return ".".join(parts[-2:])
        return netloc
    except Exception:
        return ""


def lookup_domain_whois(domain: str) -> str:
    """
    Queries RDAP public registry to discover registrant email.
    Discards known registrar abuse, privacy proxies, and masked accounts.
    """
    if not domain or "." not in domain or any(s in domain for s in SOCIAL_DOMAINS):
        return ""
    try:
        import requests
        import json
        r = requests.get(
            f"https://rdap.org/domain/{domain}",
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=3.0
        )
        if r.status_code == 200:
            data = r.json()
            candidates = []

            def walk_entities(entities):
                for ent in entities:
                    roles = [str(ro).lower() for ro in ent.get('roles', [])]
                    # Skip top-level registrar and abuse reporting contacts
                    if not any(ro in ('registrar', 'abuse') for ro in roles):
                        vcard = ent.get('vcardArray', [])
                        if len(vcard) > 1 and isinstance(vcard[1], list):
                            for item in vcard[1]:
                                if isinstance(item, list) and len(item) >= 4 and item[0] == 'email':
                                    candidates.append(str(item[3]))
                        ent_str = json.dumps(ent)
                        for em in re.findall(EMAIL_REGEX, ent_str):
                            candidates.append(em)
                    if 'entities' in ent:
                        walk_entities(ent['entities'])

            walk_entities(data.get('entities', []))

            for em in candidates:
                em_clean = em.strip().rstrip(".")
                if is_valid_email(em_clean):
                    em_lower = em_clean.lower()
                    if not any(term in em_lower for term in WHOIS_PRIVACY_TERMS):
                        return em_clean
    except Exception:
        pass
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

            # Social links (excluding share intents and website builder vendor accounts)
            for platform in ['linkedin.com', 'facebook.com', 'fb.com', 'instagram.com', 'twitter.com', 'x.com', 'tiktok.com', 'youtube.com']:
                if platform in hl and not any(k in hl for k in ['share', 'intent', 'cdn', '.jpg', '.png', 'sharer', '/squarespace', '/shopify', '/wix', '/wordpress', '/weebly']):
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

        # Decompose non-visible script, style, svg tags to prevent phantom matches
        for tag in soup(["script", "style", "noscript", "svg"]):
            tag.decompose()
        visible_text = soup.get_text(separator=' ')
    except Exception:
        visible_text = clean_html

    # 4. Normalized Written Obfuscations ("name [at] domain.com" or "name (at) domain.com")
    normalized_text = re.sub(r'\s*(?:\[|\(|\{)at(?:\]|\)|\})\s*', '@', visible_text, flags=re.IGNORECASE)
    normalized_text = re.sub(r'\s*(?:\[|\(|\{)dot(?:\]|\)|\})\s*', '.', normalized_text, flags=re.IGNORECASE)

    # 5. Regex emails
    for match in EMAIL_REGEX.findall(normalized_text):
        if is_valid_email(match):
            emails.add(match.strip().rstrip('.'))

    # 6. Regex phone numbers from visible text (North American and Bangladeshi/International)
    for m in PHONE_REGEX.finditer(visible_text):
        p_str = f"({m.group(1)}) {m.group(2)}-{m.group(3)}"
        phones.add(p_str)

    for m in re.finditer(r'(?:\+?880\s?|0)(1[3-9]\d{2}[-\s]?\d{6})\b', visible_text):
        phones.add(f"+880 {m.group(1)}")

    return emails, phones, socials


def compute_quality_score(name: str, phone: str, email: str, website: str, rating: float, address: str) -> int:
    """Calculates lead score (0–100) based on verified contact channels and completeness."""
    score = 20  # Base score for verified business entity
    if phone and phone != "N/A" and phone != "NOT FOUND":
        score += 25
    if email and email != "N/A" and email != "NOT FOUND":
        score += 25
    if website and website != "N/A" and website != "NOT FOUND":
        score += 15
    if rating and rating > 0:
        score += 10
    if address and address != "N/A" and address != "NOT FOUND":
        score += 5
    return min(100, score)


# ---------------------------------------------------------------------------
# Strict Lead Relevance & Sector Verification Engine
# ---------------------------------------------------------------------------

UNIVERSAL_EXCLUSIONS = [
    "hostel", "dormitory", "dorm", "mess hall", "residential hall",
    "shaheed minar", "minar", "monument", "memorial", "sculpture", "statue",
    "playground", "stadium", "canteen", "cafeteria", "cemetery", "graveyard",
    "mosque", "masjid", "temple", "church", "students' care", "student care"
]

IT_EXCLUDED_KEYWORDS = [
    "barista", "culinary", "chef", "cooking", "baking", "pastry",
    "restaurant", "cafe", "coffee", "catering", "hotel management",
    "welding", "welder", "electrician", "electrical works", "carpenter", "plumbing", "plumber",
    "masonry", "refrigeration", "ac repair", "auto mechanic", "automobile", "driving school",
    "driving training", "motor driving", "driving academy",
    "mobile repair", "mobile servicing", "cell phone repair", "hardware repair", "mobile servicing center",
    "tailoring", "tailor", "sewing", "sewing school", "garments", "fashion design",
    "beautician", "beauty parlour", "parlour", "makeup", "salon", "cosmetology",
    "nursing", "paramedical", "pharmacy", "medical training", "dental", "clinic", "hospital",
    "teachers training", "teacher training", "primary training", "b.ed", "dttti", "ptti",
    "kindergarten", "junior school", "high school", "madrasa", "cadet coaching", "admission coaching",
    "language club", "ielts", "spoken english", "korean language", "japanese language", "german language",
    "music school", "dance academy", "martial art", "karate", "yoga", "gym", "fitness"
]

IT_ACCEPTED_CATEGORIES = {
    "software training institute",
    "computer training school",
    "computer training center",
    "software company",
    "web hosting company",
    "internet marketing service"
}

IT_POSITIVE_REGEX = re.compile(
    r"\b("
    r"it|ict|tech|technology|technologies|software|softtech|coder|coders|coding|code|"
    r"programmer|programming|computer|computers|computing|web|webcoder|developer|developers|development|"
    r"cyber|cybersecurity|network|networking|cisco|ccna|data|ai|digital|multimedia|animation|"
    r"graphic|graphics|ui\/ux|ux|freelanc\w*|outsourcing|bpo|cloud|devops|fullstack|"
    r"frontend|backend|algorithm|algo|byte|bit|creative\s*it|basis|bitm|diit|daffodil|"
    r"bacbon|lead\s*academy|ostad|shikhbe\s*shobai|bohubrihi|interactive\s*cares|codeman\w*|"
    r"eiconik|astrait|uy\s*lab|peoplentech|nexttech|kaizen|nebula|atova"
    r")\b",
    re.IGNORECASE
)

BENGALI_IT_KEYWORDS = ["কম্পিউটার", "আইটি", "সফটওয়্যার", "প্রযুক্তি", "প্রশিক্ষণ"]


def is_lead_relevant(name: str, category: str, niche: str, website: str = "") -> tuple[bool, str]:
    """
    Evaluates whether a candidate business matches the requested niche and is a valid commercial lead,
    filtering out monuments, hostels, cafeterias, and irrelevant vocational fields.
    """
    norm_name = (name or "").lower().strip()
    norm_cat = (category or "").lower().strip()
    norm_niche = (niche or "").lower().strip()
    norm_web = (website or "").lower().strip()

    # 1. Universal Exclusions (Hostels, Monuments, Minars, Cafeterias, Parks)
    combined_text = f"{norm_name} {norm_cat} {norm_web}"
    for ex in UNIVERSAL_EXCLUSIONS:
        if ex in combined_text:
            return False, f"Universal exclusion match: '{ex}'"

    is_it_niche = any(k in norm_niche for k in ["it", "tech", "computer", "software", "coding", "web", "program"])

    if is_it_niche:
        # 2. IT-Specific Exclusions (Vocational trades, non-IT academic, medical, beauty)
        for ex in IT_EXCLUDED_KEYWORDS:
            if ex in combined_text:
                return False, f"Non-IT sector exclusion: '{ex}'"

        # 3. IT-Specific Positive Acceptance
        # Case A: Explicit IT Category
        if norm_cat in IT_ACCEPTED_CATEGORIES:
            return True, f"Direct IT category match: '{norm_cat}'"

        # Case B: Bengali Script IT keywords in name
        if any(b_kw in name for b_kw in BENGALI_IT_KEYWORDS):
            return True, "Bengali IT keyword match in name"

        # Case C: Name matches strong IT regex
        if IT_POSITIVE_REGEX.search(norm_name):
            return True, "IT keyword match in business name"

        # Case D: Website domain matches IT keyword
        if norm_web and norm_web != "n/a" and IT_POSITIVE_REGEX.search(norm_web):
            return True, "IT keyword match in website domain"

        # Case E: Generic training category (e.g. Training center) without ANY IT signal -> REJECT!
        return False, f"Lacks IT domain keywords in name, category, or website (category was '{category or 'unknown'}')"

    return True, "Generic niche match"

