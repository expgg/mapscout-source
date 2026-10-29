"""
MapScout v2.5 — Google Maps DOM Interaction & Anti-Scramble Engine
Handles feed parsing, card clicking, DOM purging, and place detail polling.
"""

import time
from selenium.webdriver.common.by import By

# ---------------------------------------------------------------------------
# JavaScript Snippets
# ---------------------------------------------------------------------------

JS_PARSE_LIST_CARDS = """
function parseFeedCards() {
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

        let cardWebsite = '';
        let cardWebEl = c.querySelector('a[data-value*="Website" i], a[aria-label*="Website" i], a.lcr4fd[href^="http"]:not([href*="google.com"])');
        if (cardWebEl && cardWebEl.href) {
            cardWebsite = cardWebEl.href;
            if (cardWebsite.includes('/url?q=')) {
                try {
                    cardWebsite = decodeURIComponent(cardWebsite.split('/url?q=')[1].split('&')[0]);
                } catch(e) {}
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
            maps_url: mapsUrl,
            website: cardWebsite
        });
    });
    return results;
}
return parseFeedCards();
"""

JS_PURGE_DOM = """
let auth = document.querySelector('a[data-item-id="authority"]');
if (auth) auth.remove();
let chips = document.querySelectorAll('a.lcr4fd[aria-label*="website" i]');
chips.forEach(c => c.remove());
let h1 = document.querySelector('h1.DUwDvf');
if (h1) h1.innerText = '';
"""

JS_CLICK_CARD = """
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
"""

JS_POLL_DETAILS = """
let h1 = document.querySelector('h1.DUwDvf');
let curTitle = h1 ? h1.innerText.trim() : '';

// 1. Multi-strategy Website detection in Google Maps pane
let websiteUrl = '';
let auth = document.querySelector('a[data-item-id="authority"]');
if (auth && auth.href && !auth.href.includes('google.com/maps')) {
    websiteUrl = auth.href;
}
if (!websiteUrl) {
    let actionChip = document.querySelector('a.lcr4fd[aria-label*="website" i], a[data-tooltip*="website" i], a[aria-label*="website" i], a[data-value*="Website" i]');
    if (actionChip && actionChip.href && !actionChip.href.includes('google.com/maps')) {
        websiteUrl = actionChip.href;
    }
}
if (!websiteUrl) {
    let allLinks = Array.from(document.querySelectorAll('div[role="main"] a, div.m6QErb a'));
    for (let l of allLinks) {
        let txt = (l.innerText || '').trim().toLowerCase();
        let aria = (l.getAttribute('aria-label') || '').toLowerCase();
        if ((txt.includes('website') || aria.includes('website')) && l.href && !l.href.includes('google.com/maps')) {
            websiteUrl = l.href;
            break;
        }
    }
}
if (websiteUrl && websiteUrl.includes('/url?q=')) {
    try {
        websiteUrl = decodeURIComponent(websiteUrl.split('/url?q=')[1].split('&')[0]);
    } catch(e) {}
}

// 2. Direct Social Media profile detection in Google Maps pane
let gmapsSocials = [];
let paneLinks = document.querySelectorAll('div[role="main"] a, div.m6QErb a');
paneLinks.forEach(a => {
    let h = a.href || '';
    if (!h) return;
    let hl = h.toLowerCase();
    if (hl.includes('facebook.com/') || hl.includes('fb.com/') || hl.includes('linkedin.com/') ||
        hl.includes('instagram.com/') || hl.includes('twitter.com/') || hl.includes('x.com/') ||
        hl.includes('youtube.com/')) {
        if (!hl.includes('/share') && !hl.includes('google.com')) {
            gmapsSocials.push(h);
        }
    }
});

let fullPhone = document.querySelector('button[data-item-id*="phone"]')?.innerText?.trim() || '';
let fullAddr = document.querySelector('button[data-item-id="address"]')?.innerText?.trim() || '';
let hoursEl = document.querySelector("div[data-item-id='oh']");
let hours = hoursEl ? hoursEl.innerText.split('\n')[0].trim() : '';
let catEl = document.querySelector('button[jsaction*="category"], span.DkEaL, button.DkEaL, span[class*="fontBodyMedium"]');
let curCategory = catEl ? catEl.innerText.trim() : '';
return {
    title: curTitle,
    website: websiteUrl,
    phone: fullPhone.replace(/^[\s\ue000-\uf8ff]+/, '').trim(),
    address: fullAddr.replace(/^[\s\ue000-\uf8ff]+/, '').trim(),
    hours: hours,
    category: curCategory,
    socials: gmapsSocials
};
"""


