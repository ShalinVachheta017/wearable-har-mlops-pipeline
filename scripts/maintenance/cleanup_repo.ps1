# Repository Cleanup Script
# =======================
# Cleans up old artifacts, logs, and temporary files
# Run from repo root: .\cleanup_repo.ps1

param(
    [switch]$DryRun,
    [switch]$Aggressive
)

$ErrorActionPreference = "Continue"

Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  🧹 Repository Cleanup Script" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Cyan

if ($DryRun) {
    Write-Host "`n⚠️  DRY RUN MODE - No files will be deleted" -ForegroundColor Yellow
}

# Calculate initial size
Write-Host "`n📊 Calculating initial size..." -ForegroundColor Yellow
$initialSize = (Get-ChildItem -Recurse -File -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum).Sum / 1MB
Write-Host "   Current size: $([math]::Round($initialSize, 2)) MB" -ForegroundColor Gray

$freedSpace = 0

# ============================================================================
# 1. Delete auto-generated caches
# ============================================================================
Write-Host "`n1️⃣  Removing auto-generated caches..." -ForegroundColor Green

$cacheDirs = @(
    ".mypy_cache",
    ".pytest_cache",
    "src/__pycache__",
    "tests/__pycache__",
    "scripts/__pycache__"
)

foreach ($dir in $cacheDirs) {
    if (Test-Path $dir) {
        $size = (Get-ChildItem -Path $dir -Recurse -File -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum).Sum / 1MB
        Write-Host "   ├─ Removing: $dir ($([math]::Round($size, 2)) MB)" -ForegroundColor Gray
        
        if (-not $DryRun) {
            Remove-Item -Recurse -Force -ErrorAction SilentlyContinue $dir
            $freedSpace += $size
        }
    }
}

# ============================================================================
# 2. Clean old artifacts (keep 5 newest)
# ============================================================================
Write-Host "`n2️⃣  Cleaning old artifacts..." -ForegroundColor Green

if (Test-Path "artifacts") {
    cd artifacts
    $allArtifacts = Get-ChildItem -Directory | Sort-Object CreationTime -Descending
    
    if ($Aggressive) {
        $keepCount = 3
    } else {
        $keepCount = 5
    }
    
    $keep = $allArtifacts | Select-Object -First $keepCount
    $remove = $allArtifacts | Where-Object { $_.Name -notin $keep.Name }
    
    Write-Host "   ├─ Total artifacts: $($allArtifacts.Count)" -ForegroundColor Gray
    Write-Host "   ├─ Keeping: $keepCount" -ForegroundColor Gray
    Write-Host "   ├─ Removing: $($remove.Count)" -ForegroundColor Gray
    
    foreach ($dir in $remove) {
        $size = (Get-ChildItem -Path $dir.FullName -Recurse -File -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum).Sum / 1MB
        Write-Host "   │  └─ $($dir.Name) ($([math]::Round($size, 2)) MB)" -ForegroundColor DarkGray
        
        if (-not $DryRun) {
            Remove-Item -Recurse -Force $dir.FullName
            $freedSpace += $size
        }
    }
    cd ..
} else {
    Write-Host "   └─ No artifacts directory found" -ForegroundColor DarkGray
}

# ============================================================================
# 3. Archive old logs
# ============================================================================
Write-Host "`n3️⃣  Archiving old logs..." -ForegroundColor Green

