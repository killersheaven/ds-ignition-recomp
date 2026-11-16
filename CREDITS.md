# DSI Recomp - Credits and Copyright

## DSI Recomp
**Native PC recompilation by Killers' Heaven™**
Started November 10, 2026. Release date: see the version in the launcher's About box.

DSI Recomp is an unofficial, non-commercial fan project. It is not affiliated with,
endorsed by or sponsored by Electronic Arts Inc., Visceral Games, Sumo Digital Ltd.,
Microsoft Corporation, Sony Interactive Entertainment or Epic Games Tools LLC.
It contains no game data: you need your own legally obtained copy of the
Xbox 360 game.

Killers' Heaven and the Killers' Heaven logo are trademarks of Killers' Heaven.

## The original game
**Dead Space™ Ignition** © 2010 Electronic Arts Inc. All rights reserved.
- Developed by **Sumo Digital Ltd.**
- Published by **Electronic Arts Inc.**
- Based on the Dead Space universe created by **Visceral Games** (EA Redwood Shores)

Dead Space, EA and the EA logo are trademarks of Electronic Arts Inc. Visceral Games
is a trademark of Electronic Arts Inc. All game code, art, audio, video and text belong
to their respective owners. The prebuilt `dsignition.exe` contains machine code
recompiled from the original Xbox 360 executable and remains the property of
Electronic Arts Inc. It is not covered by this project's license.

**Bink Video** - the game's movie player - © RAD Game Tools, Inc. / Epic Games Tools LLC.

## Platforms and trademarks
- Xbox, Xbox 360, Xbox LIVE and Xbox LIVE Arcade are trademarks of the Microsoft group of companies.
- PlayStation, PS3, and the PlayStation shape symbols (Cross, Circle, Square, Triangle)
  are trademarks or registered trademarks of Sony Interactive Entertainment Inc.
  The optional PlayStation button prompts are generated on your PC from the game files
  you supply; this project does not distribute Sony or EA artwork.
- Windows, DirectX and Direct3D are trademarks of Microsoft Corporation.
- Vulkan is a registered trademark of the Khronos Group Inc.

## Technology
- **ReXGlue SDK** - static recompilation toolchain and runtime.
  © 2026 Tom Clay. BSD 3-Clause License.
- **Xenia** - Xbox 360 research project. The ReXGlue runtime (kernel, GPU and audio emulation) is derived from it.
  © 2022 Ben Vanik and Xenia project contributors. BSD 3-Clause License.
- **XenonRecomp / XenonAnalyse** (hedge-dev) - used during early research. Not included in releases.

## Third-party libraries in the release
These ship inside the ReXGlue runtime (`rexruntime.dll`, `rexgpu-xenos.dll`). Their full license texts are in `licenses/`.

| Library | License |
|---|---|
| SDL 3 | zlib |
| FFmpeg (libavcodec, libavutil - WMA Pro audio only) | LGPL 2.1 or later |
| libmspack (LZX decompression) | LGPL 2.1 |
| fmt | MIT |
| spdlog | MIT |
| Dear ImGui | MIT |
| toml++ | MIT |
| inja | MIT |
| o1heap | MIT |
| Vulkan Memory Allocator | MIT |
| SIMDe | MIT |
| tiny-AES-c / aes_128 | Unlicense / MIT |
| glslang | BSD 3-Clause |
| SPIRV-Tools, SPIRV-Headers | Apache 2.0 / MIT |
| Vulkan Loader, Vulkan Headers | Apache 2.0 |
| DirectX Shader Compiler (dxc) | University of Illinois/NCSA |
| xxHash | BSD 2-Clause |
| utfcpp | Boost Software License 1.0 |
| CLI11 | BSD 3-Clause |
| stb | Public domain / MIT |

LGPL components: the source for FFmpeg, libmspack and the ReXGlue runtime that links
them is available at the ReXGlue SDK repository (https://github.com/rexglue/rexglue-sdk),
at the commit listed in `BUILD.md`. You can rebuild the runtime with modified versions
of these libraries using `build_windows.ps1`.

Not included in releases: the GNU binutils PowerPC disassembler (GPL) and Tracy are used
only by development tools.

## Killers' Heaven tools (this repository)
- STFS package extractor, XEX tools
- .stz / .zif / .zig texture exporter and patcher
- Button prompt sets: PlayStation layout and keyboard keycaps (keyboard artwork is original)
- Bink logo-skip trimmer, launcher, setup and build scripts
