"""
MapScout v2.5 — Dual-Engine Website Spider
High-speed concurrent HTTP spider + dynamic secondary browser tab fallback for JavaScript/SPA sites.
"""

import time
import urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
from bs4 import BeautifulSoup
from selenium.common.exceptions import TimeoutException

from modules.extractor import (
    is_valid_email,
    clean_phone_number,
    is_social_url,
    is_aggregator_url,
    extract_clean_domain,
    lookup_domain_whois,
    extract_from_html_content
)


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
    discovered_contact_anchors = []
    discovered_about_anchors = []

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

                # Step 2: Discover internal contact/policy anchors from homepage navigation
                soup = BeautifulSoup(resp.text, 'html.parser')
                contact_keywords = ['contact', 'reach', 'touch', 'support', 'help']
                about_keywords = ['about', 'team', 'staff', 'story', 'who-we-are']

                for a in soup.find_all('a', href=True):
                    href = a['href'].strip()
                    full_url = urllib.parse.urljoin(base_url, href).split('#')[0]
                    target_netloc = urllib.parse.urlparse(full_url).netloc.lower().replace("www.", "")
                    if target_netloc == base_domain and full_url != base_url:
                        hl = full_url.lower()
                        text = a.text.lower()
                        if any(k in hl or k in text for k in contact_keywords):
                            if full_url not in discovered_contact_anchors:
                                discovered_contact_anchors.append(full_url)
                        elif any(k in hl or k in text for k in about_keywords):
                            if full_url not in discovered_about_anchors:
                                discovered_about_anchors.append(full_url)

    except Exception:
        pass

    # Common standard probe paths as fallback
    standard_probes = [
        urllib.parse.urljoin(base_url, p) for p in [
            "/contact", "/contact-us", "/about", "/about-us", "/pages/contact", "/contactus"
        ]
    ]

    # Prioritize: Verified Contact Nav Links -> Verified About Links -> Fallback Probes
    urls_to_crawl = []
    for u in discovered_contact_anchors + discovered_about_anchors + standard_probes:
        if u not in urls_to_crawl and u != base_url:
            urls_to_crawl.append(u)

    urls_to_crawl = urls_to_crawl[:8]

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
        with ThreadPoolExecutor(max_workers=6) as executor:
            future_to_url = {executor.submit(fetch_subpage, u): u for u in urls_to_crawl}
            try:
                for future in as_completed(future_to_url, timeout=5.0):
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

    # Step 4: WHOIS Registry Fallback
    # If no email was discovered on the website pages, query RDAP registry for registrant email
    if not discovered_emails:
        try:
            clean_dom = extract_clean_domain(base_url)
            if clean_dom:
                whois_em = lookup_domain_whois(clean_dom)
                if whois_em:
                    discovered_emails.add(whois_em)
        except Exception:
            pass

    return list(discovered_emails), list(discovered_phones), list(discovered_socials)


def resolve_aggregator_landing_page(aggregator_url: str):
    """
    Resolves link-in-bio aggregators (Linktree, Beacons.ai, Taplink, Bio.link).
    Extracts direct emails, social channels, and the actual business domain website.
    Returns: (real_website_url or None, emails_list, phones_list, socials_list)
    """
    real_website = None
    emails = set()
    phones = set()
    socials = set()

    if not aggregator_url or not aggregator_url.startswith("http"):
        return None, list(emails), list(phones), list(socials)

    http_headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
    }

    try:
        r = requests.get(aggregator_url, headers=http_headers, timeout=(3.0, 4.0), verify=False)
        if r.status_code == 200:
            em, ph, soc = extract_from_html_content(r.text, aggregator_url)
            emails.update(em)
            phones.update(ph)
            socials.update(soc)

            soup = BeautifulSoup(r.text, "html.parser")
            for a in soup.find_all("a", href=True):
                href = a["href"].strip()
                if not href.startswith("http"):
                    continue
                hl = href.lower()
                # Check if this link is a genuine business website (not social media, not linktree itself)
                if not is_social_url(href) and not is_aggregator_url(href):
                    if not any(j in hl for j in ["apple.com", "spotify.com", "google.com", "terms", "privacy", "cookie", "login", "signup", "report", "pricing"]):
                        real_website = href.split("?")[0].rstrip("/")
                        break
    except Exception:
        pass

    return real_website, list(emails), list(phones), list(socials)


