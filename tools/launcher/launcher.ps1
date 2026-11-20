# Dead Space Ignition launcher: choose button prompts, then play.
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing
[System.Windows.Forms.Application]::EnableVisualStyles()

$root   = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
# release zip: bin\dsignition.exe; source build: port\out\build\win-amd64-release\dsignition.exe
$exeDir = Join-Path $root "bin"
if (-not (Test-Path (Join-Path $exeDir "dsignition.exe"))) { $exeDir = Join-Path $root "port\out\build\win-amd64-release" }
$exe    = Join-Path $exeDir "dsignition.exe"
$dst    = Join-Path $root "extracted\Resource"

# Game text languages: file suffix -> console language ID passed as --user_language
$langs = [ordered]@{ EN = 1; FR = 4; GE = 3; IT = 6; SP = 5 }
$langNames = [ordered]@{ EN = "English"; FR = "Français"; GE = "Deutsch"; IT = "Italiano"; SP = "Español" }
# all launcher texts by language. (Not "$T": PowerShell names ignore case, so $t below would overwrite it.)
$Strings = @{
  EN = @{ lang = "Language"; group = "Button prompts"; kb = "Keyboard"; missing = "(missing)"; skip = "Skip EA and Visceral logos"
          filesmissing = "(files missing)"; full = "I own the full game (unlock trial)"; play = "Play"; installed = "Installed:"
          custom = "custom"; about = "About / credits"; aboutTitle = "About DSI Recomp"; by = "recompiled by"
          errStart = "Could not start"; errRunning = "If the game is already running, close it first."
          errExe = "dsignition.exe not found. Run build_windows.ps1 first."; errSetup = "Game files not found. Run Setup first."
          options = "Options..."; optTitle = "DSI Recomp options"; gfx = "Graphics"; display = "Display"; fullscreen = "Fullscreen"; windowed = "Window"
          res = "Rendering resolution"; filter = "Upscaling filter"; fBil = "Bilinear (smooth)"; fFsr = "AMD FSR"; fCas = "AMD CAS (sharpen)"
          vsync = "VSync (no screen tearing)"; ctrl = "Controller"; vib = "Vibration"; dzL = "Left stick dead zone (%)"; dzR = "Right stick dead zone (%)"
          ok = "OK"; cancel = "Cancel"; defaults = "Defaults"; hint = "Achievements: open them from the game's menus; they are saved automatically."; resWarn = "Higher resolutions need a powerful GPU and can cause stutter or instability." }
  FR = @{ lang = "Langue"; group = "Icônes des boutons"; kb = "Clavier"; missing = "(manquant)"; skip = "Passer les logos EA et Visceral"
          filesmissing = "(fichiers manquants)"; full = "Je possède le jeu complet (débloquer la démo)"; play = "Jouer"; installed = "Installé :"
          custom = "personnalisé"; about = "À propos / crédits"; aboutTitle = "À propos de DSI Recomp"; by = "recompilé par"
          errStart = "Impossible de lancer le jeu"; errRunning = "Si le jeu est déjà lancé, fermez-le d'abord."
          errExe = "dsignition.exe introuvable. Lancez d'abord build_windows.ps1."; errSetup = "Fichiers du jeu introuvables. Lancez d'abord Setup."
          options = "Options..."; optTitle = "Options de DSI Recomp"; gfx = "Graphismes"; display = "Affichage"; fullscreen = "Plein écran"; windowed = "Fenêtre"
          res = "Résolution de rendu"; filter = "Filtre de mise à l'échelle"; fBil = "Bilinéaire (doux)"; fFsr = "AMD FSR"; fCas = "AMD CAS (netteté)"
          vsync = "VSync (pas de déchirement)"; ctrl = "Manette"; vib = "Vibrations"; dzL = "Zone morte stick gauche (%)"; dzR = "Zone morte stick droit (%)"
          ok = "OK"; cancel = "Annuler"; defaults = "Par défaut"; hint = "Succès : ouvrez-les depuis les menus du jeu ; ils sont enregistrés automatiquement."; resWarn = "Les résolutions élevées demandent un GPU puissant et peuvent causer des saccades ou de l'instabilité." }
  GE = @{ lang = "Sprache"; group = "Tastensymbole"; kb = "Tastatur"; missing = "(fehlt)"; skip = "EA- und Visceral-Logos überspringen"
          filesmissing = "(Dateien fehlen)"; full = "Ich besitze das Vollspiel (Testversion freischalten)"; play = "Spielen"; installed = "Installiert:"
          custom = "benutzerdefiniert"; about = "Info / Credits"; aboutTitle = "Über DSI Recomp"; by = "rekompiliert von"
          errStart = "Start fehlgeschlagen"; errRunning = "Falls das Spiel bereits läuft, beende es zuerst."
          errExe = "dsignition.exe nicht gefunden. Führe zuerst build_windows.ps1 aus."; errSetup = "Spieldateien nicht gefunden. Führe zuerst Setup aus."
          options = "Optionen..."; optTitle = "DSI Recomp – Optionen"; gfx = "Grafik"; display = "Anzeige"; fullscreen = "Vollbild"; windowed = "Fenster"
          res = "Renderauflösung"; filter = "Skalierungsfilter"; fBil = "Bilinear (weich)"; fFsr = "AMD FSR"; fCas = "AMD CAS (Schärfen)"
          vsync = "VSync (kein Tearing)"; ctrl = "Controller"; vib = "Vibration"; dzL = "Totzone linker Stick (%)"; dzR = "Totzone rechter Stick (%)"
          ok = "OK"; cancel = "Abbrechen"; defaults = "Standard"; hint = "Erfolge: über die Menüs des Spiels öffnen; sie werden automatisch gespeichert."; resWarn = "Höhere Auflösungen brauchen eine starke GPU und können Ruckler oder Instabilität verursachen." }
  IT = @{ lang = "Lingua"; group = "Icone dei pulsanti"; kb = "Tastiera"; missing = "(mancante)"; skip = "Salta i loghi EA e Visceral"
          filesmissing = "(file mancanti)"; full = "Possiedo il gioco completo (sblocca la prova)"; play = "Gioca"; installed = "Installato:"
          custom = "personalizzato"; about = "Informazioni / crediti"; aboutTitle = "Informazioni su DSI Recomp"; by = "ricompilato da"
          errStart = "Impossibile avviare il gioco"; errRunning = "Se il gioco è già in esecuzione, chiudilo prima."
          errExe = "dsignition.exe non trovato. Esegui prima build_windows.ps1."; errSetup = "File di gioco non trovati. Esegui prima Setup."
          options = "Opzioni..."; optTitle = "Opzioni di DSI Recomp"; gfx = "Grafica"; display = "Schermo"; fullscreen = "Schermo intero"; windowed = "Finestra"
          res = "Risoluzione di rendering"; filter = "Filtro di scalatura"; fBil = "Bilineare (morbido)"; fFsr = "AMD FSR"; fCas = "AMD CAS (nitidezza)"
          vsync = "VSync (niente tearing)"; ctrl = "Controller"; vib = "Vibrazione"; dzL = "Zona morta levetta sinistra (%)"; dzR = "Zona morta levetta destra (%)"
          ok = "OK"; cancel = "Annulla"; defaults = "Predefiniti"; hint = "Obiettivi: aprili dai menu del gioco; vengono salvati automaticamente."; resWarn = "Le risoluzioni più alte richiedono una GPU potente e possono causare scatti o instabilità." }
  SP = @{ lang = "Idioma"; group = "Iconos de los botones"; kb = "Teclado"; missing = "(falta)"; skip = "Omitir los logotipos de EA y Visceral"
          filesmissing = "(faltan archivos)"; full = "Tengo el juego completo (desbloquear la prueba)"; play = "Jugar"; installed = "Instalado:"
          custom = "personalizado"; about = "Acerca de / créditos"; aboutTitle = "Acerca de DSI Recomp"; by = "recompilado por"
          errStart = "No se pudo iniciar el juego"; errRunning = "Si el juego ya se está ejecutando, ciérralo primero."
          errExe = "No se encontró dsignition.exe. Ejecuta primero build_windows.ps1."; errSetup = "No se encontraron los archivos del juego. Ejecuta primero Setup."
          options = "Opciones..."; optTitle = "Opciones de DSI Recomp"; gfx = "Gráficos"; display = "Pantalla"; fullscreen = "Pantalla completa"; windowed = "Ventana"
          res = "Resolución de renderizado"; filter = "Filtro de escalado"; fBil = "Bilineal (suave)"; fFsr = "AMD FSR"; fCas = "AMD CAS (nitidez)"
          vsync = "VSync (sin tearing)"; ctrl = "Mando"; vib = "Vibración"; dzL = "Zona muerta stick izquierdo (%)"; dzR = "Zona muerta stick derecho (%)"
          ok = "Aceptar"; cancel = "Cancelar"; defaults = "Predeterminados"; hint = "Logros: ábrelos desde los menús del juego; se guardan automáticamente."; resWarn = "Las resoluciones altas requieren una GPU potente y pueden causar tirones o inestabilidad." }
}
# each button set = these files: path inside mods\<set>\  ->  path inside extracted\Resource\
# (the menu/subtitle/pop-up files exist once per language; older installs may only have English)
$items = @()
foreach ($l in $langs.Keys) {
    if (-not (Test-Path (Join-Path $root "mods\original\Frontend_$l.stz")) -and $l -ne "EN") { continue }
    foreach ($f in "subtitles_proj", "popups", "Frontend") { $items += @{ src = "$($f)_$l.stz"; dst = "SumoTool\$($f)_$l.stz" } }
}
$items += @(
    @{ src = "HardwareCrack\HardwareCrackSet.zif"; dst = "HardwareCrack\HardwareCrackSet.zif" },
    @{ src = "HardwareCrack\HardwareCrackSet.zig"; dst = "HardwareCrack\HardwareCrackSet.zig" },
    @{ src = "SoftwareHack\SoftwareHackSet.zif";   dst = "SoftwareHack\SoftwareHackSet.zif" },
    @{ src = "SoftwareHack\SoftwareHackSet.zig";   dst = "SoftwareHack\SoftwareHackSet.zig" }
)
$settingsPath = Join-Path $root "launcher_settings.json"
$settings = @{ full_game = $false; language = $null
              fullscreen = $true; res_scale = 1; filter = "bilinear"; vsync = $true
              vibration = $true; dz_left = 0; dz_right = 0 }
