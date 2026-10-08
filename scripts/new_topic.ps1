[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$Name,

    [string]$Venue = "待确认",

    [string]$Deadline = "待确认"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$safeName = ($Name.Trim() -replace '[<>:"/\\|?*]', '-') -replace '\s+', '-'
if ([string]::IsNullOrWhiteSpace($safeName)) {
    throw "Name must contain at least one valid character."
}

$target = Join-Path (Join-Path $root "projects") ("{0}-{1}" -f (Get-Date -Format "yyyyMMdd"), $safeName)
if (Test-Path -LiteralPath $target) {
    throw "Project already exists: $target"
}

New-Item -ItemType Directory -Path $target | Out-Null

function Copy-Template {
    param(
        [Parameter(Mandatory = $true)][string]$Source,
        [Parameter(Mandatory = $true)][string]$Destination
    )

    $content = Get-Content -LiteralPath $Source -Raw -Encoding UTF8
    $content = $content.Replace("{{PROJECT_NAME}}", $Name)
    $content = $content.Replace("{{VENUE}}", $Venue)
    $content = $content.Replace("{{DEADLINE}}", $Deadline)
    Set-Content -LiteralPath $Destination -Value $content -Encoding UTF8
}

$templates = Join-Path $root "templates"
Copy-Template (Join-Path $templates "project_readme.md") (Join-Path $target "README.md")
Copy-Template (Join-Path $templates "evidence.md") (Join-Path $target "EVIDENCE.md")
Copy-Template (Join-Path $templates "decisions.md") (Join-Path $target "DECISIONS.md")

Write-Output $target
