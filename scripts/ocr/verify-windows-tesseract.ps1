param(
    [Parameter(Mandatory = $false)]
    [string]$TesseractPath = "C:\Program Files\Tesseract-OCR\tesseract.exe",
    [Parameter(Mandatory = $true)]
    [ValidatePattern('^[A-Fa-f0-9]{64}$')]
    [string]$ExpectedSha256
)

$ErrorActionPreference = 'Stop'
$resolved = (Resolve-Path -LiteralPath $TesseractPath).Path
if (-not [System.IO.Path]::IsPathFullyQualified($resolved)) {
    throw 'Tesseract path must be absolute.'
}
$observed = (Get-FileHash -LiteralPath $resolved -Algorithm SHA256).Hash.ToLowerInvariant()
if ($observed -ne $ExpectedSha256.ToLowerInvariant()) {
    throw "Tesseract SHA-256 mismatch. Observed: $observed"
}
$versionOutput = & $resolved --version 2>&1
if ($LASTEXITCODE -ne 0 -or -not ($versionOutput[0] -match '^tesseract\s+([0-9]+\.[0-9]+\.[0-9]+)')) {
    throw 'Tesseract version could not be verified.'
}
$version = [version]$Matches[1]
if ($version -lt [version]'5.5.4') {
    throw "Tesseract $version is below the reviewed minimum 5.5.4."
}
$languages = & $resolved --list-langs 2>&1
if ($LASTEXITCODE -ne 0 -or $languages -notcontains 'eng') {
    throw 'The approved English traineddata model is unavailable.'
}
[ordered]@{
    executable = $resolved
    sha256 = $observed
    version = $version.ToString()
    english_model = $true
    environment = [ordered]@{
        CODEASSESS_TESSERACT_PATH = $resolved
        CODEASSESS_TESSERACT_SHA256 = $observed
    }
} | ConvertTo-Json -Depth 4