if (Test-Path $settingsPath) {
    try {
        $j = Get-Content $settingsPath -Raw | ConvertFrom-Json
        if ($j.full_game) { $settings.full_game = $true }
        if ($j.language -and $langs.Contains([string]$j.language)) { $settings.language = [string]$j.language }
        foreach ($k in "fullscreen", "vsync", "vibration") { if ($null -ne $j.$k) { $settings[$k] = [bool]$j.$k } }
        foreach ($k in "res_scale", "dz_left", "dz_right") { if ($null -ne $j.$k) { $settings[$k] = [int]$j.$k } }
        $settings.res_scale = [math]::Min([math]::Max($settings.res_scale, 1), 3)
        if ($j.filter -in "bilinear", "fsr", "cas") { $settings.filter = [string]$j.filter }
    } catch { }
}
if (-not $settings.language) {
    # first start: follow the Windows display language when the game has it
    $ui = (Get-UICulture).TwoLetterISOLanguageName
    $settings.language = switch ($ui) { "fr" { "FR" } "de" { "GE" } "it" { "IT" } "es" { "SP" } default { "EN" } }
}
$movie  = Join-Path $root "extracted\Resource\Movies\EaHd.bik"
$movieOrig = Join-Path $root "mods\original\EaHd.bik"
$movieSkip = Join-Path $root "mods\skip_logos\EaHd.bik"
# internal set names (labels come from $Strings); Get-CurrentSet returns one of these keys
$sets   = [ordered]@{ xbox = "mods\original"; ps3 = "mods\ps3_buttons"; keyboard = "mods\keyboard_buttons" }
function SetLabel($key, $L) { switch ($key) { "xbox" { "Xbox 360" } "ps3" { "PlayStation 3" } default { $Strings[$L].kb } } }