if (Test-Path "logs") {
    $archiveDir = "archive/logs_feb2026"
    
    if (-not $DryRun) {
        New-Item -ItemType Directory -Force -Path $archiveDir | Out-Null
    }
    
    $oldLogs = Get-ChildItem logs/*.log -ErrorAction SilentlyContinue | 
               Where-Object { $_.CreationTime -lt (Get-Date).AddDays(-2) }
    
    if ($oldLogs) {
        $size = ($oldLogs | Measure-Object -Property Length -Sum).Sum / 1MB
        Write-Host "   ├─ Found $($oldLogs.Count) old logs ($([math]::Round($size, 2)) MB)" -ForegroundColor Gray
        
        if (-not $DryRun) {
            $oldLogs | Move-Item -Destination $archiveDir -Force
            Write-Host "   └─ Moved to: $archiveDir" -ForegroundColor Gray
            $freedSpace += $size
        }
    } else {
        Write-Host "   └─ No old logs found" -ForegroundColor DarkGray
    }
} else {
    Write-Host "   └─ No logs directory found" -ForegroundColor DarkGray
}

# ============================================================================
# 4. Move root scripts to archive
# ============================================================================
Write-Host "`n4️⃣  Moving root scripts to archive..." -ForegroundColor Green

$scriptsToArchive = @(
    "batch_process_all_datasets.py",
    "generate_summary_report.py"
)

$archiveDir = "archive/scripts_feb2026"

if (-not $DryRun) {
    New-Item -ItemType Directory -Force -Path $archiveDir | Out-Null
}

foreach ($script in $scriptsToArchive) {
    if (Test-Path $script) {
        $size = (Get-Item $script).Length / 1KB
        Write-Host "   ├─ $script ($([math]::Round($size, 2)) KB)" -ForegroundColor Gray
        
        if (-not $DryRun) {
            Move-Item -Force $script $archiveDir
            $freedSpace += ($size / 1024)
        }
    }
}

# ============================================================================
# 5. Move CSVs to archive
# ============================================================================
Write-Host "`n5️⃣  Moving research CSVs to archive..." -ForegroundColor Green

$csvsToArchive = @(
    "Comprehensive_Research_Paper_Table_Across_All_HAR_Topics.csv",
    "Summary_of_7_Research_Themes_in_HAR.csv"
)

$archiveDir = "archive/docs_feb2026"

if (-not $DryRun) {
    New-Item -ItemType Directory -Force -Path $archiveDir | Out-Null
}

foreach ($csv in $csvsToArchive) {
    if (Test-Path $csv) {
        $size = (Get-Item $csv).Length / 1KB
        Write-Host "   ├─ $csv ($([math]::Round($size, 2)) KB)" -ForegroundColor Gray
        
        if (-not $DryRun) {
            Move-Item -Force $csv $archiveDir
            $freedSpace += ($size / 1024)
        }
    }
}

# ============================================================================
# 6. Clean old outputs
# ============================================================================
Write-Host "`n6️⃣  Archiving old outputs..." -ForegroundColor Green

if (Test-Path "outputs") {
    $archiveDir = "archive/predictions_feb2026"
    
    if (-not $DryRun) {
        New-Item -ItemType Directory -Force -Path $archiveDir | Out-Null
    }
    
    $oldPredictions = Get-ChildItem outputs/predictions_20260212* -ErrorAction SilentlyContinue
    
    if ($oldPredictions) {
        $size = ($oldPredictions | Measure-Object -Property Length -Sum).Sum / 1MB
        Write-Host "   ├─ Found $($oldPredictions.Count) old prediction files ($([math]::Round($size, 2)) MB)" -ForegroundColor Gray
        
        if (-not $DryRun) {
            $oldPredictions | Move-Item -Destination $archiveDir -Force
            Write-Host "   └─ Moved to: $archiveDir" -ForegroundColor Gray
            $freedSpace += $size
        }
    } else {
        Write-Host "   └─ No old predictions found" -ForegroundColor DarkGray
    }
}

# ============================================================================
# 7. Clean old MLflow runs (aggressive mode only)
# ============================================================================
if ($Aggressive) {
    Write-Host "`n7️⃣  Cleaning old MLflow runs (aggressive)..." -ForegroundColor Green
    
    if (Test-Path "mlruns") {
        # Keep only the most recent experiment
        Write-Host "   ⚠️  Manual cleanup recommended for MLflow runs" -ForegroundColor Yellow
        Write-Host "   └─ Use MLflow UI to delete old experiments" -ForegroundColor Gray
    }
}

# ============================================================================
# Summary
# ============================================================================
Write-Host "`n═══════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  ✅ Cleanup Complete!" -ForegroundColor Green
Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Cyan

if ($DryRun) {
    Write-Host "`n⚠️  This was a DRY RUN - No files were actually deleted" -ForegroundColor Yellow
    Write-Host "   Run without -DryRun to perform actual cleanup" -ForegroundColor Gray
} else {
    Write-Host "`n📊 Space freed: $([math]::Round($freedSpace, 2)) MB" -ForegroundColor Cyan
    
    # Calculate final size
    $finalSize = (Get-ChildItem -Recurse -File -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum).Sum / 1MB
    Write-Host "   Before: $([math]::Round($initialSize, 2)) MB" -ForegroundColor Gray
    Write-Host "   After:  $([math]::Round($finalSize, 2)) MB" -ForegroundColor Gray
    Write-Host "   Saved:  $([math]::Round($initialSize - $finalSize, 2)) MB" -ForegroundColor Green
}

Write-Host "`n📝 Next steps:" -ForegroundColor Yellow
Write-Host "   1. Verify: git status" -ForegroundColor Gray
Write-Host "   2. Test:   pytest tests/" -ForegroundColor Gray
Write-Host "   3. Commit: git add -A && git commit -m 'chore: cleanup old artifacts'" -ForegroundColor Gray

Write-Host "`n═══════════════════════════════════════════════════════`n" -ForegroundColor Cyan
