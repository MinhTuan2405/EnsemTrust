param(
    [string]$msg
)

if (-not $msg) {
    $now = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $msg = "sync at $now"
}

Write-Host "Commit message: $msg"

git add .
git commit -m "$msg"
git push