function Get-CurrentSet {
    # A set counts as installed only if ALL of its files match; anything else = $null (gets re-copied on Play)
    $cur = @{}; foreach ($it in $items) { $f = Join-Path $dst $it.dst; $cur[$it.dst] = if (Test-Path $f) { (Get-FileHash $f -Algorithm SHA1).Hash } else { "" } }
    foreach ($name in $sets.Keys) {
        $ok = $true
        foreach ($it in $items) {
            $p = Join-Path (Join-Path $root $sets[$name]) $it.src
            if (-not (Test-Path $p) -or (Get-FileHash $p -Algorithm SHA1).Hash -ne $cur[$it.dst]) { $ok = $false; break }
        }
        if ($ok) { return $name }
    }
    return $null
}

function Get-LogosSkipped {
    if (-not (Test-Path $movieSkip)) { return $false }
    if (-not (Test-Path $movie)) { return $false }
    return (Get-FileHash $movie -Algorithm SHA1).Hash -eq (Get-FileHash $movieSkip -Algorithm SHA1).Hash
}

function Set-Buttons($name) {
    $src = Join-Path $root $sets[$name]
    foreach ($it in $items) { Copy-Item (Join-Path $src $it.src) (Join-Path $dst $it.dst) -Force -ErrorAction Stop }
}

