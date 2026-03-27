$ErrorActionPreference = 'Stop'

$root = (Get-Location).Path
$outFile = Join-Path $root 'repo_summary.txt'

function Get-Indent {
    param([int]$Level)
    return ('  ' * $Level)
}

function Write-Tree {
    param(
        [System.IO.DirectoryInfo]$Dir,
        [int]$Level,
        [System.IO.StreamWriter]$Writer
    )

    $children = Get-ChildItem -LiteralPath $Dir.FullName -Force | Sort-Object @{ Expression = { -not $_.PSIsContainer } }, Name
    foreach ($child in $children) {
        $indent = Get-Indent -Level $Level
        if ($child.PSIsContainer) {
            $Writer.WriteLine("$indent+ $($child.Name)/")
            Write-Tree -Dir $child -Level ($Level + 1) -Writer $Writer
        }
        else {
            $Writer.WriteLine("$indent- $($child.Name)")
        }
    }
}

function Is-LikelyBinary {
    param([string]$Path)

    try {
        $stream = [System.IO.File]::OpenRead($Path)
        try {
            $sampleSize = [Math]::Min(4096, [int]$stream.Length)
            if ($sampleSize -le 0) { return $false }

            $buffer = New-Object byte[] $sampleSize
            [void]$stream.Read($buffer, 0, $sampleSize)

            foreach ($b in $buffer) {
                if ($b -eq 0) { return $true }
            }

            return $false
        }
        finally {
            $stream.Dispose()
        }
    }
    catch {
        return $true
    }
}

function Get-FilePurpose {
    param([System.IO.FileInfo]$File)

    $ext = $File.Extension.ToLowerInvariant()
    switch ($ext) {
        '.py' { return 'Python source code: implements logic, pipeline stages, utilities, or tests.' }
        '.ipynb' { return 'Jupyter notebook: exploratory analysis, experiments, or documentation with executable cells.' }
        '.md' { return 'Markdown documentation: notes, plans, reports, or project guidance.' }
        '.txt' { return 'Text file: plain notes, logs, summaries, or lightweight documentation.' }
        '.yml' { return 'YAML configuration: service orchestration, monitoring, alerts, or pipeline settings.' }
        '.yaml' { return 'YAML configuration: service orchestration, monitoring, alerts, or pipeline settings.' }
        '.toml' { return 'TOML configuration: project metadata, tooling, or dependency settings.' }
        '.ini' { return 'INI configuration: test runner or tool configuration values.' }
        '.json' { return 'JSON data/configuration: structured settings, reports, or metadata.' }
        '.csv' { return 'CSV dataset/report: tabular data used for training, evaluation, or reporting.' }
        '.ps1' { return 'PowerShell script: automation for setup, cleanup, or repository operations.' }
        '.sh' { return 'Shell script: automation for environment or workflow commands.' }
        '.dockerfile' { return 'Docker build file: container image build instructions.' }
        '.dvc' { return 'DVC tracking file: data/artifact version pointer used by DVC.' }
        '.keras' { return 'Serialized model artifact: trained model file for inference or rollback.' }
        '.h5' { return 'Serialized model artifact: trained model weights or model package.' }
        '.npy' { return 'NumPy artifact: array data for prepared features, labels, or intermediate outputs.' }
        '.pkl' { return 'Pickle artifact: serialized Python object used by pipeline or models.' }
        '.png' { return 'Image asset: chart, figure, or UI screenshot for reports/documentation.' }
        '.jpg' { return 'Image asset: chart, figure, or UI screenshot for reports/documentation.' }
        '.jpeg' { return 'Image asset: chart, figure, or UI screenshot for reports/documentation.' }
        '.pdf' { return 'PDF document: paper, report, thesis resource, or generated output.' }
        '.tex' { return 'LaTeX source: thesis/report chapter or formatting definitions.' }
        '.bib' { return 'BibTeX bibliography: citation entries for thesis/report writing.' }
        default {
            switch ($File.Name.ToLowerInvariant()) {
                'docker-compose.yml' { return 'Docker Compose definition: multi-service local stack orchestration.' }
                'dockerfile' { return 'Docker build file: container image build instructions.' }
                'readme.md' { return 'Top-level project overview and usage documentation.' }
                'makefile' { return 'Build automation definitions and shortcut commands.' }
                'setup.py' { return 'Python packaging/setup script defining installable project metadata.' }
                'pyproject.toml' { return 'Python project and tooling configuration; may include dependencies.' }
                default { return 'Project file: purpose inferred from location and extension; likely config, code, data, or artifact.' }
            }
        }
    }
}

