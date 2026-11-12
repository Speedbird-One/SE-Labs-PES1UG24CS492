import json
import math
import re

TRACKING_CODE = re.compile(r"([A-Za-z])([0-9]{1,6})")


def _to_positive_finite(value, name):
    # bool is a subclass of int, but True/False are not measurements.
    if isinstance(value, bool) or not isinstance(value, (int, float, str)):
        raise ValueError(f"{name} must be a number, got {type(value).__name__}")
    try:
        number = float(value)
    except (ValueError, OverflowError):
        raise ValueError(f"{name} is not a valid number: {value!r}") from None
    if not math.isfinite(number) or number <= 0:
        raise ValueError(f"{name} must be a positive, finite number, got {value!r}")
    return number


def calculate_dimensional_weight(dimensions_str):
    if not isinstance(dimensions_str, str):
        raise ValueError("Dimensions must be a string like '20x30x10'")
    dims = dimensions_str.strip().lower().split('x')
    if len(dims) != 3:
        raise ValueError(f"Expected exactly 3 dimensions (LxWxH), got {len(dims)}")
    length, width, height = (_to_positive_finite(d, name) for d, name in zip(dims, ("Length", "Width", "Height")))
    weight = (length * width * height) / 5000.0
    if not math.isfinite(weight):
        raise ValueError("Dimensions are too large")
    return round(weight, 2)


def format_tracking_label(raw_code):
    if not isinstance(raw_code, str):
        raise ValueError("Tracking code must be a string like 'E123'")
    # One ASCII letter followed by 1-6 ASCII digits. [0-9] (not \d) rejects
    # Unicode digits such as '١' that int() would otherwise accept.
    match = TRACKING_CODE.fullmatch(raw_code.strip())
    if not match:
        raise ValueError(f"Tracking code must be one letter followed by 1-6 digits, got {raw_code!r}")
    prefix, digits = match.groups()
    return f"{prefix.upper()}-{int(digits):06d}"


def parse_package_manifest(json_payload):
    if not isinstance(json_payload, (str, bytes, bytearray)):
        raise ValueError("Manifest must be a JSON string")
    try:
        data = json.loads(json_payload)
    except (ValueError, RecursionError) as e:  # JSONDecodeError and UnicodeDecodeError are ValueErrors
        raise ValueError(f"Manifest is not valid JSON: {e}") from None
    if not isinstance(data, dict):
        raise ValueError("Manifest must be a JSON object")
    if "weight" not in data:
        raise ValueError("Manifest has no 'weight' field")
    weight = data["weight"]
    if isinstance(weight, str):
        raise ValueError("Manifest 'weight' must be a JSON number, not a string")
    return _to_positive_finite(weight, "Weight")


def main():
    print("==== Running calculate_dimensional_weight ====")
    dims_input = input("Enter dimensions LxWxH in cm (e.g. 20x30x10): ")
    try:
        dim_weight = calculate_dimensional_weight(dims_input)
        print("Dimensional Weight (kg):", dim_weight)
    except ValueError as e:
        print("Invalid dimensions:", e)

    print("\n==== Running format_tracking_label ====")
    code_input = input("Enter raw code (e.g. E123): ")
    try:
        label = format_tracking_label(code_input)
        print("Formatted Label:", label)
    except ValueError as e:
        print("Invalid tracking code:", e)

    print("\n==== Running parse_package_manifest ====")
    json_input = input('Enter manifest JSON (e.g. {"weight": 12.5}): ')
    try:
        weight = parse_package_manifest(json_input)
        print("Manifest Weight:", weight)
    except ValueError as e:
        print("Invalid manifest:", e)

if __name__ == "__main__":
    main()