$form = New-Object System.Windows.Forms.Form
$form.Text = "Dead Space Ignition"
# the game's own tile from the player's package (saved by Setup), else the DSI Recomp icon
$iconPath = Join-Path $root "branding\game_icon.ico"
if (-not (Test-Path $iconPath)) { $iconPath = Join-Path $root "branding\dsi.ico" }
if (Test-Path $iconPath) { try { $form.Icon = New-Object System.Drawing.Icon($iconPath) } catch { } }
$form.FormBorderStyle = "FixedDialog"; $form.MaximizeBox = $false
$form.StartPosition = "CenterScreen"
$form.ClientSize = New-Object System.Drawing.Size(320, 384)
$form.BackColor = [System.Drawing.Color]::FromArgb(24, 28, 34)
$form.ForeColor = [System.Drawing.Color]::FromArgb(214, 234, 242)
$form.Font = New-Object System.Drawing.Font("Segoe UI", 10)

$logoPath = Join-Path $root "branding\launcher_logo.png"
if (Test-Path $logoPath) {
    $logo = New-Object System.Windows.Forms.PictureBox
    $logo.Image = [System.Drawing.Image]::FromFile($logoPath)
    $logo.SizeMode = "Zoom"; $logo.Size = New-Object System.Drawing.Size(288, 59)
    $logo.Location = New-Object System.Drawing.Point(16, 10)
    $form.Controls.Add($logo)
}
$title = New-Object System.Windows.Forms.Label
$title.AutoSize = $true
$title.Font = New-Object System.Drawing.Font("Segoe UI", 8.5)
$title.ForeColor = [System.Drawing.Color]::FromArgb(150, 170, 185)
$title.Location = New-Object System.Drawing.Point(16, 74)
$form.Controls.Add($title)

