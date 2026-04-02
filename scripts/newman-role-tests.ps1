param(
    [ValidateSet("admin", "analyst", "viewer", "all")]
    [string]$Role = "all"
)

$projectRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$collection = "postman/finance-dashboard-role-tests.postman_collection.json"
$environment = "postman/finance-dashboard-local.postman_environment.json"

Push-Location $projectRoot
try {
    if (-not (Test-Path $collection)) {
        Write-Error "Collection file not found: $collection"
        exit 1
    }

    if (-not (Test-Path $environment)) {
        Write-Error "Environment file not found: $environment"
        exit 1
    }

    $folders = switch ($Role) {
        "admin" { @("Role - Admin") }
        "analyst" { @("Role - Analyst") }
        "viewer" { @("Role - Viewer") }
        default { @("Role - Admin", "Role - Analyst", "Role - Viewer") }
    }

    foreach ($folder in $folders) {
        Write-Host "Running Newman folder: $folder"
        npx newman run $collection -e $environment --folder $folder --reporters cli
        if ($LASTEXITCODE -ne 0) {
            exit $LASTEXITCODE
        }
    }
}
finally {
    Pop-Location
}
