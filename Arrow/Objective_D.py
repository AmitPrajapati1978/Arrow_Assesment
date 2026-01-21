import json

# =========================
# OBJECT D CORE
# =========================
def run_object_d(data, output_path="processed_inventory.json"):
    """
    Object D:
    Final shaping and serialization of processed inventory data.

    This step:
    - Selects only required, business-facing fields
    - Drops intermediate processing fields
    - Ensures consistent output schema
    - Writes final dataset to disk

    Input:
        data: List[dict] output from Object C

    Output:
        List[dict] representing finalized inventory records
        (also persisted to `output_path`)
    """

    final_output = []

    for item in data:
        final_output.append({
            "serial_number": item.get("serial_number"),
            "description": item.get("description"),
            "category": item.get("category"),
            "make": item.get("make"),
            "model": item.get("model"),
            "extracted_features": item.get("extracted_features", {
                "cabin": "Unknown",
                "drive": "Unknown",
                "hours": None
            })
        })

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(final_output, f, indent=2)

    return final_output


# =========================
# STANDALONE RUN
# =========================
if __name__ == "__main__":
    with open("object_c_output.json", "r", encoding="utf-8") as f:
        input_data = json.load(f)

    result = run_object_d(input_data)

    print(f"Object D completed. Final records saved: {len(result)}")
