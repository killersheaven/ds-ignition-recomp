# Builds the DSI Recomp release zip (no game data) from a finished build_windows.ps1 build.
#   powershell -ExecutionPolicy Bypass -File .\make_release.ps1 [-Version 0.1.0]
# Needs Python 3.10+ (numpy, pillow and pyinstaller are installed with pip if missing).
# Output: release\DSI-Recomp-v<Version>-win64.zip
param([string]$Version = "0.1.0")
$ErrorActionPreference = "Stop"
$root = $PSScriptRoot
$exeDir = Join-Path $root "port\out\build\win-amd64-release"
$name = "DSI-Recomp-v$Version-win64"
$out = Join-Path $root "release"
$stage = Join-Path $out $name

function Log($m) { Write-Host "[release] $m" }
function Run($exe) {
    & $exe @args
    if ($LASTEXITCODE -ne 0) { throw "$exe $args failed with exit code $LASTEXITCODE" }
}

if (-not (Test-Path "$exeDir\dsignition.exe")) { throw "No build found. Run build_windows.ps1 first." }

# 1. Setup.exe (Python tools frozen with PyInstaller)
Log "Building Setup.exe"
Run python -m pip install --quiet --disable-pip-version-check numpy pillow pyinstaller
$work = Join-Path $out "pyinstaller"
Run python -m PyInstaller --noconfirm --clean --onefile --windowed --name Setup `
    --icon (Join-Path $root "branding\dsi.ico") `
    --distpath (Join-Path $out "dist") --workpath $work --specpath $work `
    --paths (Join-Path $root "tools") `
    --add-data "$(Join-Path $root 'tools\fonts');fonts" `
    --add-data "$(Join-Path $root 'docs\sha1_baseline.txt');." `
    --exclude-module scipy --exclude-module matplotlib `
    (Join-Path $root "tools\setup.py")

# 2. stage the release folder
Log "Staging $name"
if (Test-Path $stage) { Remove-Item -Recurse -Force $stage }
New-Item -ItemType Directory -Force $stage, "$stage\bin\branding", "$stage\bin\fonts", "$stage\tools\launcher", "$stage\branding", "$stage\docs" | Out-Null
Copy-Item (Join-Path $out "dist\Setup.exe") $stage
Copy-Item "$exeDir\dsignition.exe" "$stage\bin"
Get-ChildItem $exeDir -Filter *.dll | Copy-Item -Destination "$stage\bin"
Copy-Item (Join-Path $root "branding\killers_heaven_on_dark.png") "$stage\bin\branding"
Copy-Item (Join-Path $root "tools\fonts\*.ttf") "$stage\bin\fonts"
Copy-Item (Join-Path $root "branding\launcher_logo.png") "$stage\branding"
Copy-Item (Join-Path $root "branding\dsi.ico") "$stage\branding"
& (Join-Path $root "tools\launcher\build_launcher_exe.ps1") -OutFile (Join-Path $stage "DSI Recomp.exe")
Copy-Item (Join-Path $root "tools\launcher\launcher.ps1") "$stage\tools\launcher"
Copy-Item (Join-Path $root "docs\sha1_baseline.txt") "$stage\docs"
foreach ($f in "Launcher.bat", "play.bat", "buttons.bat", "CREDITS.md", "LICENSE") { Copy-Item (Join-Path $root $f) $stage }
Copy-Item (Join-Path $root "licenses") $stage -Recurse
# license texts of the Python parts frozen into Setup.exe, from the installed versions
$py = @'
import sys, os, shutil, importlib.metadata as md
dst = sys.argv[1]
lic = os.path.join(sys.base_prefix, 'LICENSE.txt')
if os.path.exists(lic): shutil.copyfile(lic, os.path.join(dst, 'python-LICENSE.txt'))
for pkg in ('numpy', 'pillow', 'pyinstaller'):
    d = md.distribution(pkg)
    for f in d.files or []:
        n = f.name.lower()
        if ('license' in n or 'copying' in n) and '.dist-info' in str(f):
            shutil.copyfile(f.locate(), os.path.join(dst, f'{pkg}-{d.version}-{f.name}'))
'@
$py | Set-Content (Join-Path $work "copy_licenses.py") -Encoding ASCII
Run python (Join-Path $work "copy_licenses.py") "$stage\licenses"
Copy-Item (Join-Path $root "release_readme.txt") (Join-Path $stage "README.txt")

# 3. zip
$zip = Join-Path $out "$name.zip"
if (Test-Path $zip) { Remove-Item $zip }
# Entries written one by one with "/" paths: Windows PowerShell 5 runs on .NET Framework, whose
# ZipFile.CreateFromDirectory (and Compress-Archive) store "\\" paths that non-Windows unzip tools mishandle.
Add-Type -AssemblyName System.IO.Compression, System.IO.Compression.FileSystem
$fs = [System.IO.File]::Open($zip, [System.IO.FileMode]::Create)
$za = New-Object System.IO.Compression.ZipArchive($fs, [System.IO.Compression.ZipArchiveMode]::Create)
try {
    $base = (Split-Path $stage -Parent).TrimEnd('\') + '\'
    Get-ChildItem $stage -Recurse -File | ForEach-Object {
        $entry = $_.FullName.Substring($base.Length) -replace '\\', '/'
        [void][System.IO.Compression.ZipFileExtensions]::CreateEntryFromFile($za, $_.FullName, $entry,
            [System.IO.Compression.CompressionLevel]::Optimal)
    }
} finally { $za.Dispose(); $fs.Dispose() }
$mb = [math]::Round((Get-Item $zip).Length / 1MB, 1)
Log "DONE: $zip ($mb MB)"
