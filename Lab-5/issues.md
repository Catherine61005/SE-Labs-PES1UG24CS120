# Lab 5 – Static Code Analysis: Issue Table

**Name:** Catherine D  **SRN:** PES1UG24CS120  **Repo:** L5_57_loan-eligibility  **File:** `loan_calculator.py`

Line numbers refer to the **original** file (see `reports/before/`). Rows are ordered high → medium → low severity.

## Summary

| Tool | Before | After |
|------|--------|-------|
| Bandit | 8 issues (2 High, 1 Medium, 5 Low) | 0 issues |
| Pylint | 5.17/10 (43 messages) | 10.00/10 |
| Flake8 | 22 violations | 0 violations |

## Issues found by the tools

| # | Issue | Type | Tool / Code | Line(s) | Description | Fix Approach |
|---|-------|------|-------------|---------|-------------|--------------|
| 1 | Insecure FTP import | Security (High) | Bandit B402 | 3 | `ftplib` sends data and credentials in plaintext (CWE-319). | Removed `ftplib`; upload now goes over HTTPS via `http.client.HTTPSConnection` with a verified `ssl.create_default_context()`. |
| 2 | Insecure FTP call | Security (High) | Bandit B321 | 68–70 | `ftplib.FTP(...)` + `login()` transmits the bureau password and loan report unencrypted. | `upload_to_bureau()` rewritten to `PUT` the report over TLS with an `Authorization` header. |
| 3 | Unsafe deserialization | Security (Medium) | Bandit B302 | 57, 64 | `marshal.loads()` on a file is unsafe for untrusted input and its format is Python-version specific (CWE-502). | Replaced `marshal` with `json.dump` / `json.load`; file renamed `loans.json`. |
| 4 | Hard-coded password | Security (Low) | Bandit B107 | 67 | Default argument `password="Bureau#2024"` leaks a credential into source control (CWE-259). | Removed the parameters; credentials read from `BUREAU_USER` / `BUREAU_PASSWORD` environment variables. |
| 5 | Weak random for IDs | Security (Low) | Bandit B311 | 51 | `random.randint` is predictable; IDs could be guessed (CWE-330). | Use `secrets.randbelow()` (a collision check was added in the logic-bug commit, L6). |
| 6 | Shelling out to `mail` | Security (Low) | Bandit B404, B603, B607 | 6, 74 | `subprocess` with a partial executable path (`mail`) can be hijacked via `PATH`; email address is untrusted input (CWE-78). Pylint also flagged W1510 (no `check=`). | Removed `subprocess`; send email with `smtplib` + `EmailMessage` over STARTTLS. |
| 7 | Mutable default argument | Bug (Medium) | Pylint W0102 | 20–21 | `history=[]` is created once and shared across calls, so every call appends to the same list. It was never read. | Removed the dead `history` parameter (this also fixes R0913/R0917 too-many-arguments). |
| 8 | Files not closed on error | Bug (Medium) | Pylint R1732 | 56, 63, 70 | `open()` without `with`; the file handle leaks if `write`/`read` raises. In line 70 the report file was never closed at all. | All file access uses `with open(..., encoding="utf-8")`. |
| 9 | `global` statement | Design (Medium) | Pylint W0603 | 62 | `load_applications` rebinds the module global, which breaks any other reference to the dict. | Mutate in place with `applications.clear(); applications.update(data)` and return it. |
| 10 | Shadowed builtin / unused args | Bug (Medium) | Pylint W0622, W0613, W0612 | 33–37 | `sum` shadows the builtin; `annual_rate` and `month` unused — a sign the function ignores interest (see L3). | Rewrote `max_loan_amount` (see L3); no builtin shadowing, all arguments used. |
| 11 | Module-level `main()` call | Design (Medium) | Code review | 106 | Importing the module runs the demo and writes `loans.bin`. | Wrapped in `if __name__ == "__main__":`. |
| 12 | Naming convention | Style (Low) | Pylint C0103 | 14–81 | camelCase function names (`calculateEMI`, `riskBand`, …) violate PEP 8. | Renamed to snake_case (`calculate_emi`, `risk_band`, …). |
| 13 | Missing docstrings | Style (Low) | Pylint C0114, C0116 | 1, all functions | No module or function documentation. | Added module docstring (incl. rate convention) and function docstrings. |
| 14 | Redundant control flow | Style (Low) | Pylint R1703, R1705, R1714, C0325 | 28–31, 79, 82–91 | `if/else` returning booleans, `elif` after `return`, chained `==`, superfluous parentheses. | Use `loan_type not in ALLOWED_LOAN_TYPES` (a set), flat `if` returns, no parens. |
| 15 | Unused import | Style (Low) | Pylint W0611 / Flake8 F401 | 2 | `import math` never used. | Removed. |
| 16 | f-string without placeholders | Style (Low) | Pylint W1309 / Flake8 F541 | 104 | `f"Upload to bureau skipped..."` has no `{}`. | Plain string. |
| 17 | Missing blank lines | Style (Low) | Flake8 E302, E305 | 14–93, 106 | PEP 8 requires two blank lines around top-level definitions. | Two blank lines before every `def` and the main guard. |
| 18 | Lines too long | Style (Low) | Flake8 E501 / Pylint C0301 | 20, 55, 70, 78, 95, 96, 100 | Lines over 79 chars (Flake8) / 100 chars (Pylint). | Wrapped dicts, calls and `print()` arguments. |

