"""
MapScout v2.5 — Google Sheets Webhook Synchronizer
Handles live lead streaming and quality hierarchy batch overwriting via Google Apps Script.
"""

import requests
from modules.ui import HAS_RICH, console


def check_webhook_status(sheet_url: str):
    """Verifies that the Google Apps Script Webhook is deployed and responsive."""
    if not sheet_url:
        return
    try:
        r = requests.get(sheet_url, timeout=12)
        if r.status_code == 200:
            if HAS_RICH:
                console.print("  [bold green][✓][/bold green] Google Sheets Webhook is [bold green]ONLINE[/bold green] & connected.\n")
            else:
                print("  [✓] Google Sheets Webhook is ONLINE & connected.\n")
    except Exception as e:
        if HAS_RICH:
            console.print(f"  [bold yellow][!][/bold yellow] Webhook status check notice: [dim]{e}[/dim]\n")
        else:
            print(f"  [!] Webhook status check notice: {e}\n")


def sync_to_google_sheet(sheet_url: str, rows: list, topic: str, sheet_id: str = None, mode: str = "append"):
    """
    Sends harvested leads payload to Google Sheets Apps Script Webhook.
    Modes:
      - 'append': streams single row or batch to the sheet
      - 'replace': rewrites the data rows with sorted quality hierarchy
    """
    if not sheet_url:
        return sheet_id, None
    try:
        payload = {
            "action": "sync",
            "topic": topic,
            "sheet_id": sheet_id,
            "mode": mode,
            "rows": rows
        }
        res = requests.post(sheet_url, json=payload, timeout=35)
        if res.status_code == 200:
            data = res.json()
            if data.get("status") == "success":
                return data.get("sheet_id"), data.get("sheet_url")
    except Exception:
        pass
    return sheet_id, None
