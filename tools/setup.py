"""DSI Recomp setup: turns your own Xbox 360 copy of Dead Space Ignition into a playable install.

Run Setup.exe (or `python tools/setup.py`) from the DSI Recomp folder. Steps:
  1. extract the Xbox 360 package (title ID 58410A7B) into extracted\\
     (or use a folder that already holds the extracted files)
  2. check every game file against docs\\sha1_baseline.txt (only the 2010 XBLA release is supported)
  3. back up the files the launcher swaps into mods\\original\\
  4. build the PlayStation and keyboard button-prompt sets and the logo-skip movie
     (PlayStation symbols are drawn by DSI Recomp; a PS3 copy of the game is optional)

Command line (no window):  setup.py --package <file or folder> [--ps3 <PS3 USRDIR\\resource\\sumotool>] [--root <DSI Recomp folder>]
"""
import sys, os, shutil, hashlib, threading, traceback, argparse

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

XEX_SHA1 = '451fea5e930d767fa3b770b1f80391881032c853'
# files the launcher swaps: path inside extracted\Resource  ->  path inside mods\<set>
MANAGED = {
    'SumoTool/subtitles_proj_EN.stz': 'subtitles_proj_EN.stz',
    'SumoTool/popups_EN.stz': 'popups_EN.stz',
    'SumoTool/Frontend_EN.stz': 'Frontend_EN.stz',
    'HardwareCrack/HardwareCrackSet.zif': 'HardwareCrack/HardwareCrackSet.zif',
    'HardwareCrack/HardwareCrackSet.zig': 'HardwareCrack/HardwareCrackSet.zig',
    'SoftwareHack/SoftwareHackSet.zif': 'SoftwareHack/SoftwareHackSet.zif',
    'SoftwareHack/SoftwareHackSet.zig': 'SoftwareHack/SoftwareHackSet.zig',
    'Movies/EaHd.bik': 'EaHd.bik',
}


def default_root():
    """The DSI Recomp folder: next to Setup.exe, or the repo root when run as tools/setup.py."""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(os.path.abspath(sys.executable))
    return os.path.dirname(HERE)


def sha1(path):
    h = hashlib.sha1()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def load_baseline(root):
    for p in (os.path.join(root, 'docs', 'sha1_baseline.txt'), os.path.join(HERE, 'sha1_baseline.txt')):
        if os.path.exists(p):
            out = {}
            for line in open(p, encoding='utf-8'):
                if line.strip():
                    h, name = line.split(None, 1)
                    out[name.strip().lstrip('./').replace('\\', '/')] = h
            return out
    raise FileNotFoundError('docs\\sha1_baseline.txt is missing from the DSI Recomp folder')


