$ErrorActionPreference = "Stop"

$siteDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent $siteDir

$pythonExe = Join-Path $projectRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $pythonExe)) {
    $pythonExe = "python"
}

$builder = Join-Path $projectRoot "build_interactive_consurf_viewer.py"
if (-not (Test-Path $builder)) {
    throw "Could not find builder script at $builder"
}

& $pythonExe $builder `
  --standalone `
  --input "RAD21 Full=$projectRoot\ConSurf\output\RAD21\rad21_consurf_full\Human_RAD21_consurf.grades" `
  --input "RAD21 Vertebrates=$projectRoot\ConSurf\output\RAD21\rad21_consurf_vertebrates\Human_RAD21_consurf.grades" `
  --input "RAD21 Invertebrates=$projectRoot\ConSurf\output\RAD21\rad21_consurf_invertebrates\Ciona_intestinalis_consurf.grades" `
  --output "$siteDir\index.html"

Write-Host "Updated $siteDir\index.html"
