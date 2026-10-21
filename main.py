"""
=============================================================================
                  MapScout v2.5 — Enterprise Edition
        Autonomous High-Velocity Google Maps Lead Harvester & 
                   B2B Cold Outreach Intelligence Engine
                       Engineered by Al Hossain Rifat
=============================================================================
"""

import argparse
from modules.config import load_saved_sheet_url
from modules.ui import prompt_user_input
from modules.harvester import run_lead_harvester


def main():
    parser = argparse.ArgumentParser(
        description="High-Velocity Google Maps Lead Harvester v2.6 — Engineered by Al Hossain Rifat",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument("-n", "--niche", type=str, default=None, help="Target business niche (e.g., 'Watch Store')")
    parser.add_argument("-l", "--location", type=str, default=None, help="Target location (e.g., 'Miami, FL')")
    parser.add_argument("-q", "--quota", type=str, default=None, help="Number of leads to harvest or 'all' to scrape everything (default: 'all')")
    parser.add_argument("--all", action="store_true", help="Scrape all available businesses until the end of the Google Maps list")
    parser.add_argument("--sheet-url", type=str, default=None, help="Google Apps Script Webhook URL for live streaming")
    parser.add_argument("-o", "--output", type=str, default=None, help="Custom output CSV filepath")
    parser.add_argument("--headless", action="store_true", help="Run Chrome browser in headless mode")
    parser.add_argument("--deep-rescue", action="store_true", help="Run Screaming Frog headless batch audit at the end to rescue stubborn missing emails")

    args = parser.parse_args()

    # If no CLI arguments provided, launch interactive setup
    if args.niche is None and args.location is None:
        niche, location, quota, sheet_url, headless, deep_rescue = prompt_user_input()
        output_path = args.output
    else:
        niche = args.niche or "Watch Store"
        location = args.location or "Miami, FL"

        if args.all:
            quota = None
        elif args.quota:
            q_str = str(args.quota).lower().strip()
            if q_str in ["all", "0", "max"]:
                quota = None
            else:
                try:
                    quota = int(q_str)
                except ValueError:
                    quota = None
        else:
            quota = None

        sheet_url = args.sheet_url or load_saved_sheet_url()
        output_path = args.output
        headless = args.headless
        deep_rescue = args.deep_rescue

    run_lead_harvester(
        niche=niche,
        location=location,
        quota=quota,
        sheet_url=sheet_url,
        output_path=output_path,
        headless=headless,
        deep_rescue=deep_rescue
    )


if __name__ == "__main__":
    main()
