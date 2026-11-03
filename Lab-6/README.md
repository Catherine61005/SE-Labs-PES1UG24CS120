# Lab 6: Code and Branch Coverage Analysis

**Assigned application:** L6_L7_57_income_tax  
**Module under test:** income_tax.py

## Contents
- income_tax.py: original assigned application, unchanged.
- test_code_coverage.py: statement/code coverage tests.
- test_branch_coverage.py: tests exercising both outcomes of each decision.
- coverage_code.txt and coverage_branch.txt: command output and coverage reports.
- screenshots/: SVG terminal-style evidence summaries.

## Run code coverage
```bash
coverage erase
coverage run --source=income_tax -m pytest -v test_code_coverage.py
coverage report -m
```

## Run branch coverage
```bash
coverage erase
coverage run --branch --source=income_tax -m pytest -v test_branch_coverage.py
coverage report -m
```

Coverage is measured for income_tax.py, not the test files. Both runs passed all tests and reported 100% coverage.
