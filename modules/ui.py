"""
MapScout v2.5 — Terminal UI & Interaction Engine
Rich styling, interactive session configuration, and progress presentation.
"""

import sys
from modules.config import load_saved_sheet_url

# Rich console styling
try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.text import Text
    from rich import box
    console = Console(file=sys.stdout, legacy_windows=False, force_terminal=True, safe_box=True)
    HAS_RICH = True
except ImportError:
    HAS_RICH = False
    console = None


def print_banner():
    if HAS_RICH:
        console.print()
        console.print("[bold cyan]✦ MapScout[/bold cyan] [dim]v2.5[/dim]")
        console.print("[dim]Autonomous High-Velocity Google Maps Lead Harvester & B2B Engine[/dim]")
        console.print("[italic yellow]Engineered by Al Hossain Rifat[/italic yellow]\n")
    else:
        print("\n* MapScout v2.5")
        print("Autonomous High-Velocity Google Maps Lead Harvester & B2B Engine")
        print("Engineered by Al Hossain Rifat\n")


def print_config_panel(niche: str, location: str, quota_display: str, sheet_url: str, output_path: str):
    if HAS_RICH:
        grid = Table.grid(expand=True, padding=(0, 2))
        grid.add_column(style="bold cyan", justify="left")
        grid.add_column(style="white", justify="left")
        grid.add_column(style="bold cyan", justify="left")
        grid.add_column(style="white", justify="left")

        grid.add_row("Niche / Category:", f"[yellow]{niche}[/yellow]", "Target Geo:", f"[green]{location}[/green]")
        grid.add_row("Harvest Quota:", f"[magenta]{quota_display}[/magenta]", "Website Crawler:", "[green]Active (Dual-Engine)[/green]")
        webhook_status = "[green]Connected (Live Stream)[/green]" if sheet_url else "[dim]Disabled (Local CSV)[/dim]"
        grid.add_row("Google Sheets:", webhook_status, "Output File:", f"[dim]{output_path}[/dim]")

        p = Panel(grid, title="[bold cyan] ACTIVE HARVEST PARAMETERS [/bold cyan]", border_style="cyan", box=box.ROUNDED)
        console.print(p)
        console.print()
    else:
        print("-" * 65)
        print(f"Niche: {niche} | Location: {location}")
        print(f"Quota: {quota_display} | Web Crawler: Active")
        print(f"Google Sheets: {'Connected' if sheet_url else 'Disabled'}")
        print(f"Output File: {output_path}")
        print("-" * 65 + "\n")


def create_progress_table(niche: str, location: str):
    if HAS_RICH:
        table = Table(
            title=f"Market Lead Directory — {niche.title()} in {location.title()}",
            caption="✦ High-Velocity Google Maps Harvester v2.5 • Engineered by Al Hossain Rifat ✦",
            border_style="blue",
            box=box.ROUNDED,
            header_style="bold cyan"
        )
        table.add_column("#", style="bold dim", width=4, justify="center")
        table.add_column("Business Name", style="bold white", width=25)
        table.add_column("Email Address", style="bold green", width=24)
        table.add_column("Phone Number", style="green", width=16)
        table.add_column("Website", style="cyan", width=20)
        table.add_column("Category", style="yellow", width=16)
        table.add_column("Rating & Reviews", style="red", justify="center", width=14)
        table.add_column("Score", style="bold red", justify="center", width=7)
        console.print(table)
        console.print()


def print_lead_row(lead_record: dict):
    lead_index = lead_record["rank"]
    b_name = lead_record["business_name"]
    b_email = lead_record["email"]
    b_phone = lead_record["phone"]
    final_website = lead_record["website"]
    b_category = lead_record["category"]
    rating_reviews_disp = lead_record["rating_reviews"]
    quality_score = lead_record["quality_score"]

    if HAS_RICH:
        phone_disp = b_phone if b_phone != "NOT FOUND" else "[red]NOT FOUND[/red]"
        email_disp = f"[bold green]{b_email}[/bold green]" if b_email != "NOT FOUND" else "[red]NOT FOUND[/red]"
        web_disp = (final_website.replace("https://", "").replace("http://", "").replace("www.", "").split("/")[0][:18]) if final_website != "NOT FOUND" else "[red]NOT FOUND[/red]"

        console.print(
            f"  [bold cyan]#{lead_index:02d}[/bold cyan]  "
            f"[bold white]{b_name[:24]:<24}[/bold white]  "
            f"{email_disp:<24}  "
            f"[white]{phone_disp:<16}[/white]  "
            f"[cyan]{web_disp:<18}[/cyan]  "
            f"[yellow]{b_category[:14]:<14}[/yellow]  "
            f"{rating_reviews_disp:<14}  "
            f"[bold red]{quality_score:3d}[/bold red]"
        )
    else:
        print(f"  #{lead_index:02d} | {b_name} | Email: {b_email} | Phone: {b_phone} | Score: {quality_score}")


