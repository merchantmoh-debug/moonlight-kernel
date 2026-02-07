# Project Moonlight: Clean Room Verification
# "Start Fresh. Trust Nothing."

$ErrorActionPreference = "Continue" 
$MoonBitPath = "$HOME\.moon\bin"
$MoonExe = "$MoonBitPath\moon.exe"

$env:Path += ";$MoonBitPath"

Write-Host "[Ark] Building 'The Verified Beast'..."
Set-Location "$PSScriptRoot\..\kernel-verified"

# 1. Check
Write-Host "[Ark] Running 'moon check'..."
& $MoonExe check
if ($LASTEXITCODE -ne 0) {
    Write-Error "Check Failed."
    exit 1
}

# 2. Test
Write-Host "[Ark] Executing Verification Suite..."
& $MoonExe test

if ($LASTEXITCODE -eq 0) {
    Write-Host "[Ark] VERIFICATION SUCCESSFUL. The Beast is Verified."
}
else {
    Write-Host "[Ark] VERIFICATION FAILED."
    exit 1
}
