<div align="center">

<img src="docs/assets/hero_banner.jpg" alt="Google Maps Lead Harvester SaaS Hero Banner" width="100%" style="border-radius: 12px; margin-bottom: 20px;" />

# 🗺️ MapScout v2.6
### *Autonomous High-Velocity Google Maps Lead Harvester & B2B Cold Outreach Engine*

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![SeleniumBase](https://img.shields.io/badge/SeleniumBase-UC%20Mode-FF6F00?style=for-the-badge&logo=selenium&logoColor=white)](https://github.com/seleniumbase/SeleniumBase)
[![Google Sheets](https://img.shields.io/badge/Google%20Sheets-Live%20Streaming-34A853?style=for-the-badge&logo=googlesheets&logoColor=white)](https://workspace.google.com/)
[![License](https://img.shields.io/badge/License-MIT-blue?style=for-the-badge)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey?style=for-the-badge)]()

**Automate Google Maps Lead Generation, Contact Enrichment & Outreach Data Harvesting at Scale.**  
*Harvest verified business leads at <0.6s per lead, resolve Linktree/Beacons to real custom domains, rescue emails via ICANN RDAP WHOIS, audit stubborn domains with Screaming Frog SEO Spider, and stream clean datasets live into executive Google Sheets dashboards.*

---

[📦 Releases](#-download--releases-v26) • [Quick Start](#-quick-start-running-from-source) • [4-Tier Contact Engine](#-4-tier-deep-contact-enrichment-engine) • [Key Features](#-features) • [11-Column Architecture](#-11-column-lead-intelligence-architecture) • [Google Sheets Setup](other_files/docs/GOOGLE_SHEETS_SETUP.md) • [Sample Data](samples/sample_leads_intelligence.csv)

---

</div>

## 📌 Overview

**MapScout v2.6** is an enterprise-grade, high-velocity business discovery and contact enrichment engine. Built to eliminate the friction of manual scraping extensions (like *Instant Data Scraper*) and expensive closed-source lead databases, MapScout autonomously searches Google Maps for any niche and geographic target, navigates the results feed, extracts full business contact profiles, and enriches every lead through a multi-tier fallback pipeline.

### 🌟 Key Highlights:
* **⚡ 10x In-Page Speed (<0.6s per lead):** Scrapes and extracts card details directly in-page without slow page reloads.
* **♾️ Unlimited / 'All' Mode:** Harvest every single business in a given location until Google Maps reaches the end of the feed.
* **🛡️ Clean Website & Social Profile Routing:** Prevents Discord, Telegram, WhatsApp, Linktree, and Beacons from polluting the `Website` column; routes them strictly to `Social Profiles`.
* **🌲 Linktree & Beacons.ai Auto-Resolver:** Inspects aggregator landing pages to uncover the merchant's *actual* custom domain website and direct email, promoting the real website to the `Website` column.
* **🌐 RDAP Domain Registry WHOIS Fallback:** When a website conceals its email behind a form, queries official ICANN RDAP registries to rescue registrant emails while filtering out registrar abuse and privacy proxies.
* **🐸 Screaming Frog SEO Spider Deep Rescue:** Optional post-harvest batch audit mode (`--deep-rescue`) that runs headless deep crawls on stubborn domains missing emails.
* **📊 Executive Google Sheets Dashboard:** Live streaming with Google Maps brand colors (`#4285F4`, `#34A853`, `#FBBC04`, `#EA4335`), 4 live KPI scorecards, sticky frozen columns, and embedded formula links.
* **🎯 Lead Quality Scoring (0–100):** Every prospect is mathematically scored based on contact completeness and review strength so outreach teams can prioritize top-tier opportunities.

---

## 📦 Download & Releases (v2.6)

Run MapScout on your PC instantly with or without Python installed:

| Package | Requirements | Best For | Direct Download |
| :--- | :---: | :--- | :---: |
| **⚡ 1-Click Standalone `.exe`** | **None** *(Zero Python Required)* | Instant double-click execution for Windows users | [**⬇️ Download MapScout.exe (v2.6)**](https://github.com/expgg/mapscout-source/releases/latest) |
| **📦 Full Source Code (`.zip`)** | Python 3.10+ | Developers, Linux/macOS users & power customizers | [**⬇️ Download Source Code (.zip)**](https://github.com/expgg/mapscout-source/archive/refs/heads/main.zip) |

### 🚀 Running the 1-Click `.exe` (No Python Required)
1. Head over to [**Releases**](https://github.com/expgg/mapscout-source/releases/latest) and download `MapScout.exe`.
2. Double-click `MapScout.exe` on any Windows PC.
3. The interactive console HUD will launch immediately — no command line or pip packages needed!
4. Follow the on-screen prompts or press **Enter** to accept smart defaults and start harvesting.

---

## ⚡ Quick Start (Running from Source)

### 1. Clone the Repository
```bash
git clone https://github.com/expgg/mapscout-source.git
cd mapscout-source
```

### Option A: 1-Click Launch (Windows)
1. **Launch Directly:** Double-click [`LAUNCH_SCRAPER.bat`](LAUNCH_SCRAPER.bat). It automatically checks Python dependencies and boots the tool!
2. *(Optional)* Run [`scripts/INSTALL_DEPENDENCIES.bat`](scripts/INSTALL_DEPENDENCIES.bat) to manually install or update packages.

### Option B: Terminal Interactive CLI
```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Launch interactive prompt (Press Enter to accept smart defaults or type 'all' for quota!)
python main.py
```

### Option C: Direct Command Line Flags
```bash
# Harvest ALL cake shops in Miami, FL until the end of the Google Maps list
python main.py --niche "Cake Shops" --location "Miami, FL" --all

# Scrape 50 Graphic Design Agencies in Florida with live Google Sheets streaming
python main.py --niche "Graphic Design Agency" --location "Florida" --quota 50

# Silent background execution with Screaming Frog deep rescue enabled
python main.py --niche "Dentists" --location "Chicago, IL" --quota 30 --headless --deep-rescue
```

---

## 🔬 4-Tier Deep Contact Enrichment Engine

MapScout v2.6 features an industry-leading 4-tier enrichment pipeline designed to maximize email and phone capture rates:

```
[Google Maps Business Profile]
            │
            ├── Website slot has Linktree / Beacons?
            │       └── [Tier 2: Aggregator Resolver] uncovers real domain + direct email
            │
            ├── Website slot has Discord / Telegram / Social?
            │       └── Routed cleanly to [Social Profiles] column (Website kept clean)
            │
            ▼
    [Tier 1: High-Velocity HTTP Navigation Spider]
    • Prioritizes internal navigation links (<a href>) with 'contact', 'reach', 'about'
    • Scans anchor text (e.g. "Get In Touch", "Say Hello")
    • Decodes Cloudflare email hex & JSON-LD LocalBusiness Schema
    • Decomposes script/style tags to eliminate phantom email/phone matches
            │
            ├── Email Found? ──► [Lead Enriched ✔]
            │
            ▼ (If email missing)
    [Tier 3: ICANN RDAP Domain Registry WHOIS Fallback]
    • Queries official ICANN RDAP registry (https://rdap.org/domain/{domain})
    • Traverses structured vcardArray & entity trees in ~200ms
    • Discards registrar abuse, privacy proxies, and masked accounts
            │
            ├── Email Found? ──► [Lead Enriched ✔]
            │
            ▼ (Optional Post-Harvest Batch)
    [Tier 4: Screaming Frog SEO Spider Deep Rescue (--deep-rescue)]
    • Headless batch audit across stubborn domains
    • Crawls deep multi-level internal subpages to rescue buried contacts
```

---

## 🚀 Features

### 📊 1. Standalone Google Sheet Per Research Session (Executive Layout v2.6)
Every search session spins up an independent, professionally formatted Google Sheet on your Google Drive:
* **Row 1 Single-Row Master Bar:**
  - **Topic Banner (Left):** High-end Dark Obsidian Slate (`#111827`) displaying `📊 [NICHE] IN [LOCATION]` with crisp white typography.
  - **4 Live KPI Badges with % Metrics (Beside Topic):**
    - 👥 **TOTAL LEADS:** `=COUNTA(A3:A)` (Google Blue `#1967D2` / `#E8F0FE`)
    - ✉️ **EMAILS FOUND %:** `=TEXT(COUNTIF(C3:C, "<>NOT FOUND") / MAX(1, COUNTA(A3:A)), "0.0%")` (Google Green `#137333` / `#E6F4EA`)
    - 📞 **PHONES VERIFIED %:** `=TEXT(COUNTIF(D3:D, "<>NOT FOUND") / MAX(1, COUNTA(A3:A)), "0.0%")` (Google Amber `#B06000` / `#FEF7E0`)
    - ⭐ **TOP RATED %:** `=TEXT(COUNTIF(G3:G, "*5.0*") + COUNTIF(G3:G, "*4.9*") + COUNTIF(G3:G, "*4.8*"), "#") & " (" & TEXT((COUNTIF(G3:G, "*5.0*") + COUNTIF(G3:G, "*4.9*") + COUNTIF(G3:G, "*4.8*")) / MAX(1, COUNTA(A3:A)), "0%") & ")"` (Google Red `#C5221F` / `#FCE8E6`)
* **Row 2 Sticky Frozen Header:** Vibrant Google brand header colors with frozen panes.
* **Sticky Frozen Columns (Cols 1-2):** Both `#` and `Business Name` remain permanently frozen on the left when scrolling horizontally across contact columns.
* **High-Contrast `NOT FOUND` Badges:** Any cell with missing contact data automatically displays **`NOT FOUND`** in bold pure white text (`#FFFFFF`) with an alert red background (`#D93025`).
* **Strict Text Clipping:** Configured with `WrapStrategy.CLIP` so text never spills over adjacent cells.
* **Quality Hierarchy Sorting:** Highest-quality businesses (verified email + phone + site + rating) automatically sorted to the top.

---

### 🖱️ 2. On-Screen Virtual Cursor & Anti-Scramble DOM Engine
* Injects an animated glowing virtual pointer with click ripple animations directly into Chrome.
* High-velocity AJAX side-panel clicks (<0.6s) without slow, jarring page reloads.
* Auto-detects and bypasses Google Maps single-pane layout collapses on laptops and small displays.

---

## 📈 11-Column Lead Intelligence Architecture

Every exported CSV and live Google Sheet is structured with 11 standardized columns in the exact user-specified hierarchy:

| Column | Header | Type | Description |
| :---: | :--- | :---: | :--- |
| `1` | **#** | Integer | Rank / order in session (sorted by Lead Quality Score). |
| `2` | **Business Name** | String | Exact business name from Google Maps. |
| `3` | **Email Address** | String | Discovered business email (verified via 4-tier pipeline). |
| `4` | **Phone Number** | String | Direct phone number from Google Maps or website fallback. |
| `5` | **Website** | URL | Clean business domain (embedded `=HYPERLINK("...", "🌐 domain")`). |
| `6` | **Category** | String | Primary Google Maps business category. |
| `7` | **Rating & Reviews** | String | Merged rating and review count (e.g. `⭐ 4.9 (331)`). |
| `8` | **Social Profiles** | String | Clean social profiles (Instagram, Facebook, LinkedIn, X, Discord). |
| `9` | **Google Maps** | URL | Embedded `=HYPERLINK("...", "📍 Map Link")`. |
| `10` | **Full Address** | String | Clean physical address (Street, City, State/Region, Zip). |
| `11` | **Lead Quality Score** | 0–100 | Contact completeness and review score (sorted highest to lowest). |

---

## ⚙️ CLI Flags & Parameters

| Flag | Long Flag | Default | Description |
| :--- | :--- | :---: | :--- |
| `-n` | `--niche` | Prompt | Target business niche (e.g. `Cake Shops`, `Plumbers`). |
| `-l` | `--location` | Prompt | Target location (e.g. `Miami, FL`, `London, UK`). |
| `-q` | `--quota` | `20` | Total target businesses to harvest or `'all'`. |
| | `--all` | `False` | Scrape all available businesses until the end of the Google Maps list. |
| | `--sheet-url` | `Config` | Google Apps Script Webhook URL for live streaming. |
| `-o` | `--output` | Auto | Custom CSV output filepath. |
| | `--headless` | `False` | Run browser in headless mode. |
| | `--deep-rescue` | `False` | Run Screaming Frog headless batch audit at the end to rescue stubborn missing emails. |

---

## 📂 Project Structure
```
mapscout/
│
├── modules/                            # Modularized functional architecture
│   ├── __init__.py                     # Package initialization & version info
│   ├── config.py                       # Configuration loaders, paths, & constants
│   ├── crawler.py                      # Multi-tier website spider & aggregator resolver
│   ├── cursor.py                       # Virtual cursor injection & visual effects
│   ├── extractor.py                    # Multi-strategy extraction & RDAP WHOIS lookup
│   ├── frog_rescue.py                  # Screaming Frog SEO Spider batch deep rescue engine
│   ├── harvester.py                    # Lead harvesting orchestration engine
│   ├── maps.py                         # Google Maps DOM interaction & navigation
│   ├── sheets.py                       # Live Google Sheets webhook synchronizer
│   └── ui.py                           # Rich console dashboard & interactive setup
│
├── other_files/                        # Secondary project documentation & configs
│   ├── config/                         # Configuration templates & settings
│   ├── docs/                           # Architecture guides & visual assets
│   ├── google_sheets/                  # Google Apps Script Webhook source (code.gs)
│   ├── samples/                        # Sample data exports
│   └── scripts/                        # Dependency installation & build scripts
│
├── junk_files/                         # Automated cache & build directories (git-ignored)
│   ├── chrome_profile/                 # Ephemeral browser profiles
│   ├── downloaded_files/               # Temporary downloads
│   ├── frog_rescue/                    # Ephemeral Screaming Frog crawl workspaces
│   ├── build/                          # PyInstaller build files
│   └── dist/                           # Standalone executables & zip archives
│
├── scrapped_csv/                       # Clean repository for all scraped CSV lead exports
│
├── .gitignore                          # Security rules (excludes personal configs & junk)
├── LAUNCH_SCRAPER.bat                  # 1-click Windows master launcher
├── LICENSE                             # MIT License
├── README.md                           # Master documentation
├── requirements.txt                    # Root Python dependencies
└── main.py                             # Clean, ultra-fast CLI entry point
```

---

## 👤 Author & Contributors

* **Lead Engineer:** [Al Hossain Rifat](https://github.com/expgg) (`@expgg`)
* **Core Contributor:** [`@rifatlovescat`](https://github.com/rifatlovescat) — Dynamic sheet formatting, anti-bot protection & dedicated social columns
* **Disclaimer**: *This project is developed for educational, data analysis, and authorized lead generation purposes.*
