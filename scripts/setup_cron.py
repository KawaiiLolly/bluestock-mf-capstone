"""
setup_cron.py
-------------
Usage
-----
    # Install the cron job
    python scripts/setup_cron.py --install

    # Remove the cron job
    python scripts/setup_cron.py --remove

    # Show current crontab (without modifying it)
    python scripts/setup_cron.py --show
"""

import argparse
import subprocess
import sys
from pathlib import Path

BASE_DIR      = Path(__file__).resolve().parent.parent
FETCH_SCRIPT  = BASE_DIR / "scripts" / "live_nav_fetch.py"
LOG_FILE      = BASE_DIR / "logs" / "cron_nav_fetch.log"
PYTHON        = sys.executable         

CRON_TAG = "# bluestock_mf_etl"

CRON_LINE = (
    f"TZ=Asia/Kolkata 0 20 * * 1-5 "
    f"{PYTHON} {FETCH_SCRIPT} >> {LOG_FILE} 2>&1 "
    f"{CRON_TAG}"
)

def get_current_crontab() -> str:
    """Return the current crontab as a string, or '' if empty."""
    result = subprocess.run(
        ["crontab", "-l"],
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        return result.stdout
    return ""


def set_crontab(content: str):
    """Write content as the new crontab."""
    proc = subprocess.run(
        ["crontab", "-"],
        input=content,
        text=True,
        capture_output=True,
    )
    if proc.returncode != 0:
        print(f"[ERROR] crontab write failed: {proc.stderr}")
        sys.exit(1)


def install():
    """Add the ETL cron entry if not already present."""
    current = get_current_crontab()

    if CRON_TAG in current:
        print("Cron job is already installed:")
        for line in current.splitlines():
            if CRON_TAG in line:
                print(f"  {line}")
        print("\nRun with --remove first if you want to update it.")
        return

    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

    new_crontab = current.rstrip("\n") + "\n" + CRON_LINE + "\n"
    set_crontab(new_crontab)

    print("Cron job installed successfully.")
    print("Entry added:")
    print(f"  {CRON_LINE}")
    print("Schedule  : Every weekday (Mon–Fri) at 20:00 IST")
    print(f"Script    : {FETCH_SCRIPT}")
    print(f"Log output: {LOG_FILE}")
    print("To verify:  crontab -l")
    print("To remove:  python scripts/setup_cron.py --remove")


def remove():
    """Remove the ETL cron entry."""
    current = get_current_crontab()

    if CRON_TAG not in current:
        print("No Bluestock ETL cron entry found — nothing to remove.")
        return

    new_lines = [ln for ln in current.splitlines() if CRON_TAG not in ln]
    new_crontab = "\n".join(new_lines) + "\n"
    set_crontab(new_crontab)

    print("Cron job removed.")


def show():
    """Print the current crontab."""
    current = get_current_crontab()
    if current.strip():
        print("Current crontab:")
        print(current)
    else:
        print("No crontab entries found.")


def main():
    parser = argparse.ArgumentParser(
        description="Install or remove the Bluestock MF ETL cron job."
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--install", action="store_true", help="Install the cron job")
    group.add_argument("--remove",  action="store_true", help="Remove the cron job")
    group.add_argument("--show",    action="store_true", help="Show current crontab")
    args = parser.parse_args()

    if args.install:
        install()
    elif args.remove:
        remove()
    elif args.show:
        show()

if __name__ == "__main__":
    main()