$langLabel = New-Object System.Windows.Forms.Label
$langLabel.AutoSize = $true; $langLabel.Location = New-Object System.Drawing.Point(16, 107)
$form.Controls.Add($langLabel)
$langBox = New-Object System.Windows.Forms.ComboBox
$langBox.DropDownStyle = "DropDownList"; $langBox.Location = New-Object System.Drawing.Point(144, 103)
$langBox.Size = New-Object System.Drawing.Size(160, 26)
$langBox.FlatStyle = "Flat"; $langBox.BackColor = [System.Drawing.Color]::FromArgb(36, 42, 50); $langBox.ForeColor = $form.ForeColor
foreach ($l in $langs.Keys) { [void]$langBox.Items.Add($langNames[$l]) }
$langBox.SelectedIndex = [array]::IndexOf(@($langs.Keys), $settings.language)
$form.Controls.Add($langBox)

$group = New-Object System.Windows.Forms.GroupBox
$group.ForeColor = $form.ForeColor
$group.Location = New-Object System.Drawing.Point(16, 140); $group.Size = New-Object System.Drawing.Size(288, 104)
$form.Controls.Add($group)

$current = Get-CurrentSet
$radios = @{}; $y = 22
foreach ($name in $sets.Keys) {
    $r = New-Object System.Windows.Forms.RadioButton
    $r.AutoSize = $true; $r.Location = New-Object System.Drawing.Point(14, $y)
    if (@($items | Where-Object { -not (Test-Path (Join-Path (Join-Path $root $sets[$name]) $_.src)) }).Count) { $r.Enabled = $false }
    if ($name -eq $current) { $r.Checked = $true }
    $group.Controls.Add($r); $radios[$name] = $r; $y += 26
}
if (-not $current) { $radios["xbox"].Checked = $true }

$skip = New-Object System.Windows.Forms.CheckBox
$skip.AutoSize = $true
$skip.Location = New-Object System.Drawing.Point(18, 252)
$skip.Checked = Get-LogosSkipped
if (-not ((Test-Path $movieSkip) -and (Test-Path $movieOrig))) { $skip.Enabled = $false }
$form.Controls.Add($skip)

$full = New-Object System.Windows.Forms.CheckBox
$full.AutoSize = $true
$full.Location = New-Object System.Drawing.Point(18, 276)
$full.Checked = [bool]$settings.full_game
$form.Controls.Add($full)

$play = New-Object System.Windows.Forms.Button
$play.Size = New-Object System.Drawing.Size(140, 36)
$play.Location = New-Object System.Drawing.Point(164, 312)
$play.FlatStyle = "Flat"; $play.BackColor = [System.Drawing.Color]::FromArgb(70, 96, 122)
$play.Font = New-Object System.Drawing.Font("Segoe UI Semibold", 11)
$form.AcceptButton = $play
$form.Controls.Add($play)

$opts = New-Object System.Windows.Forms.Button
$opts.Size = New-Object System.Drawing.Size(140, 36)
$opts.Location = New-Object System.Drawing.Point(16, 312)
$opts.FlatStyle = "Flat"; $opts.BackColor = [System.Drawing.Color]::FromArgb(40, 50, 62)
$opts.Font = New-Object System.Drawing.Font("Segoe UI", 10)
$form.Controls.Add($opts)

$status = New-Object System.Windows.Forms.Label
$status.AutoSize = $true; $status.Location = New-Object System.Drawing.Point(16, 360)
$status.ForeColor = [System.Drawing.Color]::FromArgb(150, 170, 185)
$form.Controls.Add($status)

