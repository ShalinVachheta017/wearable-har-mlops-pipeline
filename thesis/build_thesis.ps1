param(
    [switch]$Quick,
    [switch]$Clean,
    [switch]$OpenPdf
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$thesisRoot = $PSScriptRoot

function Invoke-NativeProcess {
    param(
        [Parameter(Mandatory = $true)][string]$Name,
        [Parameter(Mandatory = $true)][string]$FilePath,
        [Parameter(Mandatory = $true)][string[]]$ArgumentList
    )

    $proc = Start-Process -FilePath $FilePath -ArgumentList $ArgumentList -Wait -NoNewWindow -PassThru
    if ($proc.ExitCode -ne 0) {
        throw "$Name failed with exit code $($proc.ExitCode)."
    }
}

function Invoke-PdfLatex {
    param(
        [Parameter(Mandatory = $true)][string]$Name
    )

    $proc = Start-Process -FilePath "pdflatex" -ArgumentList @("-interaction=nonstopmode", "main.tex") -Wait -NoNewWindow -PassThru

    if ($proc.ExitCode -eq 0) {
        return
    }

    if (-not (Test-Path "main.pdf")) {
        throw "$Name failed with exit code $($proc.ExitCode) and no PDF output."
    }

    if (Test-Path "main.log") {
        $logText = Get-Content "main.log" -Raw
        if ($logText -match "! LaTeX Error:" -or $logText -match "! Package .* Error:" -or $logText -match "Emergency stop") {
            throw "$Name failed with LaTeX errors. Check main.log for details."
        }
    }

    Write-Warning "$Name returned exit code $($proc.ExitCode), but PDF was generated and no fatal LaTeX errors were detected."
}

Push-Location $thesisRoot
try {
    if ($Clean) {
        $auxFiles = @(
            "main.aux",
            "main.bbl",
            "main.blg",
            "main.log",
            "main.toc",
            "main.synctex.gz"
        )
        Remove-Item $auxFiles -ErrorAction SilentlyContinue

        if (Get-Command latexmk -ErrorAction SilentlyContinue) {
            try {
                Invoke-NativeProcess -Name "latexmk clean" -FilePath "latexmk" -ArgumentList @("-c")
            }
            catch {
                Write-Warning "latexmk clean failed; continuing without latexmk clean step."
            }
        }
    }

    $built = $false

    if (Get-Command latexmk -ErrorAction SilentlyContinue) {
        try {
            Invoke-NativeProcess -Name "latexmk build" -FilePath "latexmk" -ArgumentList @("-pdf", "-interaction=nonstopmode", "-synctex=1", "main.tex")
            if (Test-Path "main.pdf") {
                $built = $true
            }
        }
        catch {
            Write-Warning "latexmk build failed; falling back to pdflatex/bibtex sequence."
        }
    }

    if (-not $built) {
        Invoke-PdfLatex -Name "pdflatex pass 1"

        if (-not $Quick) {
            Invoke-NativeProcess -Name "bibtex" -FilePath "bibtex" -ArgumentList @("main")
            Invoke-PdfLatex -Name "pdflatex pass 2"
            Invoke-PdfLatex -Name "pdflatex pass 3"
        }

        $built = Test-Path "main.pdf"
    }

    if (-not $built) {
        throw "Build completed without producing main.pdf."
    }

    if ($OpenPdf -and (Test-Path "main.pdf")) {
        Start-Process (Join-Path $thesisRoot "main.pdf")
    }

    $global:LASTEXITCODE = 0
    Write-Host "Thesis build completed successfully."
}
finally {
    Pop-Location
}
