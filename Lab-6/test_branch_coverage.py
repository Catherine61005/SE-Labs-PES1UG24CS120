"""Branch coverage tests for every decision in income_tax.py."""
import pytest
from income_tax import taxable_income, tax_due, refund_status

@pytest.mark.parametrize(
    ("gross", "regime", "investments", "expected"),
    [
        (-1, "new", 0, "invalid income"),
        (1_000_000, "new", 0, 925_000),
        (1_000_000, "old", 100_000, 850_000),
        (1_000_000, "old", 200_000, 800_000),
        (10_000, "new", 0, 0),
        (500_000, "unknown", 0, "unknown regime"),
    ],
)
def test_taxable_income_branches(gross, regime, investments, expected):
    if isinstance(expected, str):
        with pytest.raises(ValueError, match=expected):
            taxable_income(gross, regime, investments)
    else:
        assert taxable_income(gross, regime, investments) == expected

@pytest.mark.parametrize(
    ("taxable", "age", "expected"),
    [
        (-1, 30, "invalid amount"),
        (200_000, 30, 0),
        (250_000, 59, 0),
        (400_000, 30, 7_500),
        (600_000, 30, 32_500),
        (400_000, 60, 5_000),
        (600_000, 80, 5_000),
        (300_000, 60, 0),
        (500_000, 80, 0),
    ],
)
def test_tax_due_branches(taxable, age, expected):
    if expected == "invalid amount":
        with pytest.raises(ValueError, match="invalid amount"):
            tax_due(taxable, age)
    else:
        assert tax_due(taxable, age) == expected

@pytest.mark.parametrize(
    ("paid", "due", "filed", "expected"),
    [
        (20, 10, True, "refund"),
        (20, 10, False, "refund delayed"),
        (5, 10, True, "pay balance"),
        (5, 10, False, "pay balance with penalty"),
        (10, 10, True, "settled"),
    ],
)
def test_refund_status_branches(paid, due, filed, expected):
    assert refund_status(paid, due, filed) == expected