$about = New-Object System.Windows.Forms.LinkLabel
$about.AutoSize = $true; $about.TextAlign = "TopRight"; $about.AutoSize = $false
$about.Size = New-Object System.Drawing.Size(150, 18); $about.Location = New-Object System.Drawing.Point(154, 360)
$about.LinkColor = [System.Drawing.Color]::FromArgb(120, 190, 230)
$about.Add_LinkClicked({
    $c = Join-Path $root "CREDITS.md"
    $text = if (Test-Path $c) { Get-Content $c -Raw } else { "DSI Recomp - recompiled by Killers' Heaven" }
    $f2 = New-Object System.Windows.Forms.Form
    $f2.Text = $Strings[(CurLang)].aboutTitle; $f2.StartPosition = "CenterParent"; $f2.Size = New-Object System.Drawing.Size(640, 560)
    $tb = New-Object System.Windows.Forms.TextBox
    $tb.Multiline = $true; $tb.ReadOnly = $true; $tb.ScrollBars = "Vertical"; $tb.Dock = "Fill"
    $tb.Font = New-Object System.Drawing.Font("Consolas", 9); $tb.Text = $text -replace "`r?`n", "`r`n"
    $f2.Controls.Add($tb); [void]$f2.ShowDialog($form)
})
$form.Controls.Add($about)

# Game settings live in dsignition.toml next to the exe, which the game reads at start, so play.bat
# and starting the exe directly use them too. Lines for other settings are kept as they are.
function Write-GameConfig($prompts) {
    $cfg = Join-Path $exeDir "dsignition.toml"
    $f = { param($v) $v.ToString([System.Globalization.CultureInfo]::InvariantCulture) }
    $values = [ordered]@{
        fullscreen = $settings.fullscreen.ToString().ToLower()
        resolution_scale = [string]$settings.res_scale
        present_effect = "`"$($settings.filter)`""
        vsync = $settings.vsync.ToString().ToLower()
        vibration = $settings.vibration.ToString().ToLower()
        left_stick_deadzone_percentage = (& $f ([double]$settings.dz_left / 100))
        right_stick_deadzone_percentage = (& $f ([double]$settings.dz_right / 100))
        user_language = [string]$langs[(CurLang)]
        license_mask = $(if ($full.Checked) { "1" } else { "0" })
        dsi_prompts = "`"$prompts`""
    }
    $keep = @()
    if (Test-Path $cfg) {
        foreach ($line in Get-Content $cfg) {
            $k = ($line -split "=", 2)[0].Trim()
            if ($line.StartsWith("# Written by") -or $values.Contains($k)) { continue }
            $keep += $line
        }
    }
    $out = @("# Written by the DSI Recomp launcher (Options). Edit the launcher instead; other lines are kept.")
    foreach ($k in $values.Keys) { $out += "$k = $($values[$k])" }
    ($out + $keep) | Set-Content $cfg -Encoding ASCII
}

