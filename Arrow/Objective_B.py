import json
import re

# =========================
# FEATURE EXTRACTORS
# =========================
def extract_cabin(description: str) -> str:
    """
    Extract cabin type from equipment description.

    Returns:
        "EROPS"  -> Enclosed cab / rollover protection
        "OROPS"  -> Open station
        "Unknown" -> Cabin type not detected
    """
    desc = description.upper()

    if "ENCLOSED CAB" in desc or "EROPS" in desc:
        return "EROPS"
    if "OPEN STATION" in desc or "OROPS" in desc:
        return "OROPS"
    return "Unknown"


def extract_drive(description: str) -> str:
    """
    Identify drive / mobility type from description.

    Returns:
        Tracks | AWD | 4WD | Wheels | Unknown
    """
    desc = description.upper()

    if "TRACK" in desc:
        return "Tracks"
    if "AWD" in desc:
        return "AWD"
    if "4WD" in desc or "4X4" in desc:
        return "4WD"
    if "2WD" in desc:
        return "Wheels"

    return "Unknown"


def extract_hours(description: str):
    """
    Extract machine operating hours from free-text description.

    Supports formats such as:
    - "1,250 HRS"
    - "HOURS: 980"
    - "METER READS 4,300"
    - "850 HOURS"

    Returns:
        int hours if found, else None
    """
    desc = description.upper()

    match = re.search(
        r'(?:HRS|HOURS|METER READS:?)\s*[:\-]?\s*(\d{1,3}(?:,\d{3})+|\d+)'
        r'|(\d{1,3}(?:,\d{3})+|\d+)\s*(?:HRS|HOURS)',
        desc
    )

    if match:
        value = match.group(1) or match.group(2)
        return int(value.replace(",", ""))

    return None


# =========================
# OBJECT B CORE
# =========================
def run_object_b(data):
    """
    Object B:
    Enrich inventory records with structured features
    extracted from unstructured description text.

    Input:
        data: List[dict] produced by Object A

    Output:
        Same list with `extracted_features` field added
    """

    for record in data:
        desc = record.get("description", "")

        record["extracted_features"] = {
            "cabin": extract_cabin(desc),
            "drive": extract_drive(desc),
            "hours": extract_hours(desc),
        }

    return data


# =========================
# STANDALONE RUN
# =========================
if __name__ == "__main__":
    with open("object_a_output.json", "r", encoding="utf-8") as f:
        input_data = json.load(f)

    result = run_object_b(input_data)

    with open("object_b_output.json", "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)

    print(f"Object B completed. Records processed: {len(result)}")