DOM_EXTRACT_JS = r"""
function extractWebsiteDom() {
    let emails = [];
    let phones = [];
    let socials = [];
    let contactLinks = [];

    // 1. Mailto links (with URL decoding)
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

    // 3. Socials & contact links - comprehensive DOM scan across all links and data attributes
    document.querySelectorAll('a[href], [data-href], [data-url]').forEach(el => {
        try {
            let h = el.getAttribute('href') || el.getAttribute('data-href') || el.getAttribute('data-url') || '';
            if (!h || h.startsWith('javascript:') || h.startsWith('#')) return;
            let fullH = h;
            try {
                fullH = new URL(h, window.location.href).href;
            } catch(ex) {}
            let hl = fullH.toLowerCase();

            // Explicit LinkedIn link detection (company, school, showcase, in, personal profiles)
            if (hl.includes('linkedin.com/')) {
                if (!hl.includes('/sharing') && !hl.includes('/sharearticle') && !hl.includes('/share') && !hl.includes('/intent')) {
                    socials.push(fullH.split('?')[0]);
                }
            }
            // Explicit Facebook link detection
            else if (hl.includes('facebook.com/') || hl.includes('fb.com/')) {
                if (!hl.includes('/sharer') && !hl.includes('/share') && !hl.includes('/intent') && !hl.includes('/dialog')) {
                    socials.push(fullH.split('?')[0]);
                }
            }
            // Other major socials
            else if (hl.includes('instagram.com/') || hl.includes('twitter.com/') || hl.includes('x.com/') || hl.includes('youtube.com/')) {
                if (!hl.includes('/share') && !hl.includes('/intent') && !hl.includes('.jpg') && !hl.includes('.png')) {
                    socials.push(fullH.split('?')[0]);
                }
            }

            // Internal Subpages for Contact, About, Team, Leadership, Connect
            if (hl.includes('contact') || hl.includes('about') || hl.includes('support') || hl.includes('reach') || hl.includes('team') || hl.includes('connect')) {
                if (fullH.startsWith('http') && fullH.includes(window.location.hostname) && !contactLinks.includes(fullH) && fullH !== window.location.href) {
                    contactLinks.push(fullH);
                }
            }
        } catch(e) {}
    });

    // 4. Cloudflare email protection tags (<span class="__cf_email__" data-cfemail="...">)
    document.querySelectorAll('[data-cfemail]').forEach(el => {
        try {
            let hex = el.getAttribute('data-cfemail');
            if (hex) {
                let r = parseInt(hex.substr(0, 2), 16);
                let email = '';
                for (let n = 2; n < hex.length; n += 2) {
                    email += String.fromCharCode(parseInt(hex.substr(n, 2), 16) ^ r);
                }
                if (email && email.includes('@')) emails.push(email);
            }
        } catch(e) {}
    });

    // 5. Inner text regex for emails & phones
    let bodyText = document.body ? document.body.innerText : '';
    let matches = bodyText.match(/[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+/g) || [];
    matches.forEach(e => emails.push(e));

    // Bangladeshi & international mobile number regex in body text
    let bdPhones = bodyText.match(/(?:\+?880\s?|0)(1[3-9]\d{2}[-\s]?\d{6})\b/g) || [];
    bdPhones.forEach(p => phones.push(p.trim()));

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
    Physical browser window inspection for dynamic React/Vue/SPA sites and Cloudflare bypass.
    Opens a new browser tab, executes Cloudflare verification if challenged,
    extracts contact data from homepage and internal subpages (Contact/About),
    safely closes the tab and returns focus to main_window.
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

        driver.set_page_load_timeout(8.0)

        try:
            driver.get(base_url)
        except TimeoutException:
            try:
                driver.execute_script("window.stop();")
            except Exception:
                pass

        time.sleep(1.2)

        # Detect Cloudflare Turnstile / Challenge and invoke UC mode bypass
        try:
            page_text = (driver.page_source or "").lower()
            if "cloudflare" in page_text and any(k in page_text for k in ["turnstile", "challenge", "verify you are human", "just a moment", "cf-wrapper"]):
                try:
                    driver.uc_gui_handle_cf()
                except Exception:
                    pass
                time.sleep(2.0)
        except Exception:
            pass

        # 1. Primary DOM extraction from homepage
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

        # Fallback to BeautifulSoup on raw outerHTML
        raw_html = dom_data.get("html") or ""
        if raw_html:
            em2, ph2, soc2 = extract_from_html_content(raw_html, base_url)
            discovered_emails.update(em2)
            discovered_phones.update(ph2)
            discovered_socials.update(soc2)

        # 2. Check if Email or LinkedIn is still missing: deep dive into Contact / About subpages
        has_linkedin = any("linkedin.com" in s.lower() for s in discovered_socials)
        has_facebook = any("facebook.com" in s.lower() or "fb.com" in s.lower() for s in discovered_socials)
        contact_links = dom_data.get("contactLinks", [])

        if (not discovered_emails or not has_linkedin or not has_facebook) and contact_links:
            for subpage_url in contact_links[:2]:
                try:
                    driver.get(subpage_url)
                except TimeoutException:
                    try:
                        driver.execute_script("window.stop();")
                    except Exception:
                        pass
                time.sleep(1.0)

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

                sub_html = sub_dom.get("html") or ""
                if sub_html:
                    em3, ph3, soc3 = extract_from_html_content(sub_html, subpage_url)
                    discovered_emails.update(em3)
                    discovered_phones.update(ph3)
                    discovered_socials.update(soc3)

                # If both email and linkedin are found, we don't need to check further subpages
                if discovered_emails and any("linkedin.com" in s.lower() for s in discovered_socials):
                    break

    except Exception:
        pass
    finally:
        try:
            if opened_tab and opened_tab in driver.window_handles and opened_tab != main_window:
                driver.switch_to.window(opened_tab)
                driver.close()
        except Exception:
            pass
        try:
            if main_window in driver.window_handles:
                driver.switch_to.window(main_window)
            elif driver.window_handles:
                driver.switch_to.window(driver.window_handles[0])
            driver.set_page_load_timeout(30)
        except Exception:
            pass

    return list(discovered_emails), list(discovered_phones), list(discovered_socials)
