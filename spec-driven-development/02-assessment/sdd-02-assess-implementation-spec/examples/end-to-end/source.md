Implement a Python CLI that reads a UTF-8 CSV file and prints the sum of the amount column.
Use Python 3.11.9 and only the standard library. Network access and file writes are excluded.
Parser owner: developer. Input schema: header amount, decimal strings, at most 1000 rows.
Output: one decimal string with exactly two fractional digits and a newline; success exit 0.
Acceptance: rows 1.25 and 2.50 produce 3.75. Empty data produces 0.00.
Invalid decimal values must fail. The error exit code and stderr schema require product-owner approval.
Implement parser first, then CLI. Verifier owns independent parser-to-CLI integration checks.
Run python -m unittest. Record fixture hash, Python version, command and exit status.
