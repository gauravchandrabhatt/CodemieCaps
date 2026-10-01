$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $projectRoot
python -m pip install -e '.[test]'
python -m compileall -q src tests
python -m pytest --junitxml=test-results\junit.xml
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
python -m pip wheel --no-deps --wheel-dir dist .