function Parse-Imports {
    param(
        [string]$Content,
        [string]$Ext
    )

    $imports = New-Object System.Collections.Generic.HashSet[string]

    if ([string]::IsNullOrWhiteSpace($Content)) {
        return $imports
    }

    $lines = $Content -split "`r?`n"

    if ($Ext -eq '.py') {
        foreach ($line in $lines) {
            if ($line -match '^\s*import\s+(.+)$') {
                $parts = $Matches[1] -split ','
                foreach ($p in $parts) {
                    $name = (($p -split '\s+as\s+')[0]).Trim()
                    if ($name) { [void]$imports.Add($name) }
                }
            }
            elseif ($line -match '^\s*from\s+([A-Za-z0-9_\.]+)\s+import\s+') {
                [void]$imports.Add($Matches[1].Trim())
            }
        }
    }
    elseif ($Ext -in @('.js', '.jsx', '.ts', '.tsx', '.mjs', '.cjs')) {
        foreach ($line in $lines) {
            if ($line -match '^\s*import\s+.*?from\s+["'']([^"'']+)["'']') {
                [void]$imports.Add($Matches[1].Trim())
            }
            elseif ($line -match '^\s*import\s+["'']([^"'']+)["'']') {
                [void]$imports.Add($Matches[1].Trim())
            }
            elseif ($line -match 'require\(["'']([^"'']+)["'']\)') {
                [void]$imports.Add($Matches[1].Trim())
            }
        }
    }

    return $imports
}

function Parse-Definitions {
    param(
        [string]$Content,
        [string]$Ext
    )

    $defs = New-Object System.Collections.Generic.List[string]

    if ([string]::IsNullOrWhiteSpace($Content)) {
        return $defs
    }

    $lines = $Content -split "`r?`n"

    if ($Ext -eq '.py') {
        foreach ($line in $lines) {
            if ($line -match '^\s*def\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(') {
                $defs.Add("function: $($Matches[1])")
            }
            elseif ($line -match '^\s*class\s+([A-Za-z_][A-Za-z0-9_]*)\s*(\(|:)') {
                $defs.Add("class: $($Matches[1])")
            }
        }
    }
    elseif ($Ext -in @('.js', '.jsx', '.ts', '.tsx', '.mjs', '.cjs')) {
        foreach ($line in $lines) {
            if ($line -match '^\s*function\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(') {
                $defs.Add("function: $($Matches[1])")
            }
            elseif ($line -match '^\s*class\s+([A-Za-z_][A-Za-z0-9_]*)\s*') {
                $defs.Add("class: $($Matches[1])")
            }
            elseif ($line -match '^\s*(?:const|let|var)\s+([A-Za-z_][A-Za-z0-9_]*)\s*=\s*\(?.*?\)?\s*=>') {
                $defs.Add("function: $($Matches[1])")
            }
        }
    }

    return $defs
}

function Get-DependenciesFromKnownFiles {
    param([System.IO.FileInfo[]]$Files)

    $deps = New-Object System.Collections.Generic.HashSet[string]

    foreach ($f in $Files) {
        $name = $f.Name.ToLowerInvariant()
        try {
            if ($name -match '^requirements.*\.txt$') {
                foreach ($line in (Get-Content -LiteralPath $f.FullName -ErrorAction Stop)) {
                    $trim = $line.Trim()
                    if (-not $trim -or $trim.StartsWith('#')) { continue }
                    $pkg = ($trim -split '[<>=!~\[]')[0].Trim()
                    if ($pkg) { [void]$deps.Add($pkg) }
                }
            }
            elseif ($name -eq 'pyproject.toml') {
                foreach ($line in (Get-Content -LiteralPath $f.FullName -ErrorAction Stop)) {
                    if ($line -match '^\s*([A-Za-z0-9_\-]+)\s*=\s*"[^"]+"\s*$') {
                        $k = $Matches[1]
                        if ($k -notin @('name', 'version', 'description', 'requires-python', 'readme')) {
                            [void]$deps.Add($k)
                        }
                    }
                }
            }
            elseif ($name -eq 'setup.py') {
                $content = Get-Content -LiteralPath $f.FullName -Raw -ErrorAction Stop
                $regex = [regex]'["'']([A-Za-z0-9_\-]+)(?:[<>=!~].*?)?["'']'
                foreach ($m in $regex.Matches($content)) {
                    $pkg = $m.Groups[1].Value
                    if ($pkg -and $pkg -notin @('name', 'version', 'description')) {
                        [void]$deps.Add($pkg)
                    }
                }
            }
            elseif ($name -eq 'package.json') {
                $json = Get-Content -LiteralPath $f.FullName -Raw -ErrorAction Stop | ConvertFrom-Json
                if ($json.dependencies) {
                    foreach ($p in $json.dependencies.PSObject.Properties.Name) { [void]$deps.Add($p) }
                }
                if ($json.devDependencies) {
                    foreach ($p in $json.devDependencies.PSObject.Properties.Name) { [void]$deps.Add($p) }
                }
            }
        }
        catch {
            # Ignore parser errors for dependency aggregation.
        }
    }

    return $deps
}

