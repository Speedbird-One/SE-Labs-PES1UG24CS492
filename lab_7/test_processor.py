import json
import math
import re

from hypothesis import given, settings, strategies as st
from processor import calculate_dimensional_weight, format_tracking_label, parse_package_manifest

# Contract used by every test: a function either returns a sensible value, or
# rejects bad input with a ValueError. Any other exception is a crash (a bug).

LABEL_FORMAT = re.compile(r"[A-Z]-[0-9]{6}")


def _is_valid_weight(value):
    return isinstance(value, float) and math.isfinite(value) and value >= 0


# ---- calculate_dimensional_weight ----

@settings(max_examples=500)
@given(st.text() | st.none())
def test_calculate_dimensional_weight_no_crash(s):
    try:
        result = calculate_dimensional_weight(s)
    except ValueError:
        return
    except Exception as e:
        assert False, f"calculate_dimensional_weight({s!r}) crashed with {type(e).__name__}: {e}"
    assert _is_valid_weight(result), f"calculate_dimensional_weight({s!r}) returned {result!r}"


@settings(max_examples=500)
@given(st.lists(st.floats(), min_size=1, max_size=5))
def test_calculate_dimensional_weight_structured(dims):
    # Near-valid input such as "20.0x-3.5x1e+200": only exactly three positive,
    # finite dimensions with a finite volume should be accepted.
    s = "x".join(str(d) for d in dims)
    valid = len(dims) == 3 and all(math.isfinite(d) and d > 0 for d in dims)
    volume = dims[0] * dims[1] * dims[2] if valid else None
    valid = valid and math.isfinite(volume)
    try:
        result = calculate_dimensional_weight(s)
    except ValueError:
        assert not valid, f"calculate_dimensional_weight({s!r}) rejected valid dimensions"
        return
    except Exception as e:
        assert False, f"calculate_dimensional_weight({s!r}) crashed with {type(e).__name__}: {e}"
    assert valid, f"calculate_dimensional_weight({s!r}) accepted invalid dimensions, returned {result!r}"
    assert result == round(volume / 5000.0, 2)


# ---- format_tracking_label ----

@settings(max_examples=500)
@given(st.text() | st.none())
def test_format_tracking_label_safe(s):
    try:
        label = format_tracking_label(s)
    except ValueError:
        return
    except Exception as e:
        assert False, f"format_tracking_label({s!r}) crashed with {type(e).__name__}: {e}"
    assert LABEL_FORMAT.fullmatch(label), f"format_tracking_label({s!r}) returned malformed label {label!r}"


@settings(max_examples=500)
@given(st.characters(), st.integers())
def test_format_tracking_label_structured(prefix, number):
    # Near-valid input such as "E-42", "ß123" or "E12345678": only one ASCII
    # letter followed by a number that fits in six digits should be accepted.
    raw = f"{prefix}{number}"
    valid = prefix.isascii() and prefix.isalpha() and 0 <= number <= 999999
    try:
        label = format_tracking_label(raw)
    except ValueError:
        assert not valid, f"format_tracking_label({raw!r}) rejected a valid code"
        return
    except Exception as e:
        assert False, f"format_tracking_label({raw!r}) crashed with {type(e).__name__}: {e}"
    assert valid, f"format_tracking_label({raw!r}) accepted an invalid code, returned {label!r}"
    assert label == f"{prefix.upper()}-{number:06d}"


# ---- parse_package_manifest ----

json_values = st.recursive(
    st.none() | st.booleans() | st.integers() | st.floats() | st.text(),
    lambda children: st.lists(children) | st.dictionaries(st.text(), children),
    max_leaves=5,
)


@settings(max_examples=500)
@given(st.text() | st.none())
def test_parse_package_manifest_safe(s):
    try:
        weight = parse_package_manifest(s)
    except ValueError:
        return
    except Exception as e:
        assert False, f"parse_package_manifest({s!r}) crashed with {type(e).__name__}: {e}"
    assert _is_valid_weight(weight), f"parse_package_manifest({s!r}) returned {weight!r}"


@settings(max_examples=500)
@given(json_values)
def test_parse_package_manifest_structured(weight_value):
    # Well-formed JSON whose "weight" can be any JSON value (null, true, "12",
    # NaN, 0, -3, 10**400, [1], ...): only a finite, positive number is valid.
    payload = json.dumps({"weight": weight_value})
    try:
        valid = (
            isinstance(weight_value, (int, float))
            and not isinstance(weight_value, bool)
            and math.isfinite(float(weight_value))
            and weight_value > 0
        )
    except OverflowError:  # an int too large to be a float
        valid = False
    try:
        weight = parse_package_manifest(payload)
    except ValueError:
        assert not valid, f"parse_package_manifest({payload!r}) rejected a valid weight"
        return
    except Exception as e:
        assert False, f"parse_package_manifest({payload!r}) crashed with {type(e).__name__}: {e}"
    assert valid, f"parse_package_manifest({payload!r}) accepted an invalid weight, returned {weight!r}"
    assert weight == float(weight_value)


@given(json_values)
def test_parse_package_manifest_non_object_payload(value):
    # A manifest must be a JSON object with a "weight" key.
    if isinstance(value, dict) and "weight" in value:
        return
    payload = json.dumps(value)
    try:
        parse_package_manifest(payload)
    except ValueError:
        return
    except Exception as e:
        assert False, f"parse_package_manifest({payload!r}) crashed with {type(e).__name__}: {e}"
    assert False, f"parse_package_manifest({payload!r}) accepted a payload without a weight"