# ---------------------------------------------------------------------------
# Helper Functions & Anti-Bot Protections
# ---------------------------------------------------------------------------

def check_and_handle_google_captcha(driver) -> bool:
    """
    Detects Google Search/Maps 'unusual traffic' block, consent walls, or reCAPTCHA challenge,
    and automatically invokes SeleniumBase UC mode captcha solvers.
    """
    try:
        page_source = (driver.page_source or "").lower()
        title = (driver.title or "").lower()
        current_url = (driver.current_url or "").lower()

        is_blocked = (
            "unusual traffic" in page_source
            or "recaptcha" in page_source
            or "robot" in title
            or "sorry/index" in current_url
            or "before you continue to google" in page_source
        )

        if is_blocked:
            try:
                # 1. Attempt consent click if it's a consent wall
                consent_btns = driver.find_elements(
                    By.CSS_SELECTOR,
                    "button[aria-label*='Accept all' i], form[action*='consent'] button, button#L2AGLb"
                )
                if consent_btns:
                    consent_btns[0].click()
                    time.sleep(2.0)
                    return True

                # 2. SeleniumBase UC GUI captcha solvers for reCAPTCHA / Cloudflare
                if hasattr(driver, "uc_gui_handle_captcha"):
                    driver.uc_gui_handle_captcha()
                elif hasattr(driver, "uc_gui_click_captcha"):
                    driver.uc_gui_click_captcha()
                time.sleep(3.0)
                return True
            except Exception:
                pass
    except Exception:
        pass
    return False


def is_end_of_feed(driver) -> bool:
    """Checks whether the feed container displays the 'reached the end of list' indicator."""
    try:
        # Check text in feed footer and dedicated end-of-list badges
        return bool(driver.execute_script("""
            const feed = document.querySelector('div[role="feed"]');
            if (!feed) return false;
            const text = feed.innerText.toLowerCase();
            return text.includes("reached the end of the list") || 
                   text.includes("no more results") || 
                   text.includes("end of results") ||
                   Boolean(document.querySelector('div.HlvSq, span.HlvSq, div.fontBodySmall.HlvSq'));
        """))
    except Exception:
        pass
    return False


def scroll_feed(driver):
    """
    Smoothly scrolls the Google Maps results feed container to the bottom to trigger next batch,
    with lazy-loading jiggle to force Google's dynamic loader.
    """
    try:
        driver.execute_script("""
            const feed = document.querySelector('div[role="feed"]');
            if (feed) {
                // Jiggle scroll to force Google Maps lazy-load trigger
                feed.scrollTop = feed.scrollHeight - 350;
                setTimeout(() => {
                    feed.scrollTop = feed.scrollHeight;
                }, 120);
            }
        """)
        time.sleep(1.2)
    except Exception:
        pass


def restore_feed_if_stuck(driver):
    """Safeguard for small screens/laptops: clicks Back if detail panel obscured the feed."""
    try:
        driver.execute_script("""
            let feed = document.querySelector('div[role="feed"]');
            if (!feed || window.getComputedStyle(feed).display === 'none') {
                let backBtn = document.querySelector('button[aria-label="Back"], button[jsaction*="back"], button[aria-label*="back" i]');
                if (backBtn) backBtn.click();
            }
        """)
    except Exception:
        pass
