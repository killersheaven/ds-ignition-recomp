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
$T = @{
  EN = @{ lang = "Language"; group = "Button prompts"; kb = "Keyboard"; missing = "(missing)"; skip = "Skip EA and Visceral logos"
          filesmissing = "(files missing)"; full = "I own the full game (unlock trial)"; play = "Play"; installed = "Installed:"
          custom = "custom"; about = "About / credits"; aboutTitle = "About DSI Recomp"; by = "recompiled by"
          errStart = "Could not start"; errRunning = "If the game is already running, close it first."
          errExe = "dsignition.exe not found. Run build_windows.ps1 first."; errSetup = "Game files not found. Run Setup first." }
  FR = @{ lang = "Langue"; group = "Icônes des boutons"; kb = "Clavier"; missing = "(manquant)"; skip = "Passer les logos EA et Visceral"
          filesmissing = "(fichiers manquants)"; full = "Je possède le jeu complet (débloquer la démo)"; play = "Jouer"; installed = "Installé :"
          custom = "personnalisé"; about = "À propos / crédits"; aboutTitle = "À propos de DSI Recomp"; by = "recompilé par"
          errStart = "Impossible de lancer le jeu"; errRunning = "Si le jeu est déjà lancé, fermez-le d'abord."
          errExe = "dsignition.exe introuvable. Lancez d'abord build_windows.ps1."; errSetup = "Fichiers du jeu introuvables. Lancez d'abord Setup." }
  GE = @{ lang = "Sprache"; group = "Tastensymbole"; kb = "Tastatur"; missing = "(fehlt)"; skip = "EA- und Visceral-Logos überspringen"
          filesmissing = "(Dateien fehlen)"; full = "Ich besitze das Vollspiel (Testversion freischalten)"; play = "Spielen"; installed = "Installiert:"
          custom = "benutzerdefiniert"; about = "Info / Credits"; aboutTitle = "Über DSI Recomp"; by = "rekompiliert von"
          errStart = "Start fehlgeschlagen"; errRunning = "Falls das Spiel bereits läuft, beende es zuerst."
          errExe = "dsignition.exe nicht gefunden. Führe zuerst build_windows.ps1 aus."; errSetup = "Spieldateien nicht gefunden. Führe zuerst Setup aus." }
  IT = @{ lang = "Lingua"; group = "Icone dei pulsanti"; kb = "Tastiera"; missing = "(mancante)"; skip = "Salta i loghi EA e Visceral"
          filesmissing = "(file mancanti)"; full = "Possiedo il gioco completo (sblocca la prova)"; play = "Gioca"; installed = "Installato:"
          custom = "personalizzato"; about = "Informazioni / crediti"; aboutTitle = "Informazioni su DSI Recomp"; by = "ricompilato da"
          errStart = "Impossibile avviare il gioco"; errRunning = "Se il gioco è già in esecuzione, chiudilo prima."
          errExe = "dsignition.exe non trovato. Esegui prima build_windows.ps1."; errSetup = "File di gioco non trovati. Esegui prima Setup." }
  SP = @{ lang = "Idioma"; group = "Iconos de los botones"; kb = "Teclado"; missing = "(falta)"; skip = "Omitir los logotipos de EA y Visceral"
          filesmissing = "(faltan archivos)"; full = "Tengo el juego completo (desbloquear la prueba)"; play = "Jugar"; installed = "Instalado:"
          custom = "personalizado"; about = "Acerca de / créditos"; aboutTitle = "Acerca de DSI Recomp"; by = "recompilado por"
          errStart = "No se pudo iniciar el juego"; errRunning = "Si el juego ya se está ejecutando, ciérralo primero."
          errExe = "No se encontró dsignition.exe. Ejecuta primero build_windows.ps1."; errSetup = "No se encontraron los archivos del juego. Ejecuta primero Setup." }
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
$settings = @{ full_game = $false; language = $null }
if (Test-Path $settingsPath) {
    try {
        $j = Get-Content $settingsPath -Raw | ConvertFrom-Json
        if ($j.full_game) { $settings.full_game = $true }
        if ($j.language -and $langs.Contains([string]$j.language)) { $settings.language = [string]$j.language }
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
# internal set names (labels come from $T); Get-CurrentSet returns one of these keys
$sets   = [ordered]@{ xbox = "mods\original"; ps3 = "mods\ps3_buttons"; keyboard = "mods\keyboard_buttons" }
function SetLabel($key, $L) { switch ($key) { "xbox" { "Xbox 360" } "ps3" { "PlayStation 3" } default { $T[$L].kb } } }

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
$form.FormBorderStyle = "FixedDialog"; $form.MaximizeBox = $false
$form.StartPosition = "CenterScreen"
$form.ClientSize = New-Object System.Drawing.Size(320, 362)
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

$status = New-Object System.Windows.Forms.Label
$status.AutoSize = $true; $status.Location = New-Object System.Drawing.Point(16, 341)
$status.ForeColor = [System.Drawing.Color]::FromArgb(150, 170, 185)
$form.Controls.Add($status)

$about = New-Object System.Windows.Forms.LinkLabel
$about.AutoSize = $true
$about.Location = New-Object System.Drawing.Point(16, 314)
$about.LinkColor = [System.Drawing.Color]::FromArgb(120, 190, 230)
$about.Add_LinkClicked({
    $c = Join-Path $root "CREDITS.md"
    $text = if (Test-Path $c) { Get-Content $c -Raw } else { "DSI Recomp - recompiled by Killers' Heaven" }
    $f2 = New-Object System.Windows.Forms.Form
    $f2.Text = $T[(CurLang)].aboutTitle; $f2.StartPosition = "CenterParent"; $f2.Size = New-Object System.Drawing.Size(640, 560)
    $tb = New-Object System.Windows.Forms.TextBox
    $tb.Multiline = $true; $tb.ReadOnly = $true; $tb.ScrollBars = "Vertical"; $tb.Dock = "Fill"
    $tb.Font = New-Object System.Drawing.Font("Consolas", 9); $tb.Text = $text -replace "`r?`n", "`r`n"
    $f2.Controls.Add($tb); [void]$f2.ShowDialog($form)
})
$form.Controls.Add($about)

function CurLang { @($langs.Keys)[[math]::Max($langBox.SelectedIndex, 0)] }
function Apply-Texts {
    $L = CurLang; $t = $T[$L]
    $title.Text = "DSI RECOMP  -  $($t.by) Killers' Heaven"
    $langLabel.Text = $t.lang
    $group.Text = $t.group
    foreach ($k in $sets.Keys) { $radios[$k].Text = (SetLabel $k $L) + $(if ($radios[$k].Enabled) { "" } else { " $($t.missing)" }) }
    $skip.Text = $t.skip + $(if ($skip.Enabled) { "" } else { " $($t.filesmissing)" })
    $full.Text = $t.full
    $play.Text = $t.play
    $about.Text = $t.about
    $status.Text = "$($t.installed) " + $(if ($current) { SetLabel $current $L } else { $t.custom })
}
Apply-Texts
$langBox.Add_SelectedIndexChanged({ Apply-Texts })

$play.Add_Click({
    try {
        $choice = ($radios.Keys | Where-Object { $radios[$_].Checked } | Select-Object -First 1)
        if ($choice -and $choice -ne (Get-CurrentSet)) { Set-Buttons $choice }
        if ($skip.Enabled -and ($skip.Checked -ne (Get-LogosSkipped))) {
            $src = if ($skip.Checked) { $movieSkip } else { $movieOrig }
            Copy-Item $src $movie -Force -ErrorAction Stop
        }
        $t = $T[(CurLang)]
        if (-not (Test-Path $exe)) { throw $t.errExe }
        if (-not (Test-Path "$root\extracted\default.xex")) { throw $t.errSetup }
        New-Item -ItemType Directory -Force "$root\docs" | Out-Null
        $gameArgs = @("--game_data_root=`"$root\extracted`"", "--gpu_plugin=xenos", "--mnk_mode=true",
                  "--log_file=`"$root\docs\run_windows.log`"")
        if ($full.Checked) { $gameArgs += "--license_mask=1" }
        $gameArgs += "--user_language=$($langs[(CurLang)])"
        # play.bat reads full_game and user_language from this file
        try { [ordered]@{ full_game = $full.Checked; language = (CurLang); user_language = $langs[(CurLang)] } | ConvertTo-Json | Set-Content $settingsPath -Encoding ASCII } catch { }
        Start-Process -FilePath $exe -ArgumentList $gameArgs -WorkingDirectory $exeDir
        $form.Close()
    } catch {
        $t = $T[(CurLang)]
        [System.Windows.Forms.MessageBox]::Show("$($t.errStart): $($_.Exception.Message)`n`n$($t.errRunning)", "Dead Space Ignition") | Out-Null
    }
})

[void]$form.ShowDialog()
