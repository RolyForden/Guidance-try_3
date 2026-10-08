[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$ProjectPath
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$resolved = (Resolve-Path -LiteralPath $ProjectPath).Path
$errors = [System.Collections.Generic.List[string]]::new()

foreach ($relativePath in @("README.md", "EVIDENCE.md", "DECISIONS.md")) {
    if (-not (Test-Path -LiteralPath (Join-Path $resolved $relativePath) -PathType Leaf)) {
        $errors.Add("Missing file: $relativePath")
    }
}

$readmePath = Join-Path $resolved "README.md"
if (Test-Path -LiteralPath $readmePath) {
    $readme = Get-Content -LiteralPath $readmePath -Raw -Encoding UTF8
    foreach ($heading in @("## 当前问题", "## 当前判断", "## 下一步")) {
        if ($readme -notmatch [regex]::Escape($heading)) {
            $errors.Add("README.md is missing heading: $heading")
        }
    }
}

if ($errors.Count -gt 0) {
    $errors | ForEach-Object { Write-Error $_ }
    exit 1
}

Write-Output "OK: $resolved"
