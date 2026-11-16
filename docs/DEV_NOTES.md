# Dead Space Ignition PC port - handoff notes (2026-11-10)

## State
- Source: `Dead Space - Ignition (World) (XBLA)/58410A7B/000D0000/339D56EC...` = LIVE (STFS) package, title ID 58410A7B, 1.7 GB, 348 entries.
- `tools/stfs_extract.py <package> <outdir> [--list]` - working STFS extractor (written this session, read-only package, all files consecutive). RESUMABLE: skips files already extracted at the right size.
- `docs/package_listing.txt` - full file listing of the package (size, start block, path).
- `extracted/` - COMPLETE (333 files, 1.7 GB).

## Next step (do first)
Re-run until it prints DONE (about 8-10 more calls):
    timeout 170 python3 tools/stfs_extract.py "<package path>" extracted | tail -3
Delete nothing; a leftover `*.part` file is just an interrupted write and gets overwritten.

## Then
1. Hash everything (sha1) into docs/ as the baseline.
2. default.xex (2,383,872 bytes): parse XEX2 headers (build date, imports, compression/encryption), decrypt/decompress to a basefile, strings sweep.
3. Identify formats: .xpac (audio), .zif/.zig (asset sets), .stz (SumoTool UI, per-language), .dat/.gpu/.rel triplets, .crack / .tur (minigame level data), .bik (Bink video).
4. Recomp route to evaluate: XenonRecomp / XenonAnalyse (static PPC -> C++), plus a D3D9-Xenon shim.