def print_summary_panel(harvested_leads: list, output_path: str, active_sheet_url: str = None):
    emails_count = sum(1 for x in harvested_leads if x.get("email") and x.get("email") != "NOT FOUND")
    phones_count = sum(1 for x in harvested_leads if x.get("phone") and x.get("phone") != "NOT FOUND")
    avg_score = round(sum(x["quality_score"] for x in harvested_leads) / max(1, len(harvested_leads)), 1)

    if HAS_RICH:
        console.print()
        sheet_line = f"\n[bold white]Live Google Sheet Dashboard:[/bold white] [bold cyan underline]{active_sheet_url}[/bold cyan underline]" if active_sheet_url else ""
        summary = Panel(
            f"[bold green]✔ Lead Generation Complete![/bold green] Successfully harvested [bold cyan]{len(harvested_leads)}[/bold cyan] verified leads.\n"
            f"✉️ [bold white]Emails Discovered:[/bold white] [bold green]{emails_count}[/bold green] | "
            f"📞 [bold white]Phones Verified:[/bold white] [bold green]{phones_count}[/bold green] | "
            f"⭐ [bold white]Avg Quality Score:[/bold white] [bold red]{avg_score}/100[/bold red]\n"
            f"[bold white]Export File:[/bold white] [underline yellow]{output_path}[/underline yellow]{sheet_line}\n"
            f"[dim italic]Engineered by Al Hossain Rifat[/dim italic]",
            border_style="green",
            box=box.ROUNDED
        )
        console.print(summary)
    else:
        print(f"\n[COMPLETE] Successfully harvested {len(harvested_leads)} leads into {output_path}")
        print(f"Emails: {emails_count} | Phones: {phones_count} | Avg Quality Score: {avg_score}/100")
        if active_sheet_url:
            print(f"[LIVE SHEET] {active_sheet_url}")
        print("Engineered by Al Hossain Rifat\n")


def print_notice(message: str, is_warning: bool = False):
    if HAS_RICH:
        style = "yellow" if is_warning else "green"
        console.print(f"  [bold {style}][*][/bold {style}] {message}")
    else:
        prefix = "[!]" if is_warning else "[*]"
        print(f"  {prefix} {message}")


def prompt_user_input():
    print_banner()

    default_niche = "Watch Store"
    default_location = "Miami, FL"
    default_quota = "all"
    saved_sheet_url = load_saved_sheet_url()

    if HAS_RICH:
        console.print("[bold yellow]Interactive Session Setup[/bold yellow] [dim](Press Enter to accept defaults)[/dim]\n")
        niche_in = console.input(f"  [bold cyan]?[/bold cyan] Business Niche / Category [dim]({default_niche})[/dim]: ").strip()
        location_in = console.input(f"  [bold cyan]?[/bold cyan] Target Location / City / State [dim]({default_location})[/dim]: ").strip()
        quota_in = console.input(f"  [bold cyan]?[/bold cyan] Lead Harvest Quota [dim](Enter number or 'all' for everything)[/dim] [dim]({default_quota})[/dim]: ").strip()

        sheet_prompt = f" [dim]({saved_sheet_url[:40]}...)[/dim]" if saved_sheet_url else " [dim](Press Enter to skip)[/dim]"
        sheet_in = console.input(f"  [bold cyan]?[/bold cyan] Google Sheets Webhook URL{sheet_prompt}: ").strip()
        headless_in = console.input("  [bold cyan]?[/bold cyan] Run in Headless Mode? (y/N) [dim](N)[/dim]: ").strip()
        console.print()
    else:
        print("Interactive Session Setup (Press Enter to accept defaults):\n")
        niche_in = input(f"  ? Business Niche / Category ({default_niche}): ").strip()
        location_in = input(f"  ? Target Location ({default_location}): ").strip()
        quota_in = input(f"  ? Lead Harvest Quota (Enter number or 'all') [{default_quota}]: ").strip()
        sheet_in = input("  ? Google Sheets Webhook URL: ").strip()
        headless_in = input("  ? Run in Headless Mode? (y/N) [N]: ").strip()
        print()

    niche = niche_in if niche_in else default_niche
    location = location_in if location_in else default_location

    quota_raw = (quota_in if quota_in else default_quota).lower()
    if quota_raw in ["all", "max", "everything", "0"]:
        quota = None  # None indicates all mode
    else:
        try:
            quota = int(quota_raw)
        except ValueError:
            quota = None

    if sheet_in:
        sheet_url = sheet_in
    elif saved_sheet_url:
        sheet_url = saved_sheet_url
    else:
        sheet_url = None

    headless = headless_in.lower() == 'y' if headless_in else False

    return niche, location, quota, sheet_url, headless