## Logic bugs found from the program's output (not flagged by any tool)

| # | Issue | Type | Line(s) | Wrong output (before) | Description | Fix Approach | Output (after) |
|---|-------|------|---------|-----------------------|-------------|--------------|----------------|
| L1 | Rate passed as percent | Bug (High) | 94 | EMI = **375000.00** per month for a 5 L loan | Demo passes `9` instead of `0.09`, so the monthly rate is 75%. Every other call uses decimals. | Call with `0.09`; `calculate_emi` now rejects rates outside `[0, 1)` and handles 0% (division by zero before). | EMI = **10379.18** |
| L2 | Eligibility short-circuit | Bug (High) | 24–25, 28–31 | Income 15000 with EMIs 12000 → **True**; loan type `crypto` → **True** | `credit_score > 750 or income > 25000` returned `True` *before* the FOIR and loan-type checks, so an 80% FOIR and an invalid product were approved. Also `existing_emi / income` crashes when income is 0. | Check every hard rule first (age, `income > 0`, FOIR ≤ 0.5, allowed loan type) and require `credit_score >= 600`. | **False**, **False** |
| L3 | Max loan ignores interest | Bug (High) | 33–38 | **900000.0** | Summed 60 × affordable EMI, i.e. treated the loan as interest-free (`annual_rate` unused). | Present value of an annuity: `available × (1 − (1+r)^−n) / r`; returns 0 if no EMI capacity. Verified: EMI on the result = exactly 15000. | **722600.60** |
| L4 | Interest saved overstated | Bug (Medium) | 76–79 | **62275.07** | Difference in total payments also contains the 50000 prepaid principal itself. | Subtract the prepayment; validate `0 ≤ prepayment < principal`. Cross-checked against the amortisation schedules (12275.09 vs 12275.07, rounding). | **12275.07** |
| L5 | Risk band accepts impossible score | Bug (Medium) | 81–91 | 950 → **LOW** | Credit scores (CIBIL) range 300–900; anything above 900 was treated as excellent. | Return `INVALID` for scores outside 300–900. | **INVALID** |
| L6 | Negative balance / duplicate IDs | Bug (Low) | 46 | — | Floating-point rounding can leave a tiny negative final balance. | Clamp with `max(..., 0.0)`; also regenerate an application ID if it already exists. | `(12, 87.97, 0.0)` |

## Commits (one per tool, plus logic bugs)

| # | Commit | Fixes | Result |
|---|--------|-------|--------|
| 0 | `Add static analysis reports before fixes` | — | `reports/before/*.txt` |
| 1 | `Fix Bandit security issues (8 -> 0)` | Issues 1–6 | Bandit 8 → 0 |
| 2 | `Fix logic bugs found from program output` | L1–L6 | Demo output correct |
| 3 | `Fix Pylint issues (6.80 -> 10.00/10)` | Issues 7–16 | Pylint → 10.00/10 |
| 4 | `Fix Flake8 PEP 8 issues (23 -> 0)` | Issues 17–18 | Flake8 → 0 |
| 5 | `Add after reports, issue table and reflection` | — | `reports/after/*.txt`, this file, `reflection.md` |

Each fix commit's message body lists the issue numbers from this table, so `git log` maps directly to the rows above.
