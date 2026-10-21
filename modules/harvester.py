"""
MapScout v2.5 — Lead Harvesting Orchestration Engine
Coordinates browser automation, real-time extraction, crawling, streaming, and export.
"""

import os
import time
import re
import urllib.parse
import pandas as pd
from seleniumbase import Driver
from selenium.webdriver.common.by import By

from modules.config import get_profile_dir, get_csv_dir
from modules.ui import (
    print_banner,
    print_config_panel,
    create_progress_table,
    print_lead_row,
    print_summary_panel,
    HAS_RICH,
    console
)
from modules.cursor import inject_visual_cursor, move_cursor_to
from modules.extractor import normalize_name, is_social_url, is_aggregator_url, compute_quality_score
from modules.crawler import crawl_website_http, resolve_aggregator_landing_page
from modules.sheets import check_webhook_status, sync_to_google_sheet
from modules.maps import (
    JS_PARSE_LIST_CARDS,
    JS_PURGE_DOM,
    JS_CLICK_CARD,
    JS_POLL_DETAILS,
    is_end_of_feed,
    scroll_feed,
    restore_feed_if_stuck
)


def run_lead_harvester(
    niche: str,
    location: str,
    quota: int = 20,
    sheet_url: str = None,
    output_path: str = None,
    headless: bool = False
):
    """
    Main lead harvesting pipeline.
    """
    print_banner()

    is_all_mode = (quota is None or quota <= 0)
    quota_display = "ALL Available Businesses (End of List)" if is_all_mode else f"{quota} businesses"

    query_term = f"{niche} in {location}"
    safe_topic = "".join([c if c.isalnum() else "-" for c in query_term]).strip("-").lower()
    while "--" in safe_topic:
        safe_topic = safe_topic.replace("--", "-")

    csv_dir = get_csv_dir()

    if not output_path:
        count_suffix = "all" if is_all_mode else str(quota)
        output_path = os.path.join(csv_dir, f"{safe_topic}-{count_suffix}-leads.csv")
    elif not os.path.isabs(output_path) and not os.path.dirname(output_path):
        output_path = os.path.join(csv_dir, output_path)

    print_config_panel(niche, location, quota_display, sheet_url, output_path)
    check_webhook_status(sheet_url)

    harvested_leads = []
    seen_place_keys = set()
    active_sheet_id = None
    active_sheet_url = None

    profile_dir = get_profile_dir()
    if HAS_RICH:
        console.print("[dim][*] Launching High-Velocity Browser Engine...[/dim]")
    else:
        print("[*] Launching High-Velocity Browser Engine...")

    driver = Driver(uc=True, headless=headless, user_data_dir=profile_dir, block_images=True)

    try:
        try:
            driver.maximize_window()
        except Exception:
            try:
                driver.set_window_size(1600, 1000)
            except Exception:
                pass

        search_encoded = urllib.parse.quote_plus(query_term)
        maps_url = f"https://www.google.com/maps/search/{search_encoded}?hl=en"

        if HAS_RICH:
            console.print(f"  [dim][*] Navigating to Google Maps search:[/dim] [cyan]{query_term}[/cyan]")
        else:
            print(f"  [*] Navigating to Google Maps search: {query_term}")

        driver.get(maps_url)
        time.sleep(3.2)
        try:
            driver.execute_script("document.body.style.zoom = '85%';")
        except Exception:
            pass
        inject_visual_cursor(driver)

        # Handle consent modal if present
        try:
            consent_btns = driver.find_elements(By.CSS_SELECTOR, "form[action*='consent'] button, button[aria-label*='Accept all']")
            if consent_btns:
                move_cursor_to(driver, consent_btns[0], click=True)
                consent_btns[0].click()
                time.sleep(1.2)
        except Exception:
            pass

        # Initialize Google Sheets session
        if sheet_url:
            if HAS_RICH:
                console.print("  [dim][*] Initializing executive Google Sheet directory on Drive...[/dim]")
            active_sheet_id, active_sheet_url = sync_to_google_sheet(
                sheet_url,
                rows=[],
                topic=f"{niche.title()} in {location.title()}",
                mode="append"
            )
            if active_sheet_url:
                if HAS_RICH:
                    console.print(f"  [bold green][✓][/bold green] Google Sheet Active: [bold cyan underline]{active_sheet_url}[/bold cyan underline]\n")
                else:
                    print(f"  [✓] Google Sheet Active: {active_sheet_url}\n")

        # Set up Rich progress table
        create_progress_table(niche, location)

        stuck_scroll_count = 0
        lead_index = 0

        while True:
            # Check quota exit condition
            if not is_all_mode and len(harvested_leads) >= quota:
                break

            # Parse visible cards in the feed
            try:
                cards = driver.execute_script(JS_PARSE_LIST_CARDS) or []
            except Exception:
                cards = []

            unvisited = [c for c in cards if c.get("name") and c["name"].strip() not in seen_place_keys]

            # If no unvisited cards in current view, scroll feed or check end of results
            if not unvisited:
                if is_end_of_feed(driver):
                    if HAS_RICH:
                        console.print("\n  [bold green][✓] Reached the end of Google Maps results for this search.[/bold green]\n")
                    else:
                        print("\n  [✓] Reached the end of Google Maps results for this search.\n")
                    break

                scroll_feed(driver)
                stuck_scroll_count += 1
                if stuck_scroll_count >= 6:
                    if HAS_RICH:
                        console.print("\n  [dim][*] No more new business cards found. Completing session...[/dim]\n")
                    else:
                        print("\n  [*] No more new business cards found. Completing session...\n")
                    break
                continue

            stuck_scroll_count = 0
            card_info = unvisited[0]
            b_name = card_info["name"].replace("Sponsored", "").replace("", "").strip()
            seen_place_keys.add(card_info["name"].strip())
            lead_index += 1

            try:
                target_name = b_name
                target_href = card_info.get("maps_url", "")
                norm_target = normalize_name(target_name)

                # 1. Anti-Scramble Safeguard: Purge old authority link and title before clicking
                driver.execute_script(JS_PURGE_DOM)

                # 2. Click the exact card element matching target_href or target_name
                driver.execute_script(JS_CLICK_CARD, target_href, target_name)

                # 3. Synchronized polling (up to 1.1s) — STRICT VERIFICATION: ONLY accept details if title matches THIS exact business!
                b_website = "N/A"
                b_phone = card_info.get("phone") or "N/A"
                b_address = card_info.get("address") or "N/A"
                b_status = card_info.get("status") or "N/A"

                t_poll = time.time()
                first_match_t = None
                while time.time() - t_poll < 1.1:
                    res = driver.execute_script(JS_POLL_DETAILS)
                    cur_title = res.get("title", "")
                    norm_cur = normalize_name(cur_title)

                    is_match = False
                    if norm_cur and norm_target:
                        if norm_target in norm_cur or norm_cur in norm_target:
                            is_match = True
                        else:
                            w_target = target_name.lower().split()
                            w_cur = cur_title.lower().split()
                            if w_target and w_cur and w_target[0] == w_cur[0]:
                                is_match = True

                    if is_match:
                        if first_match_t is None:
                            first_match_t = time.time()

                        if res.get("website"):
                            b_website = res["website"]
                        if res.get("phone"):
                            b_phone = res["phone"]
                        if res.get("address"):
                            b_address = res["address"]
                        if res.get("hours"):
                            b_status = res["hours"]

                        # Fast exit: if website is found, break immediately!
                        if b_website != "N/A":
                            break

                        # If website hasn't mounted yet, allow up to 0.35s after title match
                        if time.time() - first_match_t >= 0.35:
                            break

                    time.sleep(0.05)

                # Clean and sanitize address and phone strings to guarantee single-line cells
                if b_address and b_address != "N/A":
                    b_address = b_address.replace("\r", " ").replace("\n", ", ").strip()
                    b_address = re.sub(r',\s*(?:Closed|Open|Opens|Closes).*$', '', b_address, flags=re.I).strip()
                    b_address = re.sub(r',\s*(?:\+?1[-.\s]?)?\(?[2-9]\d{2}\)?[-.\s]?\d{3}[-.\s]?\d{4}$', '', b_address).strip()
                    while ", ," in b_address:
                        b_address = b_address.replace(", ,", ",")
                    b_address = b_address.strip(" ,")

                if b_phone and b_phone != "N/A":
                    b_phone = b_phone.replace("\r", " ").replace("\n", " ").strip()

                # Laptop safeguard: restore feed if single-pane view
                restore_feed_if_stuck(driver)

                # Format Rating and Review Count
                b_rating_str = card_info.get("rating") or ""
                b_reviews_str = card_info.get("reviews") or ""
                b_rating = float(b_rating_str) if b_rating_str else 0.0
                try:
                    b_reviews = int(b_reviews_str.replace(",", "")) if b_reviews_str else 0
                except Exception:
                    b_reviews = 0

                if b_rating > 0:
                    rating_reviews_disp = f"⭐ {b_rating:.1f}" + (f" ({b_reviews:,})" if b_reviews > 0 else "")
                else:
                    rating_reviews_disp = "-"

                b_category = card_info.get("category") or niche.title()
                place_url = card_info.get("maps_url") or maps_url

                # Website vs Social media vs Aggregator resolution
                social_profiles = []
                final_website = "N/A"
                b_email = "N/A"

                if b_website != "N/A":
                    if is_aggregator_url(b_website):
                        social_profiles.append(b_website)
                        real_site, agg_emails, agg_phones, agg_soc = resolve_aggregator_landing_page(b_website)
                        if real_site:
                            final_website = real_site
                        if agg_emails and b_email == "N/A":
                            b_email = agg_emails[0]
                        if agg_phones and (not b_phone or b_phone == "N/A"):
                            b_phone = agg_phones[0]
                        for s in agg_soc:
                            if s not in social_profiles:
                                social_profiles.append(s)
                    elif is_social_url(b_website):
                        social_profiles.append(b_website)
                        final_website = "N/A"
                    else:
                        final_website = b_website

                # Fast Concurrent Multi-Strategy HTTP Website Crawler (with WHOIS Registry Fallback)
                if final_website != "N/A":
                    found_emails, found_phones, found_soc = crawl_website_http(final_website)
                    if found_emails and b_email == "N/A":
                        b_email = found_emails[0]
                    if (not b_phone or b_phone == "N/A") and found_phones:
                        b_phone = found_phones[0]
                    for s in found_soc:
                        if s not in social_profiles:
                            social_profiles.append(s)

                socials_str = ", ".join(social_profiles[:3]) if social_profiles else "N/A"

                # Calculate Lead Quality Score (0–100)
                quality_score = compute_quality_score(
                    name=b_name,
                    phone=b_phone,
                    email=b_email,
                    website=final_website,
                    rating=b_rating,
                    address=b_address
                )

                lead_record = {
                    "rank": lead_index,
                    "business_name": b_name,
                    "email": b_email if b_email != "N/A" else "NOT FOUND",
                    "phone": b_phone if b_phone != "N/A" else "NOT FOUND",
                    "website": final_website if final_website != "N/A" else "NOT FOUND",
                    "category": b_category,
                    "rating_reviews": rating_reviews_disp if rating_reviews_disp != "-" else "NOT FOUND",
                    "social_profiles": socials_str if socials_str != "N/A" else "NOT FOUND",
                    "maps_url": place_url,
                    "address": b_address if b_address != "N/A" else "NOT FOUND",
                    "quality_score": quality_score,
                    "opening_status": b_status if b_status != "N/A" else "",
                    "rating": b_rating,
                    "reviews": b_reviews
                }

                harvested_leads.append(lead_record)

                # Real-time console table row
                print_lead_row(lead_record)

                # Real-time Google Sheets streaming + Google Cloud Email Recovery
                if sheet_url:
                    try:
                        disc = {}
                        if active_sheet_id:
                            _, _, disc = sync_to_google_sheet(
                                sheet_url,
                                rows=[lead_record],
                                topic=f"{niche.title()} in {location.title()}",
                                sheet_id=active_sheet_id,
                                mode="append",
                                return_emails=True
                            )
                        else:
                            new_id, new_url, disc = sync_to_google_sheet(
                                sheet_url,
                                rows=[lead_record],
                                topic=f"{niche.title()} in {location.title()}",
                                sheet_id=None,
                                mode="append",
                                return_emails=True
                            )
                            if new_id:
                                active_sheet_id = new_id
                                active_sheet_url = new_url

                        # If Google Cloud's whitelisted IP recovered an email that was blocked locally:
                        if disc and b_name in disc:
                            cloud_email = disc[b_name]
                            lead_record["email"] = cloud_email
                            lead_record["quality_score"] = compute_quality_score(
                                name=b_name,
                                phone=b_phone,
                                email=cloud_email,
                                website=final_website,
                                rating=b_rating,
                                address=b_address
                            )
                            if HAS_RICH:
                                console.print(f"    [bold green]☁️ Google Cloud Recovered Email:[/bold green] [bold cyan]{cloud_email}[/bold cyan] [dim](Score: {lead_record['quality_score']})[/dim]")
                            else:
                                print(f"    [CLOUD RECOVERED] {b_name} -> {cloud_email}")

                    except Exception:
                        pass

            except Exception:
                continue

        # Post-Processing: Quality Hierarchy Sorting
        if harvested_leads:
            harvested_leads.sort(key=lambda x: (x["quality_score"], x.get("reviews", 0)), reverse=True)

            for i, r in enumerate(harvested_leads, start=1):
                r["rank"] = i

            # Overwrite final Google Sheet with sorted quality hierarchy
            if sheet_url:
                if HAS_RICH:
                    console.print("  [dim][*] Applying Quality Hierarchy Sorting to Google Sheet dashboard...[/dim]")
                final_id, final_url = sync_to_google_sheet(
                    sheet_url,
                    rows=harvested_leads,
                    topic=f"{niche.title()} in {location.title()}",
                    sheet_id=active_sheet_id,
                    mode="replace" if active_sheet_id else "append"
                )
                if final_url:
                    active_sheet_url = final_url
                if final_id:
                    active_sheet_id = final_id

            # Final Export to CSV
            df = pd.DataFrame(harvested_leads)

            rename_map = {
                "rank": "#",
                "business_name": "Business Name",
                "email": "Email Address",
                "phone": "Phone Number",
                "website": "Website",
                "category": "Category",
                "rating_reviews": "Rating & Reviews",
                "social_profiles": "Social Profiles",
                "maps_url": "Google Maps Link",
                "address": "Full Address",
                "quality_score": "Lead Quality Score"
            }
            ordered_cols = [
                "#", "Business Name", "Email Address", "Phone Number", "Website",
                "Category", "Rating & Reviews", "Social Profiles", "Google Maps Link",
                "Full Address", "Lead Quality Score"
            ]

            export_df = df.rename(columns=rename_map)
            export_cols = [c for c in ordered_cols if c in export_df.columns]
            export_df = export_df[export_cols]

            export_df.to_csv(output_path, index=False, encoding="utf-8-sig")

            print_summary_panel(harvested_leads, output_path, active_sheet_url)

        else:
            if HAS_RICH:
                from rich.panel import Panel
                from rich import box
                warn_panel = Panel(
                    "[bold yellow]Notice:[/bold yellow] No leads were captured during this session.\n"
                    "Please verify your internet connection or check your search query.\n"
                    "[dim italic]Engineered by Al Hossain Rifat[/dim italic]",
                    border_style="yellow",
                    box=box.ROUNDED
                )
                console.print(warn_panel)
            else:
                print("\n[NOTICE] No leads were captured during this session.")

    finally:
        if HAS_RICH:
            console.print("[dim][*] Closing browser session cleanly...[/dim]")
        driver.quit()

        # Keep root folder spotless by isolating any seleniumbase downloaded_files into junk_files
        try:
            if os.path.exists("./downloaded_files"):
                import shutil
                shutil.rmtree("./downloaded_files", ignore_errors=True)
        except Exception:
            pass
