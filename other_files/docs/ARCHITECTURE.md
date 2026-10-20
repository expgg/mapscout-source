# 🏛️ MapScout — Architecture & Engineering Specification

This document provides a technical deep-dive into the design, algorithms, and anti-detection mechanisms powering **MapScout: The Autonomous Google Maps Lead Harvester & B2B Cold Outreach Engine**.

---

## 1. High-Level System Architecture

```
[User Input / CLI Flags]
        │
        ▼
[SeleniumBase Undetected Chrome Engine] ───► [Persistent User Profile (chrome_profile/)]
        │                                         ▲
        ▼                                         │
[Virtual Glowing Cursor & Ripple Injection] ──────┘
        │
        ▼
[Target Search URL: google.com/maps/search/...]
        │
        ▼
[Inner Feed Container Scrolling Loop (div[role='feed'])]
        │
        ├─► [Lazy Loading Trigger via Controlled Scroll Deltas]
        └─► [Termination Detector: Quota Hit OR "End of List" Notification]
        │
        ▼
[Card By Card Investigation & Direct Extraction]
        │  • Business Name (Title selector / aria-label)
        │  • Primary Category
        │  • Rating & Review Count
        │  • Verified Phone Number
        │  • Physical Street / City / State Address
        │  • Listed Website URL
        │  • Operational Status (Open / Closed)
        │
        ▼
[Targeted Fallback Evaluator]
        │
   ┌────┴─────────────────────────────────┐
   │ Missing Email or Phone AND Site?     │
   ├───────────────┬──────────────────────┤
   ▼ YES           ▼ NO
[Targeted Web Spider]                [Direct Assembly]
   • Homepage, /contact, /about               │
   • Regex Email + Anti-Junk Filter           │
   • Secondary Phone Regex                    │
   • Social Links (LinkedIn, FB, IG, X)       │
   └───────────────┬──────────────────────────┘
                   ▼
[Lead Quality Score Algorithm (0-100)]
                   │
                   ▼
[Multi-Channel Dispatcher]
   ├─► [Real-Time Rich Terminal HUD Output]
   ├─► [Live Google Sheets Webhook Stream (Row-by-Row)]
   └─► [Session CSV / Excel Data Persister]
```

---

## 2. Stealth Navigation & Feed Scrolling Mechanics

### Anti-Bot Defense
* Google Maps actively tracks abnormal scrolling frequency, automated mouse events, and headless browser signatures.
* To achieve 100% bypass without Cloudflare/Google CAPTCHAs, we use **SeleniumBase UC Mode (Undetected ChromeDriver)** paired with a local persistent Chrome profile directory (`./chrome_profile`).

### Inner Feed Container Navigation
* Unlike traditional web pages where `window.scrollTo()` scrolls the body, Google Maps embeds results inside an independent scrollable layout:
  `div[role='feed']` (or `div.m6QErb.DxyBCb.kA9KIf.dS8AEf`).
* The engine dynamically finds this container and issues micro-scroll commands using JavaScript `element.scrollTop += delta` interspersed with realistic randomized pauses (0.7s – 1.4s) to allow Google Maps to fetch the next batch of places.
* Detection of list termination:
  The crawler scans for the end marker element:
  - `div.HlvSq` containing text: *"You've reached the end of the list."*

---

## 3. Targeted Website Spider & Email Extraction

### Why Selective Crawling?
* Scraping 100 external websites indiscriminately can introduce significant lag, IP throttling, or timeouts.
* **Our approach**: We only spider external websites when high-value contact details (specifically **Email Address** or **Phone Number**) are missing from the primary Google Maps listing.

### Clean Regex & Junk Filtering
Standard regex often catches garbage (e.g. `logo.png`, `user@2x.jpg`, `@sentry.io`, `@wixpress.com`).
Our extraction engine applies strict heuristic sanitization:
1. Regex pattern: `[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}`
2. Blacklist validation:
   - Excludes email endings matching image extensions: `.png`, `.jpg`, `.jpeg`, `.gif`, `.svg`, `.webp`.
   - Excludes known third-party plugin/platform domains: `sentry.io`, `wixpress.com`, `cloudflare.com`, `schema.org`, `domain.com`, `example.com`.
3. Limits spidering strictly to:
   - Homepage (`/`)
   - `/contact`, `/contact-us`, `/get-in-touch`
   - `/about`, `/about-us`

---

## 4. Lead Quality Score (0–100) Formula

Every harvested lead is scored to help outreach teams prioritize top-tier prospects:

| Signal | Weight | Rationale |
|---|:---:|---|
| **Business Name** | +20 | Base verified Google Maps listing entity |
| **Direct Phone Number** | +25 | Instant outreach via cold call or SMS |
| **Verified Email** | +25 | High-converting cold email outreach channel |
| **Live Website** | +15 | Required for SEO auditing and business verification |
| **Rating & Reviews** | +10 | Indicates social proof and business legitimacy |
| **Physical Address** | +5 | Local geographic verification |
| **Total Maximum** | **100** | **Complete Lead Profile** |
