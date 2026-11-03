"""Code coverage test cases for 57_income_tax (Lab 6)."""
import pytest
from income_tax import taxable_income, tax_due, refund_status

def test_new_regime_deduction_and_positive_taxable_income():
    assert taxable_income(1_000_000, "new", 0) == 925_000

def test_old_regime_investments_within_limit():
    assert taxable_income(1_000_000, "old", 100_000) == 850_000

def test_old_regime_investments_capped_at_limit():
    assert taxable_income(1_000_000, "old", 200_000) == 800_000

def test_taxable_income_cannot_be_negative():
    with pytest.raises(ValueError, match="invalid income"):
        taxable_income(-1, "new", 0)

def test_unknown_tax_regime_is_rejected():
    with pytest.raises(ValueError, match="unknown regime"):
        taxable_income(500_000, "other", 0)

def test_taxable_income_floor_is_zero():
    assert taxable_income(10_000, "new", 0) == 0

def test_tax_due_below_exemption_for_under_60():
    assert tax_due(200_000, 30) == 0

def test_tax_due_in_first_slab_for_under_60():
    assert tax_due(400_000, 30) == 7_500

def test_tax_due_in_higher_slab_for_under_60():
    assert tax_due(600_000, 30) == 32_500

def test_tax_due_for_senior_citizen():
    assert tax_due(400_000, 65) == 5_000

def test_tax_due_for_super_senior_citizen():
    assert tax_due(600_000, 80) == 5_000

def test_negative_taxable_amount_is_rejected():
    with pytest.raises(ValueError, match="invalid amount"):
        tax_due(-1, 30)

@pytest.mark.parametrize(
    ("paid", "due", "filed", "expected"),
    [
        (20_000, 10_000, True, "refund"),
        (20_000, 10_000, False, "refund delayed"),
        (5_000, 10_000, True, "pay balance"),
        (5_000, 10_000, False, "pay balance with penalty"),
        (10_000, 10_000, True, "settled"),
    ],
)
def test_refund_status_outcomes(paid, due, filed, expected):
    assert refund_status(paid, due, filed) == expected
