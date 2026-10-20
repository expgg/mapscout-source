# 📊 Google Sheets Setup Guide — Google Maps Lead Harvester

Follow this quick 2-minute guide to connect your Google Maps scraper directly to Google Sheets for real-time dashboard generation.

---

## ⚡ 1. Open Google Apps Script
1. Open your web browser and go to [script.google.com](https://script.google.com/).
2. Click **New project** (top-left).
3. Name your project: `Google Maps Lead Harvester`.

---

## 📋 2. Paste the Script Code
1. Erase any placeholder code inside the `Code.gs` editor.
2. Open [`google_sheets/code.gs`](../google_sheets/code.gs) from this repository, copy the entire contents, and paste it into `Code.gs`.
3. Press `Ctrl + S` to save the project.

---

## 🚀 3. Deploy as a Web App
1. Click the blue **Deploy** button (top-right) and select **New deployment**.
2. Click the gear icon ⚙️ next to *"Select type"* and choose **Web app**.
3. Configure the settings:
   * **Description**: `Google Maps Live Stream v1.0`
   * **Execute as**: `Me (your-email@gmail.com)`
   * **Who has access**: **`Anyone`** *(Essential so your Python script can post data securely)*.
4. Click **Deploy**.
5. Grant permissions if prompted by Google:
   * Click **Review permissions**.
   * Choose your Google account.
   * Click **Advanced** -> **Go to Google Maps Lead Harvester (unsafe)**.
   * Click **Allow**.
6. Copy the generated **Web app URL** (starts with `https://script.google.com/macros/s/.../exec`).

---

## ⚙️ 4. Link the Webhook in the Scraper
You have two simple ways to use your Webhook URL:

### Option A: Save Permanently in Config
Create `config/sheet_config.json` with your URL:
```json
{
  "sheet_webhook_url": "https://script.google.com/macros/s/YOUR_DEPLOYMENT_ID/exec"
}
```

### Option B: Paste into Interactive CLI Prompt
When you launch `LAUNCH_SCRAPER.bat` or `python main.py`, the interactive prompt will ask:
```text
Google Sheets Webhook URL [optional, press Enter to skip]:
```
Paste your Webhook URL, and the bot will immediately spin up a new Google Sheet for that session and stream rows in live!
