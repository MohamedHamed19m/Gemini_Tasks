#!/usr/bin/env pwsh
# Project Verification Script for Ralph Wiggum
# Place in .gemini/verify.ps1 in your project

Write-Host "Running project verification..."

# Exit on any error
$ErrorActionPreference = "Stop"

try {
    # Run tests
    if (Test-Path "package.json") {
        Write-Host "Running npm tests..."
        npm test
        Write-Host "Tests passed"
    }
    
    # Run linting
    if (Test-Path ".eslintrc*") {
        Write-Host "Running linter..."
        npm run lint
        Write-Host "Linting passed"
    }
    
    # Type checking
    if (Test-Path "tsconfig.json") {
        Write-Host "Running type check..."
        npm run type-check
        Write-Host "Type check passed"
    }
    
    # Build check
    if (Test-Path "package.json") {
        $packageJson = Get-Content "package.json" -Raw | ConvertFrom-Json
        if ($packageJson.scripts.build) {
            Write-Host "Running build..."
            npm run build
            Write-Host "Build successful"
        }
    }

    # Python/uv check
    if ((Test-Path "server/pyproject.toml") -or (Test-Path "server/requirements.txt")) {
        Write-Host "Checking Python project in server/..."
        
        if (Get-Command uv -ErrorAction SilentlyContinue) {
            Write-Host "Running Python tests with uv..."
            $env:PYTHONPATH = "."
            Set-Location -Path server
            uv run pytest
            Set-Location -Path ..
            Write-Host "Python tests passed"
        } else {
            Write-Host "uv not found, skipping Python tests"
        }
    }
    
    Write-Host "`nAll verification passed"
    exit 0
    
} catch {
    Write-Host "`nVerification failed: $_"
    exit 1
}