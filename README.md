<div align="center">

<img src="docs/assets/hero_banner.jpg" alt="Google Maps Lead Harvester SaaS Hero Banner" width="100%" style="border-radius: 12px; margin-bottom: 20px;" />

# 🗺️ MapScout v2.5
### *Autonomous High-Velocity Google Maps Lead Harvester & B2B Cold Outreach Engine*

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![SeleniumBase](https://img.shields.io/badge/SeleniumBase-UC%20Mode-FF6F00?style=for-the-badge&logo=selenium&logoColor=white)](https://github.com/seleniumbase/SeleniumBase)
[![Google Sheets](https://img.shields.io/badge/Google%20Sheets-Live%20Streaming-34A853?style=for-the-badge&logo=googlesheets&logoColor=white)](https://workspace.google.com/)
[![License](https://img.shields.io/badge/License-MIT-blue?style=for-the-badge)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey?style=for-the-badge)]()

**Automate Google Maps Lead Generation, Contact Enrichment & Outreach Data Harvesting at Scale.**  
*Harvest hundreds to thousands of verified business leads, crawl official websites for missing emails and social profiles, and stream clean datasets live into auto-generated executive Google Sheets directories.*

---

[📦 Download .exe](#-download--releases-v25) • [Quick Start](#-quick-start-running-from-source) • [Key Features](#-features) • [11-Column Architecture](#-11-column-lead-intelligence-architecture) • [Google Sheets Setup](docs/GOOGLE_SHEETS_SETUP.md) • [Architecture](docs/ARCHITECTURE.md) • [Sample Data](samples/sample_leads_intelligence.csv)

---

</div>

## 📌 Overview

**MapScout v2.5** is an enterprise-grade, high-velocity business discovery and contact enrichment engine. Built to eliminate the friction of manual scraping extensions (like *Instant Data Scraper*) and paid/closed-source email finders, this tool autonomously searches Google Maps for any niche and geographic target, navigates the results feed, extracts full business contact profiles, and intelligently crawls target websites to discover missing emails and social channels.

### 🌟 Why This Exists:
* **⚡ 10x In-Page Speed (<0.6s per lead):** Scrapes and extracts card details directly in-page without full page reloads.
* **♾️ Unlimited / 'All' Mode:** Harvest every single business in a given location until Google Maps reaches the end of the list.
* **🌐 Automated Contact Fallback:** No closed-source email bots required. When an email or phone is missing from Maps, the engine spiders the business's official website (`/`, `/contact`, `/about`) to extract verified emails with zero human intervention.
* **📊 Executive Google Sheets Dashboard:** Formatted with vibrant Google Maps brand colors (`#4285F4`, `#34A853`, `#FBBC04`, `#EA4335`), 4 live KPI scorecards, sticky frozen columns, strict cell text clipping, and embedded `=HYPERLINK("...", "📍 Map Link")` formulas.
* **🖱️ On-Screen Neon Glow Cursor:** Renders an animated glowing cursor directly inside Chrome so you can visually monitor the scraper in real time.
* **🎯 Lead Quality Scoring (0–100):** Every prospect is mathematically scored based on contact completeness so outreach teams can prioritize top-tier opportunities.

---

## 📦 Download & Releases (v2.5)

Run MapScout on your PC instantly with or without Python installed:

| Package | Requirements | Best For | Direct Download |
| :--- | :---: | :--- | :---: |
| **⚡ 1-Click Standalone `.exe`** | **None** *(Zero Python Required)* | Instant double-click execution for Windows users | [**⬇️ Download MapScout.exe (v2.5)**](https://github.com/expgg/mapscout-source/releases/latest) |
| **📦 Full Source Code (`.zip`)** | Python 3.10+ | Developers, Linux/macOS users & power customizers | [**⬇️ Download Source Code (.zip)**](https://github.com/expgg/mapscout-source/archive/refs/heads/main.zip) |

### 🚀 Running the 1-Click `.exe` (No Python Required)
1. Head over to [**Releases**](https://github.com/expgg/mapscout-source/releases/latest) and download `MapScout.exe`.
2. Double-click `MapScout.exe` on any Windows PC.
3. The interactive console HUD will launch immediately — no command line, virtual environment, or pip packages needed!
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
2. *(Optional)* Run [`scripts/INSTALL_DEPENDENCIES.bat`](scripts/INSTALL_DEPENDENCIES.bat) if you wish to manually install or update packages.

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
python main.py --niche "Cake Shops" --location "Miami, FL" --all --enrich

# Scrape 50 Graphic Design Agencies in Florida with live Google Sheets streaming
python main.py --niche "Graphic Design Agency" --location "Florida" --quota 50

# Silent background execution
python main.py --niche "Dentists" --location "Chicago, IL" --quota 30 --headless
```

---

## 🚀 Features

### 📊 1. Standalone Google Sheet Per Research Session (Executive Layout v2.5)
Every search session spins up an independent, professionally formatted Google Sheet on your Google Drive:
* **Row 1 Single-Row Master Bar:**
  - **Topic Banner (Left):** High-end Dark Obsidian Slate (`#111827`) displaying `📊 [NICHE] IN [LOCATION]` with crisp white typography.
  - **4 Live KPI Badges with % Metrics (Beside Topic):**
    - 👥 **TOTAL LEADS:** `=COUNTA(A3:A)` (Google Blue `#1967D2` / `#E8F0FE`)
    - ✉️ **EMAILS FOUND %:** `=TEXT(COUNTIF(C3:C, "<>NOT FOUND") / MAX(1, COUNTA(A3:A)), "0.0%")` (Google Green `#137333` / `#E6F4EA`)
    - 📞 **PHONES VERIFIED %:** `=TEXT(COUNTIF(D3:D, "<>NOT FOUND") / MAX(1, COUNTA(A3:A)), "0.0%")` (Google Amber `#B06000` / `#FEF7E0`)
    - ⭐ **TOP RATED %:** `=TEXT(COUNTIF(G3:G, "*5.0*") + COUNTIF(G3:G, "*4.9*") + COUNTIF(G3:G, "*4.8*"), "#") & " (" & TEXT((COUNTIF(G3:G, "*5.0*") + COUNTIF(G3:G, "*4.9*") + COUNTIF(G3:G, "*4.8*")) / MAX(1, COUNTA(A3:A)), "0%") & ")"` (Google Red `#C5221F` / `#FCE8E6`)
* **Row 2 Sticky Frozen Header:** Vibrant Google brand header colors with frozen panes. Business Name is in Google Blue (`#1A73E8`), creating sharp visual contrast against Row 1.
* **Sticky Frozen Columns (Cols 1-2):** Both `#` and `Business Name` remain permanently frozen on the left when scrolling horizontally to the right across all contact columns!
* **High-Contrast `NOT FOUND` Badges:** Any cell with missing contact data automatically displays **`NOT FOUND`** in bold pure white text (`#FFFFFF`) with an alert red background (`#D93025`), making lead qualification instant!
* **Row 3+ Data Rows:** Top-to-bottom pastel color-coded columns per information type, with embedded `📍 Map Link` and `🌐 Website` formula links.
* **Strict Text Clipping:** Configured with `WrapStrategy.CLIP` so no long text ever spills over adjacent cells!
* **Quality Hierarchy Sorting:** Highest-quality businesses (verified email + phone + site + rating) automatically sorted to the top.

> *For a 2-minute setup guide on connecting your Google Account, read the [Google Sheets Setup Guide](docs/GOOGLE_SHEETS_SETUP.md).*

---

### 🌐 2. Dual-Engine Website Crawler (Always Active by Default)
* **Engine 1 (Fast HTTP Spider):** Rapidly scans homepage and contact subpages with Cloudflare email decoding (`/cdn-cgi/l/email-protection#`).
* **Engine 2 (Dynamic Secondary Chrome Window Fallback):** If email is still missing, triggers a secondary Chrome browser window positioned right beside Google Maps to render client-side JavaScript, SPAs, and dynamic contact pages.
* **Social vs Website Separation:** Instagram and Facebook links are automatically routed to `Social Profiles` and never mistaken for business websites.

---

### 🖱️ 3. On-Screen Virtual Cursor & High-Velocity In-Page Navigation
* Injects an animated glowing virtual pointer with click ripple animations directly into Chrome.
* High-velocity AJAX side-panel clicks (<0.6s) without slow, jarring page reloads.

---

## 📈 11-Column Lead Intelligence Architecture

Every exported CSV and live Google Sheet is structured with 11 standardized columns in the exact user-specified hierarchy:

| Column | Header | Type | Description |
| :---: | :--- | :---: | :--- |
| `1` | **#** | Integer | Rank / order in session. |
| `2` | **Business Name** | String | Exact business name from Google Maps. |
| `3` | **Email Address** | String | Discovered business email (verified via dual-engine spider). |
| `4` | **Phone Number** | String | Direct phone number from Google Maps or website fallback. |
| `5` | **Website** | URL | Embedded `=HYPERLINK("...", "🌐 domain")` link. |
| `6` | **Category** | String | Primary Google Maps business category. |
| `7` | **Rating & Reviews** | String | Merged rating and review count (e.g. `⭐ 4.9 (331)`). |
| `8` | **Social Profiles** | String | Clean social profiles (Instagram, Facebook, LinkedIn, X). |
| `9` | **Google Maps** | URL | Embedded `=HYPERLINK("...", "📍 Map Link")`. |
| `10` | **Full Address** | String | Clean physical address (Street, City, State/Region, Zip). |
| `11` | **Lead Quality Score** | 0–100 | Contact viability score (sorted highest to lowest). |


*(Inspect a sample export in [`samples/sample_leads_intelligence.csv`](samples/sample_leads_intelligence.csv)).*

---

## ⚙️ CLI Flags & Parameters

| Flag | Long Flag | Default | Description |
| :--- | :--- | :---: | :--- |
| `-n` | `--niche` | Prompt | Target business niche (e.g. `Cake Shops`, `Plumbers`). |
| `-l` | `--location` | Prompt | Target location (e.g. `Miami, FL`, `London, UK`). |
| `-q` | `--quota` | `20` | Total target businesses to harvest or `'all'`. |
| | `--all` | `False` | Scrape all available businesses until the end of the Google Maps list. |
| | `--enrich` | `True` | Crawl website for missing email/phone contacts. |
| | `--no-enrich` | `False` | Skip external website crawling (Maps data only). |
| | `--sheet-url` | `Config` | Google Apps Script Webhook URL for live streaming. |
| `-o` | `--output` | Auto | Custom CSV output filepath. |
| | `--headless` | `False` | Run browser in headless mode. |

---

## 📂 Project Structure
```
mapscout/
│
├── config/
│   ├── requirements.txt                # Pinned Python package dependencies
│   ├── sheet_config.example.json       # Template configuration for Google Sheets Webhook
│   └── sheet_config.json               # Local user Google Sheets config (git-ignored)
│
├── docs/
│   ├── assets/                         # SaaS hero banners & visual assets
│   ├── ARCHITECTURE.md                 # Technical deep-dive on feed scrolling & anti-detection
│   └── GOOGLE_SHEETS_SETUP.md          # Step-by-step Google Apps Script setup guide
│
├── google_sheets/
│   └── code.gs                         # Google Apps Script engine for Drive auto-creation
│
├── samples/
│   └── sample_leads_intelligence.csv   # Clean 11-column sample dataset
│
├── scripts/
│   └── INSTALL_DEPENDENCIES.bat        # 1-click package installer
│
├── .gitignore                          # Security rules (excludes browser cookies & personal tokens)
├── LAUNCH_SCRAPER.bat                  # 1-click Windows master launcher
├── LICENSE                             # MIT License
├── README.md                           # Master documentation & visual guide
├── requirements.txt                    # Root Python dependencies
└── main.py                             # High-velocity automation engine & interactive Rich CLI HUD
```

---

## 👤 Author & Credits

**Engineered by:** Al Hossain Rifat  
* **Disclaimer**: *This project is developed for educational, data analysis, and authorized lead generation purposes.*