## Leads already spotted in the listing (unverified, names only)
- HardwareCrack/: `mp_test1-5.crack`, `ScratchPad1-3.crack`, `test`, `test1` - look like dev/test levels.
- PacketAttack/: `mp_map1-5.tur` - multiplayer maps.
- Resource/Shaders/*.hlsl - plain-text HLSL source shipped in the package (incl. `snow.hlsl`, `Plant1.hlsl`, which sound unrelated to this game - possibly leftovers from another Sumo title).
- Resource/SumoTool/ - Sumo Digital in-house tooling formats.
- Root `PC.png` among the icon PNGs - almost certainly an achievement icon abbreviation, not a PC-port hint; check ArcadeInfo.xml.
- A `ShaderCache/` and `scripts/` directory exist; contents not yet reviewed.

## RESOLVED - overlapping extractor runs
Extraction completed; all 333 files present, no .part leftovers, no zero-filled 4K blocks in any .bik, so the overlap did no detectable damage. The steps below are no longer needed (full STFS hash verification is still optional).

### Original warning
Three extractor runs were launched concurrently by mistake at about 15:09, all writing the same `.part` files. Files extracted from `Resource/Movies/Comic2A_2.bik` onward may be CORRUPT (zero-filled holes) even if their size is correct. Everything before that file is fine.
Fix before doing anything else:
1. Make sure no `stfs_extract.py` process is still running.
2. Remove (or move to `_to_delete/`) every file in `extracted/Resource/` from `Movies/Comic2A_2.bik` onward in package order (see docs/package_listing.txt), plus any `*.part` files. Deleting needs the delete permission in the device shell; otherwise move them.
3. Re-run the extractor ONE call at a time until it prints DONE.
4. Ideally add SHA-1 verification of each data block against the STFS level-0 hash tables to the extractor, and verify the whole extraction.

## Session 2 (2026-11-10)
- Step 1 DONE: `docs/sha1_baseline.txt` (333 files). default.xex sha1 451fea5e930d767fa3b770b1f80391881032c853.
- XEX2 headers parsed with `tools/xex_info.py` -> `docs/xex_info.txt`:
  - Original PE: GameCode_Xbox360_f.exe, built 2010-09-01, XDK 2.0.11626, VS2010 compiler (C1/C2 16.0).
  - Image base 0x82000000, image size 0x11A0000 (~17.6 MB), entry 0x8214D2F0.
  - AES encrypted (retail), LZX compressed (window 0x8000). Imports only xam.xex + xboxkrnl.exe.
  - Static libs: D3D9/D3DX9/XGRAPHICS, XAudio2/X3DAudio/XAPOBase/XMCore, XMP, XHV2, XOnline/XNet, Avatar (XAVATAR/XAVATRV1), XFFB.
- Next: decrypt + LZX-decompress to a PE basefile (XenonRecomp's XenonUtils or emoose's xex1tool can do this), then strings sweep and XenonAnalyse.
- PC tools check (docs/tools_check.txt): VS Build Tools 2026 (MSVC), Git, Python 3.15, MinGW cmake/ninja on PATH (use Developer PowerShell for VS to avoid them), RTX 4070, old xenia_master in Downloads. User installing VS 2022 Community + Clang tools; Xenia Canary recommended.
- XenonRecomp + XenonAnalyse build cleanly (clang 18, Linux cloud container).
- default.xex UNPACKED via XenonUtils Xex2LoadImage (tools/xexdump.cpp) -> work/default_image.bin (18,481,152 bytes, sha1 622765d7089bd305fff75e111ee5460c8ccd50c1), mapped at 0x82000000.
  Sections: .rdata 0x82000400, .pdata 0x820F4000, .text 0x82110000 (0x3D3ADC = ~4 MB code), BINK 0x824E3C00 (Bink code), .data 0x82500400 (0xC6969C), .idata, .XBLD, .reloc.
- Strings: docs/default_strings.txt. Leftover dev command-line switches in docs/cmdline_switches.txt (-unlock all|racers|tracks|missions|extras, -num_laps, -no_ai_racers, -packetattack <file>, -quickstart, -debug_hud, -30hz, -tty...). The racers/tracks/laps switches suggest the engine is shared with a Sumo Digital racing title.
- Next: XenonAnalyse on the xex -> jump tables; write the XenonRecomp TOML (needs save/restore gpr/fpr/vmx addresses + setjmp/longjmp); recompile.
- XenonAnalyse ran but found 0 jump tables. Its patterns are tuned to Sonic Unleashed's compiler output. The image has 364 `bctr` sites in .text; the common lead-ins (lis/addi ... rlwinm ... lwzx/mtctr) look like ordinary switch tables, so we need our own jump-table finder (or to extend XenonAnalyse's patterns) before recompiling.
- Game boots in Xenia Canary (user confirmed it launches; not yet played).
- tools/find_switches.py: custom jump-table finder (concrete evaluation of the block before each bctr; handles lwzx absolute, lbzx/lhzx offset tables, bgt/ble/bgtlr bounds, mr copies of the index reg, unbounded tables sized by function bounds). 161 tables -> recomp/switch_tables.toml (stock XenonAnalyse: 0). The 205 other bctr are vtable/function-pointer calls.
- Save/restore helpers: savegprlr_14 0x823521E0, restgprlr_14 0x82352230, savefpr_14 0x82352F90, restfpr_14 0x82352FDC, savevmx_14 0x82353400, restvmx_14 0x82353698, savevmx_64 0x82353494, restvmx_64 0x8235372C. setjmp/longjmp not yet located.
- recomp/config.toml written. FIRST FULL RECOMPILE RAN (2 s, 65 MB of C++, built in the cloud container, not kept on the PC). Problems:
  1. 1457 unrecognized instructions across 28 opcodes that upstream XenonRecomp doesn't implement (bdzf, stfsu, lfsu, sthu, lhzu, eqv, vsel128, vpkswss128, subfze, addc, lhzux, lfsux, stfdu, stbux, lwzux, lbzux, frsqrte, lvehx, ...). See recomp/unrecognized_summary.txt. Fix: add cases to XenonRecomp/recompiler.cpp (update-form loads/stores are easy).
  2. 22 switch tables have labels outside XenonRecomp's function bounds (recomp/bad_switch_bases.txt): its function sizing differs from .pdata/gap sizing; fix with [[functions]] overrides in config.toml.

## Session 3 (2026-11-10 evening)
- Patched XenonRecomp with the 28 missing opcodes and added [[functions]] overrides for the 22 inline-table leaf functions. Result: 0 unrecognized, 0 switch errors, and all 56 generated .cpp pass `clang++ -fsyntax-only`. The 211 kernel/XAM imports remained unimplemented.
- PIVOT: ReXGlue SDK (github.com/rexglue/rexglue-sdk, v0.10.0-dev, commit 546a082 2026-11-06). It's XenonRecomp-derived codegen plus a Xenia-derived kernel/GPU/audio runtime, used by the Blue Dragon and Dead Rising 2: Case Zero ports. It removes the need to hand-write imports or a D3D replacement.
  - Requirements: CMake >= 3.25, Ninja, Clang >= 20 (Windows: VS 2022 + "C++ Clang Compiler for Windows" + "MSBuild support for LLVM (clang-cl)").
  - CLI v0.10: `rexglue init --project-name dsignition --xex-path <xex> --game-root <dir>` creates `dsignition_manifest.toml`; `rexglue codegen` then generates into generated/default.
  - ReXGlue's own analysis on default.xex: clean, 10 s, 70 MB, 165 jump tables (a strict superset of our 161). Our custom tables/overrides are NOT needed.
  - Linux build of the SDK in the cloud container uses LLVM 20.1.8 from the GitHub release tarball, plus libgtk-3-dev and SDL X11 deps.
- Project folder for the PC: `port/` (manifest points at ../extracted).
- Asset formats (first look, magic bytes):
  - .zif/.zig: raw zlib (78 DA).
  - PAAssets.dat "INFO", .rel "RELO", .gpu = raw GPU data; marker 0x44332211 = Sumo engine bundle.
  - .tur "TurD"; .crack custom header.
  - .stz (170, SumoTool UI, per language).
  - .bik = Bink 1 "BIKi" (Bink player is linked into the exe: BINK/BINKDATA sections).
  - Audio.xpac is a single audio pack.
  - Resource/Shaders/*.hlsl source + ShaderCache/*.VScache|PScache: the game seems to compile/cache shaders itself.
- LINUX TEST BUILD (cloud container): the SDK built and installed. The dsi project (manifest + generated) compiles and links into a 36 MB `dsignition` ELF.
  - Run: `LD_LIBRARY_PATH=<sdk>/lib:<llvm>/lib/x86_64-unknown-linux-gnu DISPLAY=:99 ./dsignition --game_data_root=<extracted> --gpu_plugin=xenos --log_file=run.log` (Xvfb + Mesa llvmpipe Vulkan). The GPU plugin .so/.dll must sit next to the exe.
  - Run 1: kernel init OK, Vd ring-buffer calls OK, VFS OK, then FATAL: call to unregistered function 0x822641D0. That function is reached only via lis/addi function pointers.
  - Fix: tools/find_code_ptrs.py + a data-section scan found 70 pointer-only function starts, now in the manifest under [entrypoint.functions].
- Staged game data (no movies, EN-only stz) lives at ~/gamedata in the container (not persistent).
- Run 2 (with the GPU plugin): Vulkan up, shader storage, interrupt callback, audio init, file loads; then FATAL at 0x82148ED8, a pointer-only function after a tail-call bctr.
- Second pointer scan (now counting bctr as a boundary; excludes ReXGlue switch case labels and lis/addi values used as indexed-load table bases): 26 more functions. Manifest now has 96 [entrypoint.functions] entries.
- setjmp_address = 0x82354CC0 (MSVC _setjmp: hook ptr check, mflr/mfcr, stfd f14-31/std r13-31 into r3), longjmp_address = 0x823549A0 (r3=buf, r4=val; 0 -> 1). Both are in the manifest.
- Runs 3-5: NO CRASH. The game runs until the timeout: it builds GPU pipelines, connects a controller, and probes Resource\Movies\ and Audio\music\music.xml (missing - check whether that's normal).
- *** FIRST VISIBLE FRAME: the EA logo intro (EaHd.bik) renders. Screenshot: docs/first_frame_ea_logo.png. *** On llvmpipe it needs --vulkan_async_skip_incomplete_frames=false and about 150 s.
- Windows: build_windows.ps1 in the root (clones SDK @546a082, builds, installs, builds port/, copies DLLs, writes play.bat). Run from Developer PowerShell for VS 2022.

## Session 4 (2026-11-12 to 14)
- WINDOWS BUILD WORKS: port/out/build/win-amd64-release/dsignition.exe (23.5 MB, clang 23.1.5 + VS Build Tools 2026 x64 env). The game reaches its title screen on the user's RTX 4070.
- Build fixes:
  - build_windows.ps1 now enters the x64 VS dev shell itself (a 32-bit shell gave lld-link "undefined symbol mainCRTStartup") and fails loudly.
  - Git on Windows checked out libmspack symlinks as text files; 18 were replaced with real copies. MoltenVK links were left as-is (macOS only).
  - device_commit_files wrote STALE cached copies twice. Write files via device_bash (base64) and verify the sha1.
- play.bat flags: --gpu_plugin=xenos --mnk_mode=true (keyboard: Enter=Start, Space=A, Backspace=B, WASD=left stick, arrows=right stick) --license_mask=1 (full game instead of the XBLA trial; the user owns the title).
- DEV SWITCHES ARE DEAD DATA: table at 0x8252D330..0x8252D540 (33 entries of {var name, argc, switch, help}), including racing leftovers -mode/-track/-car/-num_laps/-ai_speed. NO code or data references the table; the retail build compiled out the parser. Re-enabling them would mean patching the game logic each one controlled.
- PS3 leftovers: the exe has PS3/PSN TEXT strings (MSG_PS3_*, "signed out of PLAYSTATION", PS3 save prompts) - a shared codebase with the PS3 version. "Square/Circle/Triangle1" are Software Hack level shapes, not buttons. Button art is unconfirmed.
- .stz (SumoTool UI) format: 0x48-byte header of offsets, then 3 zlib streams. Frontend_EN.stz: 0x48 -> 333 KB CPU data (TEXT chunks, "Button Prompt"), 0x13548 -> 21 KB RELO tables (PTEX = texture pointer relocs, KFRM = keyframes), 0x14C48 -> 60 MB GPU data (Xenos textures). Chunks use the same RELO + 0x44332211 marker as PAAssets.dat/.rel.
- NEXT for button glyphs: write an stz texture exporter (Xenos untile + DXT) -> PNG, find the button sprites, then repack with PS3/keyboard art.
- tools/stz_export.py WORKS: exports .stz textures to PNG (Xenos untile + 8in16 swap + DXT1/3/5 + ARGB8888). Texture index = (record_ptr, gpu_offset) pairs; fetch constant at record+0x2C. Output is in textures/<file>/.
  - Frontend_EN: 15 x 2048x2048 DXT3 atlases (title art, logo, Xbox 360 controller images, UI frames, fonts, minigame item icons).
  - popups_EN_01 (1024x1024) top-right: small round A, B and an O-ring icon (~28 px) in matching style. The ring may be a PS3 Circle leftover; no Cross/Square/Triangle found yet. Main-menu button prompts are not located yet - check the other stz files and the .zif/.zig sets.
- User owns the PS3 version: if installed in RPCS3 (their own license), copy dev_hdd0/game/<ID>/USRDIR to D:\DSIgnitionport\ps3\ for PS3 button art (RSX texture format; the exporter will need a PS3 path).
- stz_export.py: added a single-texture fallback (files without an index run).
- BUTTON PROMPTS FOUND: subtitles_proj_EN.stz (512x256 DXT3 font atlas) holds RB, LB, RT, LT, Y, X, B, A as FONT GLYPHS at the top of the font sheet. Prompts are inline font characters, so swapping those glyph cells changes every prompt with no code change. Other font atlases (Frontend, popups, software_hacking) should be checked for the same glyph cells. Next: map glyph cells via the font tables in the CPU stream (TEXT chunks), then write an stz repacker.
- PS3 files copied to ps3/USRDIR (lowercase names). The PS3 subtitles_proj_en.stz texture uses an RSX header (CellGcmTexture: fmt 0xC7 = DXT3 linear, 512x256) with plain linear little-endian DXT blocks, and holds the full PS3 set R1 L1 L2 R2 Square Triangle Circle Cross in the same style.
- .stz header = 6 (offset, raw, comp) triples (the first 3 unused = 0x48,0,0); streams are zlib, 64-byte aligned from 0x48.
- tools/glyph_swap.py: pastes the donor icons over the Xbox glyph cells (A->Cross, B->Circle, X->Square, Y->Triangle, LB->L1, RB->R1, LT->L2, RT->R2), re-encodes only the changed DXT3 blocks (Pillow), re-tiles and repacks. Verified by re-export.
- PS3 buttons INSTALLED: extracted/Resource/SumoTool/subtitles_proj_EN.stz (sha1 23cf2bc1...). Original backup: mods/original/ (sha1 69bde24e...). PS3 version also in mods/ps3_buttons/.
- Only the subtitle font holds the button set (plus the A/B/ring art in popups_EN_01). Needs an in-game check that menu prompts use this font.
- BUTTON PROMPT MODS (2026-11-14):
  - stz_export.py also reads PS3 .stz: RSX CellGcmTexture records (fmt&0x9f: 0x86 DXT1, 0x87 DXT3, 0x88 DXT5, 0x85 ARGB; 0x40 = linear), each referenced by a (record_offset-0x10, gpu_offset) pair.
  - stz_patch.py: general "edit texture N of an Xbox .stz" library (load_texture / save_patched / paste_icon). It re-encodes only changed DXT blocks, re-tiles, fixes the endian and rebuilds the header.
  - keyboard_glyphs.py draws keycaps in the game's palette (no glow: DXT3 4-bit alpha dithers it).
  - make_button_mods.py builds mods/ps3_buttons and mods/keyboard_buttons (subtitles_proj_EN.stz with all 8 glyphs; popups_EN.stz A/B icons, ring left as is).
  - Mapping follows the actual controls: A=Cross/Space, B=Circle/Backspace, X=Square/L, Y=Triangle/P, LB=L1/1, RB=R1/3, LT=L2/Q, RT=R2/E. Note: the PS3 popups have Square+Circle in the A/B slots; we use Cross for confirm on purpose.
  - buttons.bat xbox|ps3|keyboard copies the set into extracted\Resource\SumoTool (xbox = mods\original backups). The PS3 set is currently INSTALLED.
  - sha1: original subtitles 69bde24e / popups 1c8510f6; ps3 6ae78764 / 2f95cd3d; keyboard 58a6a00d / b8dd439d.
  - English only so far; other languages (_FR/_GE/_IT/_SP) have their own font files.
- File transfer gotcha: device_commit_files may write a stale copy when it reuses an output name. Always use a fresh file name and verify the sha1. Overwrite files on the PC via python open('wb'), since deletes are not permitted.

## Session 5 (2026-11-15/16)
- Root play.bat (calls the real one next to the exe). Launcher.bat -> tools/launcher/launcher.ps1 (WinForms): pick Xbox/PS3/Keyboard prompts, "Skip EA and Visceral logos" checkbox, Play.
- LOGO SKIP: EaHd.bik (13.7 s) = EA logo + Visceral X-ray skull logo. tools/bink_trim.py makes a valid 1-frame Bink (mods/skip_logos/EaHd.bik, sha1 4a2dbb1a; original f9baab59 in mods/original). Linux test: boots straight to the title screen. Blood.bik (40 s) is the game's own intro/blood transition and is used by many scripts - leave it.
- Movie names live in scripts/FrontEndScripts.sbn (Sumo "smospkg2" bytecode), not the exe.
- BUG FIX (user: first screen showed the new glyph, then the menus showed Xbox buttons): the menu prompts come from Frontend_EN.stz:
  - atlas 07 row at y~1301: LB, Start(play-arrow circle), RB, X, B, Y, A
  - atlas 00: big 47px X + LB tab; atlas 01: RB tab
  - PS3 atlas 07 order: L1, R1, Start(bare arrow), Square, Triangle, Cross, [A-ring letter], Circle; PS3 atlas 00 big Square
  - make_button_mods.py now builds Frontend_EN.stz too (pad=1 in the tight row). Keyboard Start = Enter keycap.
  - sha1 Frontend: original 6b0b852d, ps3 5c7d3ef8, keyboard 1a72f594.
- Launcher/buttons.bat now swap 3 files (subtitles, popups, Frontend). Get-CurrentSet requires ALL files to match, otherwise it re-copies on Play. The KEYBOARD set is currently installed.
- GOTCHA: never build mods from ~/gamedata in the container (the test boot installs mods there). Build from the staged originals in /mnt/user-data/uploads/.../extracted.
- Not yet scanned for prompts: minigame sets (.zif/.zig), BgFrames*.stz, PAAssets. Other languages untouched.
- MINIGAME PROMPTS (2026-11-16): Hardware Crack + Software Hack draw prompts from 2x2 ring textures in their asset sets.
  - <Set>.zif = zlib(4-byte size + engine data); <Set>.zig = zlib(4-byte size + GPU data).
  - Texture table = 60-byte records: name ptr at +4, Xenos fetch at +0x24, GPU base = first word of the NEXT record (+0x3c).
  - HardwareCrack: Xbox rings 25 (bright) / 28 (dim); PS3 rings 29 / 30 SHIP IN THE XBOX FILE.
  - SoftwareHack: Xbox 85 / 88; PS3 89 / 91.
  - Quadrants: Xbox X Y / A B; PS3 Triangle Circle / Square Cross. Mapping: X->Square, Y->Triangle, A->Cross, B->Circle.
  - All are 256x256 DXT5 with 9 packed mips. We rewrite level 0 only and set mip_max_level = 0 (fetch dword4 bits 6-9) so the old mips are never sampled.
  - Keyboard rings = the PS3 Circle quadrant with the centre cleared (r<49.5 of 128 = transparent) + label in the ring band colour with the rim colour as outline.
  - tools/minigame_buttons.py builds mods/<set>/HardwareCrack|SoftwareHack/*.zif/.zig; originals are in mods/original/.
  - System Override and Packet Attack have no button textures of their own (they presumably use the font glyphs). PAAssets = .dat (INFO, 8 D3D headers at 0x7e8, stride 52) + .gpu (sequential, no mips).
- Launcher/buttons.bat now swap 7 files per set (3 stz + 4 minigame). The KEYBOARD set is fully installed.
- device_commit_files rejected a 27 MB file (HTTP 400); keep transfers to about 14 MB or less per file.
- RELEASE PREP (2026-11-16): name "DSI Recomp"; recomp credited to Killers' Heaven (user's team; logo in branding/, with dark/transparent variants).
  - CREDITS.md covers EA/Sumo/Visceral/RAD/Microsoft/Sony/ReXGlue/Xenia and third-party licenses. Shipped LGPL: FFmpeg libavcodec+avutil (WMA Pro only), libmspack (both static in rexruntime). The binutils disasm (GPL) is codegen-only, not shipped.
  - Launcher shows the logo, a credit line and an About/credits dialog (reads CREDITS.md).
  - BOOT SPLASH: port/src/splash_dialog.h + DsignitionApp::LaunchModule override. It shows an ImGui overlay (logo + "DSI Recomp - native PC recompilation" + EA copyright line), 3 s, skippable, THEN calls ReXApp::LaunchModule, so EA/Visceral logos are not covered. The logo is read from branding/killers_heaven_on_dark.png in the working dir (build_windows.ps1 copies it next to the exe). The default ImGui font is ASCII-only, so no TM/(C) glyphs. Verified on the Linux build (screenshot: work/splash_preview.png).
  - Plan agreed: BOTH a GitHub source repo (private until release; user creating it, awaiting owner/name + license choice, MIT suggested) AND a prebuilt Windows release needing only the user's 360 files. PS3 menu glyphs: optional "use your PS3 files" step + own-drawn default. license_mask: launcher option, off by default.
