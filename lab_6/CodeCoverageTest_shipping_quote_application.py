"""Lab 6 - Step 5: tests written to raise LINE coverage of shipping_quote.py to >= 90%.

Each test is aimed at executing previously unexecuted lines. Not every
True/False outcome of every decision is exercised here - that is the
job of BranchCoverageTest_shipping_quote_application.py.
"""
import pytest
from shipping_quote import process_shipments, monitor_container_pressures


def _shipment(packages, mode="ground", **extra):
    shipment = {"manifest_approved": True, "mode": mode, "packages": packages}
    shipment.update(extra)
    return shipment


# Example test case supplied with the handout
def test_single_ground_shipment():
    shipments = [_shipment([{"weight_kg": 10, "is_hazmat": False}], is_fragile=False, express_priority=False)]
    result = process_shipments(shipments, 20.0)
    assert result["total_quote"] == 60.0
    assert result["status"] == "CLEARED"


def test_invalid_input_raises_value_error():
    with pytest.raises(ValueError):
        process_shipments("not a list", 5.0)


def test_unapproved_manifest_is_skipped():
    shipments = [{"manifest_approved": False, "packages": [{"weight_kg": 5}]}]
    assert process_shipments(shipments, 10.0) == {"total_quote": 0.0, "status": "NO_CARGO"}


def test_air_mode_and_heavy_package_and_express():
    # 10 handling + 40kg * (12 * 1.5) = 730, express x1.25 = 912.5
    shipments = [_shipment([{"weight_kg": 40}], mode="air", express_priority=True)]
    result = process_shipments(shipments, 10.0)
    assert result == {"total_quote": 912.5, "status": "CLEARED"}


def test_unknown_mode_is_rejected():
    shipments = [_shipment([{"weight_kg": 5}], mode="sea")]
    assert process_shipments(shipments, 10.0)["status"] == "NO_CARGO"


def test_non_positive_weight_and_hazmat_surcharge():
    # 10 handling + 50 hazmat surcharge; weight 0 package is rejected
    shipments = [_shipment([{"weight_kg": 0}, {"weight_kg": 2, "is_hazmat": True}])]
    assert process_shipments(shipments, 10.0) == {"total_quote": 60.0, "status": "CLEARED"}


def test_more_than_three_rejections_flags_review():
    shipments = [_shipment([{"weight_kg": 0}] * 4)]
    assert process_shipments(shipments, 5.0)["status"] == "FLAGGED_REVIEW"


def test_no_data_pressure_logs():
    assert monitor_container_pressures([]) == "NO_DATA"


def test_leak_detected():
    assert monitor_container_pressures([[15.0, 13.0, 12.0]]) == "LEAK_DETECTED"


def test_stable_pressure():
    assert monitor_container_pressures([[15.0, 14.5]]) == "STABLE"
