# Thin Windows wrapper. All logic lives in scripts/sdd.py (cross-platform).
param([Parameter(ValueFromRemainingArguments = $true)][string[]]$Args)
$script = Join-Path $PSScriptRoot "sdd.py"
# Translate legacy -Force switch to --force for the Python CLI.
$translated = $Args | ForEach-Object { if ($_ -eq "-Force") { "--force" } else { $_ } }
python $script @translated
exit $LASTEXITCODE
