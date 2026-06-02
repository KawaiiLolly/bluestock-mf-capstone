"""
    data_ingestion.py
"""

from pathlib import Path
import pandas as pd
import requests

SCHEMES = {
    125497: "HDFC_Top100_Direct",
    119551: "SBI_Bluechip_Direct",
    120503: "ICICI_Bluechip_Direct",
    118632: "Nippon_LargeCap_Direct",
    119092: "Axis_Bluechip_Direct",
    120841: "Kotak_Bluechip_Direct",
}

RAW_DIR = Path("../data/raw")
RAW_DIR.mkdir(parents=True, exist_ok=True)

for code, name in SCHEMES.items():

    try:
        url = f"https://api.mfapi.in/mf/{code}"

        response = requests.get(url, timeout=15)
        response.raise_for_status()
        
        payload = response.json()

        if "data" not in payload:
            print(f"No NAV data found for {name}")
            continue

        df = pd.DataFrame(payload["data"])
        output_file = RAW_DIR / f"nav_{code}_{name}.csv"
        df.to_csv(output_file, index=False)
        print(f"Saved {output_file.name} ({len(df):,} rows)")

    except Exception as e:
        print(f"Failed {name}: {e}")

print("\nNAV fetch completed.")