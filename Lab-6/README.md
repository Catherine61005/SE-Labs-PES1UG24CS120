# Lab 6: Code and Branch Coverage Analysis

**Assigned application:** `L6_L7_57_income_tax`  
**Module under test:** `income_tax.py`

## Files
- `income_tax.py`: original assigned application, unchanged.
- `test_income_tax.py`: original starter tests from the assigned repository.
- `CodeCoverageTest_57_income_tax.py`: additional code coverage test cases.
- `BranchCoverageTest_57_income_tax.py`: additional branch coverage test cases.
- `coverage_code.txt` and `coverage_branch.txt`: recorded test and coverage output.
- `screenshots/`: terminal-style coverage evidence.

## Code coverage
```bash
coverage erase
coverage run --source=income_tax -m pytest -v CodeCoverageTest_57_income_tax.py
coverage report -m
```

## Branch coverage
```bash
coverage erase
coverage run --branch --source=income_tax -m pytest -v BranchCoverageTest_57_income_tax.py
coverage report -m
```

The original application was not modified. Coverage was measured only for `income_tax.py`. Both suites passed, with 100% code coverage and 100% branch coverage (28/28 branches).
