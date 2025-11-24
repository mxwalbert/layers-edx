# Setup script for EPQ Java library
# This script clones and compiles the EPQ library for cross-validation testing

param(
    [switch]$SkipClone = $false
)

$ErrorActionPreference = "Stop"

Write-Host "Setting up EPQ library for cross-validation testing..." -ForegroundColor Cyan

# Check for Java
Write-Host "`nChecking Java version..." -ForegroundColor Yellow
try {
    $javaVersion = java -version 2>&1 | Select-String "version" | ForEach-Object { $_.Line }
    Write-Host "Found: $javaVersion" -ForegroundColor Green
    
    # Check if Java 21+
    if ($javaVersion -notmatch "(\d+)\.") {
        Write-Host "Warning: Could not parse Java version. EPQ requires Java 21+" -ForegroundColor Yellow
    }
} catch {
    Write-Host "ERROR: Java not found. Please install Java 21 or higher." -ForegroundColor Red
    Write-Host "Download from: https://adoptium.net/" -ForegroundColor Yellow
    exit 1
}

# Check for Maven
Write-Host "`nChecking Maven..." -ForegroundColor Yellow
try {
    $mvnVersion = mvn -version 2>&1 | Select-String "Apache Maven" | ForEach-Object { $_.Line }
    Write-Host "Found: $mvnVersion" -ForegroundColor Green
} catch {
    Write-Host "ERROR: Maven not found. Please install Maven." -ForegroundColor Red
    Write-Host "Download from: https://maven.apache.org/download.cgi" -ForegroundColor Yellow
    exit 1
}

# Create directory structure
$epqDir = ".venv\share\java"
$epqPath = "$epqDir\EPQ"

if (-not (Test-Path $epqDir)) {
    Write-Host "`nCreating directory: $epqDir" -ForegroundColor Yellow
    New-Item -ItemType Directory -Path $epqDir -Force | Out-Null
}

# Clone EPQ repository
if (-not $SkipClone) {
    if (Test-Path $epqPath) {
        Write-Host "`nEPQ directory already exists at $epqPath" -ForegroundColor Yellow
        $overwrite = Read-Host "Do you want to remove and re-clone? (y/N)"
        if ($overwrite -eq 'y' -or $overwrite -eq 'Y') {
            Write-Host "Removing existing EPQ directory..." -ForegroundColor Yellow
            Remove-Item -Recurse -Force $epqPath
        } else {
            Write-Host "Skipping clone step." -ForegroundColor Yellow
            $SkipClone = $true
        }
    }
    
    if (-not $SkipClone) {
        Write-Host "`nCloning EPQ repository..." -ForegroundColor Yellow
        Push-Location $epqDir
        try {
            git clone https://github.com/usnistgov/EPQ.git
            Write-Host "EPQ cloned successfully!" -ForegroundColor Green
        } catch {
            Write-Host "ERROR: Failed to clone EPQ repository." -ForegroundColor Red
            Pop-Location
            exit 1
        }
        Pop-Location
    }
}

# Compile EPQ
Write-Host "`nCompiling EPQ library..." -ForegroundColor Yellow
Push-Location $epqPath
try {
    mvn compile
    if ($LASTEXITCODE -ne 0) {
        throw "Maven compile failed"
    }
    Write-Host "EPQ compiled successfully!" -ForegroundColor Green
} catch {
    Write-Host "ERROR: Failed to compile EPQ." -ForegroundColor Red
    Pop-Location
    exit 1
}

# Copy dependencies
Write-Host "`nCopying Maven dependencies..." -ForegroundColor Yellow
try {
    mvn dependency:copy-dependencies -DoutputDirectory=target/dependency
    if ($LASTEXITCODE -ne 0) {
        throw "Maven dependency copy failed"
    }
    Write-Host "Dependencies copied successfully!" -ForegroundColor Green
} catch {
    Write-Host "ERROR: Failed to copy dependencies." -ForegroundColor Red
    Pop-Location
    exit 1
}

Pop-Location

# Verify setup
Write-Host "`nVerifying EPQ setup..." -ForegroundColor Yellow
$elementClass = "$epqPath\target\classes\gov\nist\microanalysis\EPQLibrary\Element.class"
$jamaJar = "$epqPath\target\dependency\jama-1.0.3.jar"

$verified = $true
if (-not (Test-Path $elementClass)) {
    Write-Host "ERROR: EPQ classes not found at $elementClass" -ForegroundColor Red
    $verified = $false
}

if (-not (Test-Path $jamaJar)) {
    Write-Host "ERROR: Jama dependency not found at $jamaJar" -ForegroundColor Red
    $verified = $false
}

if ($verified) {
    Write-Host "`n✓ EPQ setup complete and verified!" -ForegroundColor Green
    Write-Host "`nEPQ Location: $epqPath" -ForegroundColor Cyan
    Write-Host "Compiled Classes: $epqPath\target\classes" -ForegroundColor Cyan
    Write-Host "Dependencies: $epqPath\target\dependency" -ForegroundColor Cyan
} else {
    Write-Host "`n✗ EPQ setup incomplete. Please review errors above." -ForegroundColor Red
    exit 1
}