def run(root, package, ps3=None, log=print, progress=lambda f: None):
    root = os.path.abspath(root)
    ext = os.path.join(root, 'extracted')
    mods = os.path.join(root, 'mods')
    orig = os.path.join(mods, 'original')
    baseline = load_baseline(root)
    res = os.path.join(ext, 'Resource')

    # 1. game files ---------------------------------------------------------------------------
    package = os.path.abspath(package)
    if os.path.isdir(package):
        if not os.path.exists(os.path.join(package, 'default.xex')):
            raise RuntimeError('That folder has no default.xex. Pick the Xbox 360 package file, or the folder it was extracted to.')
        if os.path.normcase(package) != os.path.normcase(ext):
            log(f'Copying game files from {package} ...')
            n = 0
            for name in baseline:
                src = os.path.join(package, *name.split('/'))
                dst = os.path.join(ext, *name.split('/'))
                if not os.path.exists(src):
                    raise RuntimeError(f'Missing game file: {name}')
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                shutil.copyfile(src, dst)
                n += 1
                progress(0.30 * n / len(baseline))
    else:
        from stfs_extract import extract
        # files modified by a previous setup / the launcher are re-extracted from the package
        for rel in MANAGED:
            p = os.path.join(res, *rel.split('/'))
            if os.path.exists(p) and sha1(p) != baseline.get('Resource/' + rel):
                os.remove(p)
        log(f'Extracting {os.path.basename(package)} (about 1.7 GB, a few minutes) ...')
        count = [0]
        def elog(msg):
            if msg.startswith('ok '):
                count[0] += 1
                progress(0.30 * count[0] / len(baseline))
            elif msg.startswith('magic='):
                pass
            else:
                log(msg)
        extract(package, ext, log=elog)

    # 2. verify -------------------------------------------------------------------------------
    xex = os.path.join(ext, 'default.xex')
    if not os.path.exists(xex):
        raise RuntimeError('No default.xex was found in the package. Is this Dead Space Ignition (58410A7B)?')
    if sha1(xex) != XEX_SHA1:
        raise RuntimeError('default.xex does not match the supported version (Xbox 360 XBLA release, title update 0). '
                           'Only that version can run with this build.')
    log('Checking all game files ...')
    # a re-run can find launcher-swapped files: put the originals back first
    for rel, m in MANAGED.items():
        p, b = os.path.join(res, *rel.split('/')), os.path.join(orig, *m.split('/'))
        want = baseline.get('Resource/' + rel)
        if os.path.exists(p) and sha1(p) != want and os.path.exists(b) and sha1(b) == want:
            shutil.copyfile(b, p)
    bad = []
    for i, (name, h) in enumerate(sorted(baseline.items())):
        p = os.path.join(ext, *name.split('/'))
        if not os.path.exists(p):
            bad.append(name + ' (missing)')
        elif sha1(p) != h:
            bad.append(name)
        progress(0.30 + 0.30 * (i + 1) / len(baseline))
    if bad:
        raise RuntimeError(f'{len(bad)} game file(s) are missing or differ from the supported version:\n  ' + '\n  '.join(bad[:15]))
    log(f'All {len(baseline)} game files OK.')

    # 3. back up originals -----------------------------------------------------------------------
    for rel, m in MANAGED.items():
        dst = os.path.join(orig, *m.split('/'))
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copyfile(os.path.join(res, *rel.split('/')), dst)
    log('Original files backed up to mods\\original.')
    progress(0.62)

    # 4. button sets and logo skip ----------------------------------------------------------------
    import make_button_mods, minigame_buttons, bink_trim
    if ps3:
        need = ('subtitles_proj_en.stz', 'popups_en.stz', 'frontend_en.stz')
        missing = [f for f in need if not os.path.exists(os.path.join(ps3, f))]
        if missing:
            raise RuntimeError(f'The PS3 folder must be USRDIR\\resource\\sumotool from the PS3 version (missing: {", ".join(missing)}).')
        log('Building button prompts (PlayStation symbols from your PS3 copy) ...')
    else:
        log('Building button prompts ...')
    quiet = lambda *a, **k: None
    for m in (make_button_mods, minigame_buttons):
        m.print = quiet                      # the builders print every glyph; keep the setup log short
    try:
        make_button_mods.main(orig, mods, ps3 or None)
        progress(0.85)
        minigame_buttons.build(orig, mods)
    finally:
        for m in (make_button_mods, minigame_buttons):
            del m.print
    progress(0.95)
    bink_trim.trim(os.path.join(orig, 'EaHd.bik'), os.path.join(mods, 'skip_logos', 'EaHd.bik'), 1)
    # previews are for development only
    for v in ('ps3_buttons', 'keyboard_buttons'):
        shutil.rmtree(os.path.join(mods, v, 'preview'), ignore_errors=True)
        for f in os.listdir(os.path.join(mods, v)):
            if f.endswith('_preview.png'):
                os.remove(os.path.join(mods, v, f))
    progress(1.0)
    log('Button prompt sets and logo skip ready.')
    log('')
    log('Setup complete. Start the game with Launcher.bat.')


