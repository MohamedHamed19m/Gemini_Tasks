#!/usr/bin/env pwsh
# Project Verification Script for Ralph Wiggum
# Place in .gemini/verify.ps1 in your project

Write-Host "Running project verification..." -ForegroundColor Cyan

# Exit on any error
$ErrorActionPreference = "Stop"

try {
    # Run tests
    if (Test-Path "package.json") {
        Write-Host "Running npm tests..." -ForegroundColor Yellow
        npm test
        Write-Host "✓ Tests passed" -ForegroundColor Green
    }
    
    # Run linting
    if (Test-Path ".eslintrc*") {
        Write-Host "Running linter..." -ForegroundColor Yellow
        npm run lint
        Write-Host "✓ Linting passed" -ForegroundColor Green
    }
    
    # Type checking
    if (Test-Path "tsconfig.json") {
        Write-Host "Running type check..." -ForegroundColor Yellow
        npm run type-check
        Write-Host "✓ Type check passed" -ForegroundColor Green
    }
    
    # Build check
    $packageJson = Get-Content "package.json" -Raw | ConvertFrom-Json
    if ($packageJson.scripts.build) {
        Write-Host "Running build..." -ForegroundColor Yellow
        npm run build
        Write-Host "✓ Build successful" -ForegroundColor Green
    }
    
    Write-Host "`n✓ All verification passed" -ForegroundColor Green
    exit 0
    
} catch {
    Write-Host "`n✗ Verification failed: $_" -ForegroundColor Red
    exit 1
}
