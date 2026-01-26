# Windows Setup Script for Gemini Tasks Extension
# Windows 11 Compatibility: PS 5.1 + PS 7+

Write-Host "Setting up Gemini Tasks Extension for Windows..." -ForegroundColor Green

# Create directories
$geminiDir = Join-Path $env:USERPROFILE ".gemini"
$tasksDir = Join-Path $geminiDir "tasks"
$stateDir = Join-Path $geminiDir "ralph-state"

Write-Host "Creating directories..." -ForegroundColor Yellow
if (!(Test-Path $tasksDir)) { New-Item -ItemType Directory -Force -Path $tasksDir | Out-Null }
if (!(Test-Path $stateDir)) { New-Item -ItemType Directory -Force -Path $stateDir | Out-Null }

Write-Host "OK: Directories checked/created" -ForegroundColor Green

# Set environment variables for current session
$env:GEMINI_RALPH_MODE = "true"
$env:GEMINI_MAX_ITERATIONS = "25"
$env:GEMINI_COMPLETION_PROMISE = "complete"
$env:GEMINI_TASK_LIST_ID = "default"

# Permanent environment variables
$setPermanent = Read-Host "`nSet environment variables permanently? (y/n)"
if ($setPermanent -eq "y") {
    [System.Environment]::SetEnvironmentVariable("GEMINI_RALPH_MODE", "true", "User")
    [System.Environment]::SetEnvironmentVariable("GEMINI_MAX_ITERATIONS", "25", "User")
    [System.Environment]::SetEnvironmentVariable("GEMINI_COMPLETION_PROMISE", "complete", "User")
    Write-Host "OK: Permanent environment variables set" -ForegroundColor Green
}

# Create PowerShell profile helper
$profileHelper = @"

# Gemini Ralph Wiggum Helper Functions
function Start-RalphSession {
    param([string]`$TaskListId = "default", [int]`$MaxIterations = 25)
    `$env:GEMINI_RALPH_MODE = "true"
    `$env:GEMINI_TASK_LIST_ID = `$TaskListId
    `$env:GEMINI_MAX_ITERATIONS = `$MaxIterations
    Write-Host "Starting Ralph session: `$TaskListId" -ForegroundColor Green
    gemini
}

function Show-RalphTasks {
    param([string]`$TaskListId = "default")
    `$tasksFile = Join-Path `$env:USERPROFILE ".gemini\tasks\`$TaskListId.json"
    if (Test-Path `$tasksFile) {
        `$tasks = Get-Content `$tasksFile -Raw | ConvertFrom-Json
        Write-Host "Tasks for: `$TaskListId" -ForegroundColor Cyan
        foreach (`$task in `$tasks) {
            `$statusChar = "[ ]"
            if (`$task.status -eq "completed") { `$statusChar = "[x]" }
            elseif (`$task.status -eq "in_progress") { `$statusChar = "[>]" }
            Write-Host "`$statusChar [`$(`$task.id)] `$(`$task.subject)"
        }
    } else {
        Write-Host "No tasks found for: `$TaskListId"
    }
}

Set-Alias ralph Start-RalphSession
Set-Alias ralph-tasks Show-RalphTasks
"@

$addToProfile = Read-Host "`nAdd helper functions to PowerShell profile? (y/n)"
if ($addToProfile -eq "y") {
    if (!(Test-Path $PROFILE)) { New-Item -ItemType File -Path $PROFILE -Force | Out-Null }
    Add-Content -Path $PROFILE -Value $profileHelper
    Write-Host "OK: Added to profile: $PROFILE" -ForegroundColor Green
}

Write-Host "`nSetup complete! You can now use 'ralph' to start a session." -ForegroundColor Green