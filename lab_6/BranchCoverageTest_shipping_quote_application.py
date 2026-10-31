"""Lab 6 - Step 7: tests written to raise BRANCH coverage of shipping_quote.py to >= 90%.

Superset of the code-coverage tests, plus tests that drive the decisions
the line-coverage suite never took the other way (fragile hazmat, bad
handling fee, ground heavy parcels, pressure streak resets, etc.).
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


# ---- additional tests for branch coverage ----

def test_negative_handling_fee_raises_value_error():
    with pytest.raises(ValueError):
        process_shipments([], -1.0)


def test_empty_shipments_list_is_no_cargo():
    assert process_shipments([], 10.0) == {"total_quote": 0.0, "status": "NO_CARGO"}


def test_fragile_hazmat_zeroes_shipment_and_stops_processing_packages():
    # Hazmat in a fragile shipment: cost reset to 0, remaining packages ignored.
    shipments = [_shipment([{"weight_kg": 5, "is_hazmat": True}, {"weight_kg": 100}], is_fragile=True)]
    assert process_shipments(shipments, 10.0) == {"total_quote": 0.0, "status": "NO_CARGO"}


def test_fragile_without_hazmat_is_priced_normally():
    shipments = [_shipment([{"weight_kg": 5}], is_fragile=True)]
    assert process_shipments(shipments, 10.0)["total_quote"] == 30.0


def test_ground_heavy_package_uses_surcharge_rate():
    # 10 + 31 * (4 * 1.5) = 196
    shipments = [_shipment([{"weight_kg": 31}])]
    assert process_shipments(shipments, 10.0)["total_quote"] == 196.0


def test_weight_exactly_30_is_not_heavy():
    shipments = [_shipment([{"weight_kg": 30}])]
    assert process_shipments(shipments, 0.0)["total_quote"] == 120.0


def test_air_light_package():
    shipments = [_shipment([{"weight_kg": 2}], mode="air")]
    assert process_shipments(shipments, 1.0)["total_quote"] == 25.0


def test_express_priority_false_has_no_multiplier():
    shipments = [_shipment([{"weight_kg": 10}], express_priority=False)]
    assert process_shipments(shipments, 0.0)["total_quote"] == 40.0


def test_defaults_when_keys_missing():
    # mode defaults to ground, weight defaults to 0 (rejected), manifest default is unapproved
    shipments = [{"manifest_approved": True, "packages": [{}]}, {"packages": [{"weight_kg": 5}]}]
    assert process_shipments(shipments, 7.0) == {"total_quote": 7.0, "status": "CLEARED"}


def test_exactly_three_rejections_is_not_flagged():
    shipments = [_shipment([{"weight_kg": 0}] * 3)]
    assert process_shipments(shipments, 5.0)["status"] == "CLEARED"


def test_flagged_review_still_reports_total():
    shipments = [_shipment([{"weight_kg": 1}, {"weight_kg": 0}, {"weight_kg": 0}, {"weight_kg": 0}, {"weight_kg": 0}])]
    assert process_shipments(shipments, 0.0) == {"total_quote": 4.0, "status": "FLAGGED_REVIEW"}


def test_non_list_shipments_with_valid_fee_raises():
    with pytest.raises(ValueError):
        process_shipments(None, 0.0)


def test_pressure_streak_reset_prevents_leak():
    assert monitor_container_pressures([[13.0, 15.0, 13.0]]) == "STABLE"


def test_pressure_boundary_14_is_not_low():
    assert monitor_container_pressures([[14.0, 14.0]]) == "STABLE"


def test_pressure_leak_found_in_later_container():
    assert monitor_container_pressures([[15.0], [13.0, 13.5]]) == "LEAK_DETECTED"


def test_pressure_streak_does_not_carry_across_containers():
    assert monitor_container_pressures([[13.0], [13.0]]) == "STABLE"


def test_pressure_empty_container_is_stable():
    assert monitor_container_pressures([[]]) == "STABLE"
