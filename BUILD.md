# Building DSI Recomp (Windows)

## Requirements
- **Your own copy of Dead Space Ignition for Xbox 360 (XBLA)**: the STFS package for title ID
  `58410A7B`. Only this version is supported; `default.xex` must have SHA-1
  `451fea5e930d767fa3b770b1f80391881032c853` (full list in `docs/sha1_baseline.txt`).
- **Visual Studio 2022 or 2026 Build Tools** with the *Desktop development with C++* workload (MSVC, Windows SDK, CMake, Ninja).
- **LLVM / Clang 20 or newer.** Visual Studio 2022 bundles Clang 19, which is too old: `winget install LLVM.LLVM`
- **Git**
- **Python 3.10+** with `numpy` and `pillow` (for the setup and button/logo tools): `pip install numpy pillow`
- A GPU with Direct3D 12 or Vulkan.

## 1. Set up the game files
```
python tools\setup.py --package "<path to your 58410A7B package>"
```
(Run `python tools\setup.py` without arguments for the setup window.) It extracts the package into
`extracted\` (333 files, about 1.7 GB), checks every file against `docs\sha1_baseline.txt`, backs up the
files the launcher swaps into `mods\original\`, and builds the button-prompt sets and the logo skip in
`mods\`. Add `--ps3 <PS3 USRDIR\resource\sumotool>` to use the PS3 version's own PlayStation symbols
instead of the ones DSI Recomp draws. Running it again is safe.

## 2. Build
From any PowerShell window:
```
powershell -ExecutionPolicy Bypass -File .\build_windows.ps1
```
The script:
1. sets up the 64-bit Visual Studio environment itself;
2. picks the newest Clang;
3. clones the ReXGlue SDK at commit **`546a082`** (v0.10.0-dev) into `rexglue-sdk\`, then builds and installs it;
4. generates and compiles the game code from `extracted\default.xex`;
5. copies the runtime DLLs and the splash logo next to the exe and writes `play.bat`.

The first build takes 20 to 40 minutes. Output: `port\out\build\win-amd64-release\dsignition.exe`.
All output is logged to `docs\build_windows.log`.

Known issue: Git on Windows checks out the SDK's libmspack symlinks as small text files, which fails
with `lzxd.c:1:1: error: expected identifier`. Replace each placeholder with the file it points to,
or clone with symlinks enabled (Windows Developer Mode + `git config --global core.symlinks true`).

## 3. Release zip (optional)
```
powershell -ExecutionPolicy Bypass -File .\make_release.ps1 -Version 0.1.0
```
Builds `Setup.exe` with PyInstaller (installed with pip if missing) and writes
`release\DSI-Recomp-v0.1.0-win64.zip`: the game exe and DLLs in `bin\`, Setup.exe, the launcher,
README, credits and licenses. No game data.

The individual tools still work on their own (`tools\make_button_mods.py`, `tools\minigame_buttons.py`,
`tools\bink_trim.py`, `tools\stfs_extract.py`); always build sets from the original files.

## Play
Run `Launcher.bat`: pick the button prompts, optionally skip the logos, then press Play.
If you own the **full game** (not the trial), tick *I own the full game* once. It passes
`--license_mask=1`, and the launcher remembers it in `launcher_settings.json`. It is off by default. `play.bat` starts
the game directly. Game flags used: `--gpu_plugin=xenos --mnk_mode=true`. Run `dsignition.exe --help`
for all runtime options. The game log goes to `docs\run_windows.log`.
