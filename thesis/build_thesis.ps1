param(
    [switch]$Quick,
    [switch]$Clean,
    [switch]$OpenPdf
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$thesisRoot = $PSScriptRoot

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
            latexmk -c
        }
    }

    if (Get-Command latexmk -ErrorAction SilentlyContinue) {
        latexmk -pdf -interaction=nonstopmode -synctex=1 main.tex
    }
    else {
        pdflatex main.tex

        if (-not $Quick) {
            bibtex main
            pdflatex main.tex
            pdflatex main.tex
        }
    }

    if ($OpenPdf -and (Test-Path "main.pdf")) {
        Start-Process (Join-Path $thesisRoot "main.pdf")
    }

    Write-Host "Thesis build completed successfully."
}
finally {
    Pop-Location
}
