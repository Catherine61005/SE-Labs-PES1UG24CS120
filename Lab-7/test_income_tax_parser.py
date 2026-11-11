"""Hypothesis fuzz tests for income_tax_parser.py (Lab 7).

Each of the three functions gets:
  * a "no crash" fuzz test (the handout template: any text or None must not raise),
  * a wider "no crash" test fed with values of *any* type,
  * property tests that check the answer is correct, not just that it exists.
"""
import string

from hypothesis import given, settings, strategies as st

from income_tax_parser import clean_pan, parse_amount, parse_tax_slab

settings.register_profile("lab7", max_examples=300, deadline=None)
settings.load_profile("lab7")

# Anything a caller could hand to the functions: text, None and other types.
ANY_INPUT = st.one_of(
    st.text(), st.none(), st.integers(), st.floats(), st.booleans(),
    st.binary(), st.lists(st.text(), max_size=3),
)

MAX_AMOUNT_DIGITS = 18   # amounts longer than this are rejected by the fixed parser


# ---------------------------------------------------------------- clean_pan
@given(st.text() | st.none())
def test_clean_pan_no_crash(s):
    try:
        clean_pan(s)
    except Exception as e:
        assert False, f"clean_pan crashed with: {e!r}"


@given(ANY_INPUT)
def test_clean_pan_no_crash_any_type(s):
    try:
        clean_pan(s)
    except Exception as e:
        assert False, f"clean_pan crashed with: {e!r}"


@given(st.text() | st.none())
def test_clean_pan_output_is_clean(s):
    """Result is always a string, upper-case, with no whitespace left in it."""
    out = clean_pan(s)
    assert isinstance(out, str)
    assert out == out.upper()
    assert not any(ch.isspace() for ch in out)


@given(st.text(alphabet=string.ascii_letters + string.digits + " \t\n"))
def test_clean_pan_removes_whitespace_and_uppercases(s):
    expected = "".join(ch for ch in s if not ch.isspace()).upper()
    assert clean_pan(s) == expected


@given(st.text())
def test_clean_pan_is_idempotent(s):
    assert clean_pan(clean_pan(s)) == clean_pan(s)


# ------------------------------------------------------------- parse_amount
@given(st.text() | st.none())
def test_parse_amount_no_crash(s):
    try:
        parse_amount(s)
    except Exception as e:
        assert False, f"parse_amount crashed with: {e!r}"


@given(ANY_INPUT)
def test_parse_amount_no_crash_any_type(s):
    try:
        parse_amount(s)
    except Exception as e:
        assert False, f"parse_amount crashed with: {e!r}"


@given(ANY_INPUT)
def test_parse_amount_result_is_none_or_non_negative_int(s):
    result = parse_amount(s)
    assert result is None or (isinstance(result, int) and result >= 0)


@given(st.integers(min_value=0, max_value=10**15))
def test_parse_amount_round_trip(n):
    assert parse_amount(str(n)) == n
    assert parse_amount(f"Rs {n:,}") == n
    assert parse_amount(f"rs{n:,}") == n


@given(st.integers(max_value=-1))
def test_parse_amount_rejects_negative(n):
    assert parse_amount(str(n)) is None


@given(st.text(alphabet=st.characters(categories=["Nd"], exclude_characters="0123456789"),
               min_size=1))
def test_parse_amount_rejects_non_ascii_digits(s):
    # e.g. Arabic-Indic digits: int() would accept them, an amount should not
    assert parse_amount(s) is None


@given(st.integers(min_value=MAX_AMOUNT_DIGITS + 1, max_value=6000))
def test_parse_amount_rejects_absurdly_long_numbers(n):
    # also covers Python's 4300-digit int() limit, which used to raise ValueError
    assert parse_amount("9" * n) is None


# ---------------------------------------------------------- parse_tax_slab
@given(st.text() | st.none())
def test_parse_tax_slab_no_crash(s):
    try:
        parse_tax_slab(s)
    except Exception as e:
        assert False, f"parse_tax_slab crashed with: {e!r}"


@given(ANY_INPUT)
def test_parse_tax_slab_no_crash_any_type(s):
    try:
        parse_tax_slab(s)
    except Exception as e:
        assert False, f"parse_tax_slab crashed with: {e!r}"


@given(ANY_INPUT)
def test_parse_tax_slab_result_is_none_or_valid_slab(s):
    result = parse_tax_slab(s)
    if result is not None:
        low, high, rate = result
        assert all(isinstance(v, int) for v in result)
        assert 0 <= low <= high
        assert 0 <= rate <= 100


@given(st.integers(0, 10**12), st.integers(0, 10**12), st.integers(0, 100))
def test_parse_tax_slab_round_trip(a, b, rate):
    low, high = min(a, b), max(a, b)
    assert parse_tax_slab(f"{low}-{high}:{rate}") == (low, high, rate)


@given(st.integers(1, 10**12), st.integers(1, 10**12), st.integers(0, 100))
def test_parse_tax_slab_rejects_low_above_high(a, b, rate):
    low, high = max(a, b) + 1, min(a, b)
    assert parse_tax_slab(f"{low}-{high}:{rate}") is None


@given(st.integers(0, 10**6), st.integers(101, 10**6))
def test_parse_tax_slab_rejects_rate_above_100(low, rate):
    assert parse_tax_slab(f"{low}-{low + 1}:{rate}") is None


@given(st.text().filter(lambda s: ":" not in s))
def test_parse_tax_slab_rejects_line_without_colon(s):
    assert parse_tax_slab(s) is None
