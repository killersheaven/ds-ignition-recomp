# Building DSI Recomp (Windows)

## Requirements
- **Your own copy of Dead Space Ignition for Xbox 360 (XBLA)**: the STFS package for title ID
  `58410A7B`. Only this version is supported; `default.xex` must have SHA-1
  `451fea5e930d767fa3b770b1f80391881032c853` (full list in `docs/sha1_baseline.txt`).
- **Visual Studio 2022 or 2026 Build Tools** with the *Desktop development with C++* workload (MSVC, Windows SDK, CMake, Ninja).
- **LLVM / Clang 20 or newer.** Visual Studio 2022 bundles Clang 19, which is too old: `winget install LLVM.LLVM`
- **Git**
- **Python 3.10+** with `numpy`, `pillow` and `scipy` (for the extractor and the button/logo tools):
  `pip install numpy pillow scipy`
- A GPU with Direct3D 12 or Vulkan.

## 1. Extract the game
```
python tools\stfs_extract.py "<path to your 58410A7B package>" extracted
```
The extractor is resumable; run it again until it reports DONE. You should end up with 333 files (about 1.7 GB) in `extracted\`.

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

## 3. Button prompts and logo skip (optional)
Back up the originals first:
```
mkdir mods\original\HardwareCrack mods\original\SoftwareHack
copy extracted\Resource\SumoTool\subtitles_proj_EN.stz mods\original\
copy extracted\Resource\SumoTool\popups_EN.stz        mods\original\
copy extracted\Resource\SumoTool\Frontend_EN.stz      mods\original\
copy extracted\Resource\HardwareCrack\HardwareCrackSet.zi? mods\original\HardwareCrack\
copy extracted\Resource\SoftwareHack\SoftwareHackSet.zi?   mods\original\SoftwareHack\
copy extracted\Resource\Movies\EaHd.bik               mods\original\
```
Then build the sets from the originals:
```
python tools\make_button_mods.py mods\original <PS3 USRDIR>\resource\sumotool mods
python tools\minigame_buttons.py mods\original mods
python tools\bink_trim.py mods\original\EaHd.bik mods\skip_logos\EaHd.bik 1
```
`make_button_mods.py` currently needs the PS3 version's `resource\sumotool` folder, for the PS3 menu
and font symbols. A version with original artwork for players without a PS3 copy is planned.
The minigame sets need only the Xbox files (their PS3 symbols ship inside them).

Always build from the original files, never from files already modified by a set.

## 4. Play
Run `Launcher.bat`: pick the button prompts, optionally skip the logos, then press Play.
If you own the **full game** (not the trial), tick *I own the full game* once. It passes
`--license_mask=1`, and the launcher remembers it in `launcher_settings.json`. It is off by default. `play.bat` starts
the game directly. Game flags used: `--gpu_plugin=xenos --mnk_mode=true`. Run `dsignition.exe --help`
for all runtime options. The game log goes to `docs\run_windows.log`.
