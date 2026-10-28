# Lab 5 – Reflection

**Name:** Catherine D  **SRN:** PES1UG24CS120  **Repo:** L5_57_loan-eligibility

### 1. Which issues were the easiest to fix, and which were the hardest? Why?

**Easiest:** the Flake8 and low-severity Pylint findings — missing blank lines (E302), long lines (E501), the unused `math` import, the f-string with no placeholders, and camelCase names. Each message names the exact line and the fix is mechanical; none of them change behaviour.

**Hardest:** the security issues and the logic bugs, because the tool only tells you *what* is wrong, not *what to replace it with*.
- Bandit B402/B321 (FTP) cannot be silenced by tweaking a line — even `ftplib.FTP_TLS` is still flagged because the module import itself is blacklisted. I had to change the transport (HTTPS with certificate verification) and move the hard-coded password into environment variables, while keeping the function's purpose.
- Replacing `subprocess` + `mail` meant rewriting the notification with `smtplib` and STARTTLS.
- The logic bugs were hardest of all because **no tool reported them**: an EMI of ₹3,75,000 on a ₹5 L loan, an applicant with an 80% FOIR being approved, a "maximum loan" that ignored interest, and interest-saved that included the prepaid principal. I found them only by reading the output critically and checking the maths (e.g. confirming that the EMI on the new maximum loan is exactly the affordable ₹15,000).

### 2. Did the static analysis tools report any false positives? If so, describe one example.

Yes, or at least findings that were not real bugs in this context:
- **Pylint R0913/R0917 (too many arguments)** on `checkEligibility` is a design heuristic, not a defect — six inputs to an eligibility rule is reasonable. It disappeared only because the sixth parameter (`history`) was genuinely dead code.
- **Bandit B311 (random)** is only a real problem if the value must be unpredictable. For a loan application ID it arguably matters (sequential/guessable IDs enable enumeration), so I fixed it, but for something like shuffling demo data it would be a false positive.
- **Bandit B404 (import subprocess)** is Low severity and fires on the import alone, regardless of how `subprocess` is used — a safe, fully-qualified, list-argument call would still be flagged.

The opposite problem — **false negatives** — was more significant here: all six logic bugs passed every tool, and a 10.00/10 Pylint score would not have caught them.

### 3. How would you integrate static analysis tools into your actual software development workflow?

- **Locally:** run Flake8 and Pylint in the editor (VS Code extensions) for instant feedback, plus a **pre-commit hook** (`pre-commit` with `flake8`, `pylint`, `bandit`) so style and security issues are blocked before they reach a commit.
- **In CI:** a GitHub Actions job on every pull request that runs `flake8`, `pylint --fail-under=9.5` and `bandit -r . -ll` (fail on medium/high), so the build fails when quality regresses.
- **Configuration in the repo:** a shared `.pylintrc` / `setup.cfg` so everyone uses the same line length and rules, and `# nosec` / `# pylint: disable` only with a justification comment.
- **Not a substitute for tests:** since the tools missed every logic bug in this lab, I would pair them with unit tests (e.g. `pytest` cases checking a known EMI, FOIR rejection and the 300–900 score range) in the same CI pipeline.

### 4. What tangible improvements did you observe in code quality, readability, or robustness after applying the fixes?

- **Security:** Bandit went from 8 issues (2 High, 1 Medium, 5 Low) to 0. No plaintext FTP, no hard-coded password in source, no unsafe `marshal` deserialization, no shell-out to `mail`, unguessable IDs.
- **Quality score:** Pylint 5.17 → **10.00/10**; Flake8 22 → **0** violations.
- **Robustness:** files are always closed (`with`), there is no shared mutable default, `load_applications` no longer rebinds a global, invalid inputs raise clear `ValueError`s, 0% interest and zero income no longer crash, and importing the module no longer runs the demo or writes files.
- **Correctness:** the demo output is now sensible — EMI ₹10,379.18, ineligible applicants rejected, maximum loan ₹7,22,600.60, interest saved ₹12,275.07, score 950 → INVALID.
- **Readability:** snake_case names, docstrings that state the rate convention (decimal, 9% → 0.09), named constants (`MIN_CREDIT_SCORE`, `ALLOWED_LOAN_TYPES`) instead of magic values, and flat `if` chains instead of nested `elif/else`.