function Show-Options {
    $t = $Strings[(CurLang)]
    $d = New-Object System.Windows.Forms.Form
    $d.Text = $t.optTitle; $d.StartPosition = "CenterParent"; $d.FormBorderStyle = "FixedDialog"
    $d.MaximizeBox = $false; $d.MinimizeBox = $false; $d.ShowInTaskbar = $false
    $d.ClientSize = New-Object System.Drawing.Size(360, 440)
    $d.BackColor = $form.BackColor; $d.ForeColor = $form.ForeColor; $d.Font = $form.Font
    function Lbl($text, $x, $y, $bold) {
        $l = New-Object System.Windows.Forms.Label; $l.Text = $text; $l.AutoSize = $true
        $l.Location = New-Object System.Drawing.Point($x, $y)
        if ($bold) { $l.Font = New-Object System.Drawing.Font("Segoe UI Semibold", 10); $l.ForeColor = [System.Drawing.Color]::FromArgb(150, 200, 235) }
        $d.Controls.Add($l); $l
    }
    function Combo($items, $x, $y, $w) {
        $c = New-Object System.Windows.Forms.ComboBox; $c.DropDownStyle = "DropDownList"; $c.FlatStyle = "Flat"
        $c.BackColor = [System.Drawing.Color]::FromArgb(36, 42, 50); $c.ForeColor = $form.ForeColor
        $c.Location = New-Object System.Drawing.Point($x, $y); $c.Size = New-Object System.Drawing.Size($w, 26)
        foreach ($i in $items) { [void]$c.Items.Add($i) }
        $d.Controls.Add($c); $c
    }
    function Check($text, $x, $y, $on) {
        $c = New-Object System.Windows.Forms.CheckBox; $c.Text = $text; $c.AutoSize = $true; $c.Checked = $on
        $c.Location = New-Object System.Drawing.Point($x, $y); $d.Controls.Add($c); $c
    }
    function Num($x, $y, $v) {
        $n = New-Object System.Windows.Forms.NumericUpDown; $n.Minimum = 0; $n.Maximum = 50; $n.Value = $v
        $n.BackColor = [System.Drawing.Color]::FromArgb(36, 42, 50); $n.ForeColor = $form.ForeColor
        $n.Location = New-Object System.Drawing.Point($x, $y); $n.Size = New-Object System.Drawing.Size(64, 26)
        $d.Controls.Add($n); $n
    }
    [void](Lbl $t.gfx 16 14 $true)
    [void](Lbl $t.display 16 46 $false)
    $mode = Combo @($t.fullscreen, $t.windowed) 190 42 150
    $mode.SelectedIndex = $(if ($settings.fullscreen) { 0 } else { 1 })
    [void](Lbl $t.res 16 80 $false)
    $res = Combo @("1x (720p)", "2x (1440p)", "3x (2160p / 4K)") 190 76 150
    $res.SelectedIndex = [math]::Min([math]::Max($settings.res_scale, 1), 3) - 1
    $warn = Lbl $t.resWarn 16 106 $false
    $warn.AutoSize = $false; $warn.Size = New-Object System.Drawing.Size(328, 34)
    $warn.ForeColor = [System.Drawing.Color]::FromArgb(236, 176, 80)
    $warn.Visible = ($res.SelectedIndex -gt 0)
    $res.Add_SelectedIndexChanged({ $warn.Visible = ($res.SelectedIndex -gt 0) })
    [void](Lbl $t.filter 16 150 $false)
    $flt = Combo @($t.fBil, $t.fFsr, $t.fCas) 190 146 150
    $flt.SelectedIndex = [array]::IndexOf(@("bilinear", "fsr", "cas"), $settings.filter)
    $vs = Check $t.vsync 18 182 $settings.vsync

    [void](Lbl $t.ctrl 16 222 $true)
    $vib = Check $t.vib 18 252 $settings.vibration
    [void](Lbl $t.dzL 16 284 $false); $dzl = Num 276 280 $settings.dz_left
    [void](Lbl $t.dzR 16 316 $false); $dzr = Num 276 312 $settings.dz_right

    $hint = Lbl $t.hint 16 350 $false
    $hint.AutoSize = $false; $hint.Size = New-Object System.Drawing.Size(328, 34)
    $hint.ForeColor = [System.Drawing.Color]::FromArgb(150, 170, 185)

    $def = New-Object System.Windows.Forms.Button; $def.Text = $t.defaults; $def.FlatStyle = "Flat"
    $def.Location = New-Object System.Drawing.Point(16, 396); $def.Size = New-Object System.Drawing.Size(110, 30)
    $def.Add_Click({ $mode.SelectedIndex = 0; $res.SelectedIndex = 0; $flt.SelectedIndex = 0; $vs.Checked = $true
                     $vib.Checked = $true; $dzl.Value = 0; $dzr.Value = 0 })
    $ok = New-Object System.Windows.Forms.Button; $ok.Text = $t.ok; $ok.FlatStyle = "Flat"; $ok.DialogResult = "OK"
    $ok.BackColor = [System.Drawing.Color]::FromArgb(70, 96, 122)
    $ok.Location = New-Object System.Drawing.Point(160, 396); $ok.Size = New-Object System.Drawing.Size(86, 30)
    $cn = New-Object System.Windows.Forms.Button; $cn.Text = $t.cancel; $cn.FlatStyle = "Flat"; $cn.DialogResult = "Cancel"
    $cn.Location = New-Object System.Drawing.Point(256, 396); $cn.Size = New-Object System.Drawing.Size(88, 30)
    $d.Controls.AddRange(@($def, $ok, $cn)); $d.AcceptButton = $ok; $d.CancelButton = $cn

    if ($d.ShowDialog($form) -eq "OK") {
        $settings.fullscreen = ($mode.SelectedIndex -eq 0)
        $settings.res_scale = $res.SelectedIndex + 1
        $settings.filter = @("bilinear", "fsr", "cas")[[math]::Max($flt.SelectedIndex, 0)]
        $settings.vsync = $vs.Checked
        $settings.vibration = $vib.Checked
        $settings.dz_left = [int]$dzl.Value
        $settings.dz_right = [int]$dzr.Value
        Save-Settings
    }
}

