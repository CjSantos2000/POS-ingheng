$ErrorActionPreference = 'Stop'

Set-Location $PSScriptRoot

$hostName = '127.0.0.1'
$port = 8000
$loginUrl = "http://$hostName`:$port/login/"

if (Test-Path '.venv/Scripts/python.exe') {
    $python = '.venv/Scripts/python.exe'
} elseif (Test-Path 'venv/Scripts/python.exe') {
    $python = 'venv/Scripts/python.exe'
} elseif (Get-Command py -ErrorAction SilentlyContinue) {
    $python = 'py'
} else {
    $python = 'python'
}

Write-Host "Starting POS Enghing on http://$hostName`:$port ..."
Write-Host "Opening login page: $loginUrl"

Start-Job -ScriptBlock {
    param($url)
    Start-Sleep -Seconds 2
    Start-Process $url
} -ArgumentList $loginUrl | Out-Null

if ($python -eq 'py') {
    & py -3 manage.py runserver "$hostName`:$port"
} else {
    & $python manage.py runserver "$hostName`:$port"
}
