# Test plan and local execution record

## Coverage
- API health and first-run data initialization.
- Work-item creation and generated project keys.
- Human approval, sequential unlock, and audit persistence.
- Out-of-order workflow rejection and review-note validation.
- Rejected-stage resubmission.
- Optional browser smoke: render dashboard, approve a phase, and add a backlog item.

## Execute

```powershell
python -m pip install -e ".[test]"
python -m pytest --junitxml=test-results/junit.xml
```

For browser validation, install Chromium with `python -m playwright install chromium`, set `$env:RUN_BROWSER_TESTS='1'`, then run `python -m pytest tests/test_browser.py --junitxml=test-results/playwright.xml`.

## Execution report
Pending execution in the local environment. The JUnit XML report is generated under `test-results/` when the suite runs; generated reports are intentionally excluded from source control and should be attached to the capstone/Jira evidence after execution.