function Save-Settings {
    try {
        [ordered]@{ full_game = $full.Checked; language = (CurLang); user_language = $langs[(CurLang)]
                    fullscreen = $settings.fullscreen; res_scale = $settings.res_scale; filter = $settings.filter
                    vsync = $settings.vsync; vibration = $settings.vibration
                    dz_left = $settings.dz_left; dz_right = $settings.dz_right } |
            ConvertTo-Json | Set-Content $settingsPath -Encoding ASCII
    } catch { }
}

function CurLang { @($langs.Keys)[[math]::Max($langBox.SelectedIndex, 0)] }
function Apply-Texts {
    $L = CurLang; $t = $Strings[$L]
    $title.Text = "DSI RECOMP  -  $($t.by) Killers' Heaven"
    $langLabel.Text = $t.lang
    $group.Text = $t.group
    foreach ($k in $sets.Keys) { $radios[$k].Text = (SetLabel $k $L) + $(if ($radios[$k].Enabled) { "" } else { " $($t.missing)" }) }
    $skip.Text = $t.skip + $(if ($skip.Enabled) { "" } else { " $($t.filesmissing)" })
    $full.Text = $t.full
    $play.Text = $t.play
    $about.Text = $t.about
    $opts.Text = $t.options
    $status.Text = "$($t.installed) " + $(if ($current) { SetLabel $current $L } else { $t.custom })
}
Apply-Texts
$langBox.Add_SelectedIndexChanged({ Apply-Texts })
$opts.Add_Click({ Show-Options })

$play.Add_Click({
    try {
        $choice = ($radios.Keys | Where-Object { $radios[$_].Checked } | Select-Object -First 1)
        if ($choice -and $choice -ne (Get-CurrentSet)) { Set-Buttons $choice }
        if ($skip.Enabled -and ($skip.Checked -ne (Get-LogosSkipped))) {
            $src = if ($skip.Checked) { $movieSkip } else { $movieOrig }
            Copy-Item $src $movie -Force -ErrorAction Stop
        }
        $t = $Strings[(CurLang)]
        if (-not (Test-Path $exe)) { throw $t.errExe }
        if (-not (Test-Path "$root\extracted\default.xex")) { throw $t.errSetup }
        New-Item -ItemType Directory -Force "$root\docs" | Out-Null
        $gameArgs = @("--game_data_root=`"$root\extracted`"", "--gpu_plugin=xenos", "--mnk_mode=true",
                  "--log_file=`"$root\docs\run_windows.log`"")
        if ($full.Checked) { $gameArgs += "--license_mask=1" }
        $gameArgs += "--user_language=$($langs[(CurLang)])"
        # play.bat reads full_game and user_language from launcher_settings.json; the game reads dsignition.toml
        Save-Settings
        try { Write-GameConfig $(if ($choice) { $choice } else { "xbox" }) } catch { }
        Start-Process -FilePath $exe -ArgumentList $gameArgs -WorkingDirectory $exeDir
        $form.Close()
    } catch {
        $t = $Strings[(CurLang)]
        [System.Windows.Forms.MessageBox]::Show("$($t.errStart): $($_.Exception.Message)`n`n$($t.errRunning)", "Dead Space Ignition") | Out-Null
    }
})

[void]$form.ShowDialog()