# ------------------------------------------------------------------------------------------------
def gui(root):
    import tkinter as tk
    from tkinter import ttk, filedialog, messagebox

    w = tk.Tk()
    w.title('DSI Recomp - Setup')
    w.configure(bg='#1b1d22')
    w.resizable(False, False)
    style = ttk.Style(w)
    try:
        style.theme_use('clam')
    except tk.TclError:
        pass
    fg, bg, acc = '#dfe8ee', '#1b1d22', '#46607a'
    style.configure('TLabel', background=bg, foreground=fg, font=('Segoe UI', 10))
    style.configure('Head.TLabel', font=('Segoe UI Semibold', 13))
    style.configure('Dim.TLabel', foreground='#8b97a3', font=('Segoe UI', 9))
    style.configure('TButton', font=('Segoe UI', 10))
    style.configure('TCheckbutton', background=bg, foreground=fg, font=('Segoe UI', 10))
    style.map('TCheckbutton', background=[('active', bg)])
    style.configure('Horizontal.TProgressbar', troughcolor='#2a2e35', background=acc)

    try:
        logo = tk.PhotoImage(file=os.path.join(root, 'branding', 'launcher_logo.png'))
        tk.Label(w, image=logo, bg=bg).grid(row=0, column=0, columnspan=3, pady=(14, 2))
    except Exception:
        logo = None
    ttk.Label(w, text='DSI Recomp setup', style='Head.TLabel').grid(row=1, column=0, columnspan=3, pady=(2, 10))

    pkg = tk.StringVar()
    ttk.Label(w, text='Your Xbox 360 game package (title ID 58410A7B), or a folder of extracted files:').grid(
        row=2, column=0, columnspan=3, sticky='w', padx=16)
    ttk.Entry(w, textvariable=pkg, width=62).grid(row=3, column=0, columnspan=2, sticky='we', padx=(16, 6), pady=4)

    def pick_pkg():
        p = filedialog.askopenfilename(title='Dead Space Ignition Xbox 360 package', parent=w)
        if p:
            pkg.set(os.path.normpath(p))
    def pick_pkg_dir():
        p = filedialog.askdirectory(title='Folder with the extracted game (contains default.xex)', parent=w)
        if p:
            pkg.set(os.path.normpath(p))
    bf = tk.Frame(w, bg=bg); bf.grid(row=3, column=2, padx=(0, 16))
    ttk.Button(bf, text='File...', command=pick_pkg, width=7).pack(side='left')
    ttk.Button(bf, text='Folder...', command=pick_pkg_dir, width=8).pack(side='left', padx=(4, 0))
    ttk.Label(w, text='On the console it is in Content\\0000000000000000\\58410A7B\\000D0000\\ (a file with a long hex name).',
              style='Dim.TLabel').grid(row=4, column=0, columnspan=3, sticky='w', padx=16)

    use_ps3 = tk.BooleanVar(value=False)
    ps3 = tk.StringVar()
    def toggle():
        st = 'normal' if use_ps3.get() else 'disabled'
        ps3_entry.configure(state=st); ps3_btn.configure(state=st)
    ttk.Checkbutton(w, text='Optional: use the PlayStation symbols from my own PS3 copy', variable=use_ps3,
                    command=toggle).grid(row=5, column=0, columnspan=3, sticky='w', padx=16, pady=(12, 0))
    ps3_entry = ttk.Entry(w, textvariable=ps3, width=62, state='disabled')
    ps3_entry.grid(row=6, column=0, columnspan=2, sticky='we', padx=(16, 6), pady=4)
    def pick_ps3():
        p = filedialog.askdirectory(title='PS3 version: USRDIR\\resource\\sumotool', parent=w)
        if p:
            ps3.set(os.path.normpath(p))
    ps3_btn = ttk.Button(w, text='Folder...', command=pick_ps3, width=8, state='disabled')
    ps3_btn.grid(row=6, column=2, sticky='w', padx=(0, 16))
    ttk.Label(w, text='Not needed: DSI Recomp draws its own PlayStation symbols. Folder = USRDIR\\resource\\sumotool.',
              style='Dim.TLabel').grid(row=7, column=0, columnspan=3, sticky='w', padx=16)

    bar = ttk.Progressbar(w, length=560, mode='determinate', maximum=1.0)
    bar.grid(row=8, column=0, columnspan=3, padx=16, pady=(14, 4), sticky='we')
    txt = tk.Text(w, height=9, width=80, bg='#121418', fg=fg, relief='flat', font=('Consolas', 9), state='disabled')
    txt.grid(row=9, column=0, columnspan=3, padx=16, pady=4, sticky='we')
    go = ttk.Button(w, text='Install')
    go.grid(row=10, column=2, sticky='e', padx=16, pady=(4, 14))

    def log(msg):
        def a():
            txt.configure(state='normal'); txt.insert('end', msg + '\n'); txt.see('end'); txt.configure(state='disabled')
        w.after(0, a)
    def progress(f):
        w.after(0, lambda: bar.configure(value=f))

    def work(p, q):
        try:
            run(root, p, q, log, progress)
            w.after(0, lambda: messagebox.showinfo('DSI Recomp', 'Setup complete.\n\nStart the game with Launcher.bat.', parent=w))
        except Exception as e:
            log('ERROR: ' + str(e))
            with open(os.path.join(root, 'setup_error.log'), 'w', encoding='utf-8') as f:
                traceback.print_exc(file=f)
            w.after(0, lambda: messagebox.showerror('DSI Recomp', str(e), parent=w))
        finally:
            w.after(0, lambda: go.configure(state='normal'))

    def start():
        p = pkg.get().strip().strip('"')
        if not p or not os.path.exists(p):
            messagebox.showwarning('DSI Recomp', 'Pick your Xbox 360 game package first.', parent=w); return
        q = ps3.get().strip().strip('"') if use_ps3.get() else None
        go.configure(state='disabled'); bar.configure(value=0)
        threading.Thread(target=work, args=(p, q), daemon=True).start()
    go.configure(command=start)
    w.mainloop()


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--package', help='Xbox 360 package file, or a folder with the extracted game')
    ap.add_argument('--ps3', help='optional: PS3 version USRDIR\\resource\\sumotool folder')
    ap.add_argument('--root', default=default_root(), help='DSI Recomp folder (default: this one)')
    a = ap.parse_args()
    if a.package:
        last = [-1]
        def prog(f):
            if int(f * 20) != last[0]:
                last[0] = int(f * 20); print(f'  {int(f * 100)}%', flush=True)
        try:
            run(a.root, a.package, a.ps3, lambda m: print(m, flush=True), prog)
        except Exception as e:
            sys.exit(f'ERROR: {e}')
    else:
        gui(a.root)


if __name__ == '__main__':
    main()