$allFiles = Get-ChildItem -LiteralPath $root -Recurse -File -Force | Sort-Object FullName
$totalFiles = $allFiles.Count

$writer = New-Object System.IO.StreamWriter($outFile, $false, [System.Text.Encoding]::UTF8)
try {
    $writer.WriteLine("Repository Summary")
    $writer.WriteLine("Generated: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')")
    $writer.WriteLine("Root: $root")
    $writer.WriteLine("Total files: $totalFiles")
    $writer.WriteLine('')

    $writer.WriteLine('=== FULL FOLDER STRUCTURE (TREE) ===')
    $writer.WriteLine("+ $(Split-Path -Path $root -Leaf)/")
    Write-Tree -Dir (Get-Item -LiteralPath $root) -Level 1 -Writer $writer
    $writer.WriteLine('')

    $globalImports = New-Object System.Collections.Generic.HashSet[string]

    $writer.WriteLine('=== PER-FILE DETAILS ===')
    foreach ($file in $allFiles) {
        $ext = $file.Extension.ToLowerInvariant()
        $purpose = Get-FilePurpose -File $file

        $writer.WriteLine('------------------------------------------------------------')
        $writer.WriteLine("Full file path: $($file.FullName)")
        $writer.WriteLine("Purpose: $purpose")

        $isBinary = Is-LikelyBinary -Path $file.FullName
        if ($isBinary) {
            $writer.WriteLine('First 30 lines of code: [Binary or non-text file; preview omitted]')
            $writer.WriteLine('Any imports used: [Not applicable for binary/non-text file]')
            $writer.WriteLine('Any functions or classes defined: [Not applicable for binary/non-text file]')
            $writer.WriteLine('')
            continue
        }

        $content = ''
        try {
            $content = Get-Content -LiteralPath $file.FullName -Raw -ErrorAction Stop
        }
        catch {
            $writer.WriteLine('First 30 lines of code: [Unable to read text content]')
            $writer.WriteLine('Any imports used: [Unavailable due to read error]')
            $writer.WriteLine('Any functions or classes defined: [Unavailable due to read error]')
            $writer.WriteLine('')
            continue
        }

        $lines = $content -split "`r?`n"
        $first30 = $lines | Select-Object -First 30

        $writer.WriteLine('First 30 lines of code:')
        if ($first30.Count -eq 0) {
            $writer.WriteLine('[Empty file]')
        }
        else {
            foreach ($line in $first30) {
                $writer.WriteLine($line)
            }
        }

        $imports = Parse-Imports -Content $content -Ext $ext
        if ($imports.Count -gt 0) {
            foreach ($imp in $imports) { [void]$globalImports.Add($imp) }
            $writer.WriteLine("Any imports used: $(([string[]]$imports | Sort-Object) -join ', ')")
        }
        else {
            $writer.WriteLine('Any imports used: [None detected]')
        }

        $defs = Parse-Definitions -Content $content -Ext $ext
        if ($defs.Count -gt 0) {
            $writer.WriteLine("Any functions or classes defined: $(([string[]]$defs) -join '; ')")
        }
        else {
            $writer.WriteLine('Any functions or classes defined: [None detected]')
        }

        $writer.WriteLine('')
    }

    $depsFromFilesRaw = Get-DependenciesFromKnownFiles -Files $allFiles
    $depsFromFiles = New-Object System.Collections.Generic.HashSet[string]
    foreach ($d in $depsFromFilesRaw) {
        if (-not [string]::IsNullOrWhiteSpace($d)) {
            [void]$depsFromFiles.Add($d)
        }
    }
    foreach ($imp in $globalImports) {
        if ($imp -notmatch '^[\./]') {
            [void]$depsFromFiles.Add($imp)
        }
    }

    $writer.WriteLine('=== LIST OF ALL DEPENDENCIES FOUND ===')
    if ($depsFromFiles.Count -eq 0) {
        $writer.WriteLine('[No dependencies detected]')
    }
    else {
        foreach ($d in ([string[]]$depsFromFiles | Sort-Object)) {
            $writer.WriteLine("- $d")
        }
    }
}
finally {
    $writer.Flush()
    $writer.Dispose()
}

Write-Output "Summary generated at: $outFile"