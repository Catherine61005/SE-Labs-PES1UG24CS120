"""Input parsing helpers for the income tax calculator (Lab 7, fixed version).

The original module assumed every input was well formed and crashed on
anything else (None, empty text, wrong format, huge numbers, ...).

Fixed behaviour: each function accepts *any* Python object and never raises.
  * clean_pan      -> always returns a str ("" if the input is not text)
  * parse_amount   -> returns a non-negative int, or None if the input is invalid
  * parse_tax_slab -> returns (low, high, rate) ints, or None if the input is invalid
"""
import re

MAX_DIGITS = 18   # largest amount/slab limit accepted (fits in 64 bits, avoids huge ints)
MAX_RATE = 100    # a tax rate is a percentage

# Optional 'Rs' / 'Rs.' / rupee-sign prefix (any case) followed by ASCII digits only.
_AMOUNT = re.compile(r"(?:rs\.?|₹)?([0-9]+)", re.IGNORECASE | re.ASCII)
# LOW-HIGH:RATE, ASCII digits only, optional blanks around the separators.
_SLAB = re.compile(
    r"\s*([0-9]{1,%d})\s*-\s*([0-9]{1,%d})\s*:\s*([0-9]{1,3})\s*" % (MAX_DIGITS, MAX_DIGITS)
)


def clean_pan(pan):
    """
    Removes all whitespace from a PAN and upper-cases it.
    Returns "" if pan is not a string (e.g. None), so it never raises.
    """
    if not isinstance(pan, str):
        return ""
    return "".join(pan.split()).upper()


def parse_amount(text):
    """
    Converts an amount such as 'Rs 12,50,000' into an int.
    Accepts an optional 'Rs' / 'Rs.' / rupee-sign prefix (any case), commas
    and spaces around plain ASCII digits.
    Returns None for anything else: non-text, empty text, decimals, negative
    numbers, other-script digits, underscores or numbers longer than MAX_DIGITS.
    """
    if not isinstance(text, str):
        return None
    match = _AMOUNT.fullmatch("".join(text.split()).replace(",", ""))
    if match is None:
        return None
    digits = match.group(1).lstrip("0") or "0"
    if len(digits) > MAX_DIGITS:
        return None
    return int(digits)


def parse_tax_slab(line):
    """
    Parses 'LOW-HIGH:RATE' into a (low, high, rate) tuple of ints.
    Returns None if the line is not in that exact format, if LOW is greater
    than HIGH, or if RATE is above MAX_RATE (100).
    """
    if not isinstance(line, str):
        return None
    match = _SLAB.fullmatch(line)
    if match is None:
        return None
    low, high, rate = (int(group) for group in match.groups())
    if low > high or rate > MAX_RATE:
        return None
    return low, high, rate


def main():
    try:
        print("==== Running clean_pan ====")
        value = input("Enter a PAN (e.g. abcde 1234f): ")
        pan = clean_pan(value)
        print("Cleaned PAN:", pan if pan else "(nothing entered)")

        print("\n==== Running parse_amount ====")
        value = input("Enter an amount (e.g. Rs 12,50,000): ")
        amount = parse_amount(value)
        if amount is None:
            print("Invalid amount: use digits only, e.g. Rs 12,50,000")
        else:
            print("Amount in rupees:", amount)

        print("\n==== Running parse_tax_slab ====")
        value = input("Enter a tax slab as LOW-HIGH:RATE (e.g. 250000-500000:5): ")
        slab = parse_tax_slab(value)
        if slab is None:
            print("Invalid tax slab: use LOW-HIGH:RATE with LOW <= HIGH and RATE 0-100,"
                  " e.g. 250000-500000:5")
        else:
            print("Tax slab (low, high, rate):", slab)
    except (EOFError, KeyboardInterrupt):
        print("\nInput cancelled.")


if __name__ == "__main__":
    main()
