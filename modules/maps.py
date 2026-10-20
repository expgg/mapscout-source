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

JS_PURGE_DOM = """
let auth = document.querySelector('a[data-item-id="authority"]');
if (auth) auth.remove();
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
"""


# ---------------------------------------------------------------------------
# Helper Functions
# ---------------------------------------------------------------------------

def is_end_of_feed(driver) -> bool:
    """Checks whether the feed container displays the 'reached the end of list' indicator."""
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
    """Smoothly scrolls the Google Maps results feed container."""
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
