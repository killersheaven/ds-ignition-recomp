# Dead Space Ignition launcher: choose button prompts, then play.
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing
[System.Windows.Forms.Application]::EnableVisualStyles()

$root   = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$exeDir = Join-Path $root "port\out\build\win-amd64-release"
$exe    = Join-Path $exeDir "dsignition.exe"
$dst    = Join-Path $root "extracted\Resource"
# each button set = these files: path inside mods\<set>\  ->  path inside extracted\Resource\
$items  = @(
    @{ src = "subtitles_proj_EN.stz";              dst = "SumoTool\subtitles_proj_EN.stz" },
    @{ src = "popups_EN.stz";                      dst = "SumoTool\popups_EN.stz" },
    @{ src = "Frontend_EN.stz";                    dst = "SumoTool\Frontend_EN.stz" },
    @{ src = "HardwareCrack\HardwareCrackSet.zif"; dst = "HardwareCrack\HardwareCrackSet.zif" },
    @{ src = "HardwareCrack\HardwareCrackSet.zig"; dst = "HardwareCrack\HardwareCrackSet.zig" },
    @{ src = "SoftwareHack\SoftwareHackSet.zif";   dst = "SoftwareHack\SoftwareHackSet.zif" },
    @{ src = "SoftwareHack\SoftwareHackSet.zig";   dst = "SoftwareHack\SoftwareHackSet.zig" }
)
$settingsPath = Join-Path $root "launcher_settings.json"
$settings = @{ full_game = $false }
if (Test-Path $settingsPath) {
    try { $j = Get-Content $settingsPath -Raw | ConvertFrom-Json; if ($j.full_game) { $settings.full_game = $true } } catch { }
}
$movie  = Join-Path $root "extracted\Resource\Movies\EaHd.bik"
$movieOrig = Join-Path $root "mods\original\EaHd.bik"
$movieSkip = Join-Path $root "mods\skip_logos\EaHd.bik"
$sets   = [ordered]@{ "Xbox 360" = "mods\original"; "PlayStation 3" = "mods\ps3_buttons"; "Keyboard" = "mods\keyboard_buttons" }

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
$form.ClientSize = New-Object System.Drawing.Size(320, 326)
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
$title.Text = "DSI RECOMP  -  recompiled by Killers' Heaven"; $title.AutoSize = $true
$title.Font = New-Object System.Drawing.Font("Segoe UI", 8.5)
$title.ForeColor = [System.Drawing.Color]::FromArgb(150, 170, 185)
$title.Location = New-Object System.Drawing.Point(16, 74)
$form.Controls.Add($title)

$group = New-Object System.Windows.Forms.GroupBox
$group.Text = "Button prompts"; $group.ForeColor = $form.ForeColor
$group.Location = New-Object System.Drawing.Point(16, 104); $group.Size = New-Object System.Drawing.Size(288, 104)
$form.Controls.Add($group)

$current = Get-CurrentSet
$radios = @{}; $y = 22
foreach ($name in $sets.Keys) {
    $r = New-Object System.Windows.Forms.RadioButton
    $r.Text = $name; $r.AutoSize = $true; $r.Location = New-Object System.Drawing.Point(14, $y)
    if (@($items | Where-Object { -not (Test-Path (Join-Path (Join-Path $root $sets[$name]) $_.src)) }).Count) { $r.Enabled = $false; $r.Text += " (missing)" }
    if ($name -eq $current) { $r.Checked = $true }
    $group.Controls.Add($r); $radios[$name] = $r; $y += 26
}
if (-not $current) { $radios["Xbox 360"].Checked = $true }

$skip = New-Object System.Windows.Forms.CheckBox
$skip.Text = "Skip EA and Visceral logos"; $skip.AutoSize = $true
$skip.Location = New-Object System.Drawing.Point(18, 216)
$skip.Checked = Get-LogosSkipped
if (-not ((Test-Path $movieSkip) -and (Test-Path $movieOrig))) { $skip.Enabled = $false; $skip.Text += " (files missing)" }
$form.Controls.Add($skip)

$full = New-Object System.Windows.Forms.CheckBox
$full.Text = "I own the full game (unlock trial)"; $full.AutoSize = $true
$full.Location = New-Object System.Drawing.Point(18, 240)
$full.Checked = [bool]$settings.full_game
$form.Controls.Add($full)

$play = New-Object System.Windows.Forms.Button
$play.Text = "Play"; $play.Size = New-Object System.Drawing.Size(140, 36)
$play.Location = New-Object System.Drawing.Point(164, 276)
$play.FlatStyle = "Flat"; $play.BackColor = [System.Drawing.Color]::FromArgb(70, 96, 122)
$play.Font = New-Object System.Drawing.Font("Segoe UI Semibold", 11)
$form.AcceptButton = $play
$form.Controls.Add($play)

$status = New-Object System.Windows.Forms.Label
$status.AutoSize = $true; $status.Location = New-Object System.Drawing.Point(16, 305)
$status.ForeColor = [System.Drawing.Color]::FromArgb(150, 170, 185)
$status.Text = if ($current) { "Installed: $current" } else { "Installed: custom" }
$form.Controls.Add($status)

$about = New-Object System.Windows.Forms.LinkLabel
$about.Text = "About / credits"; $about.AutoSize = $true
$about.Location = New-Object System.Drawing.Point(16, 278)
$about.LinkColor = [System.Drawing.Color]::FromArgb(120, 190, 230)
$about.Add_LinkClicked({
    $c = Join-Path $root "CREDITS.md"
    $text = if (Test-Path $c) { Get-Content $c -Raw } else { "DSI Recomp - recompiled by Killers' Heaven" }
    $f2 = New-Object System.Windows.Forms.Form
    $f2.Text = "About DSI Recomp"; $f2.StartPosition = "CenterParent"; $f2.Size = New-Object System.Drawing.Size(640, 560)
    $tb = New-Object System.Windows.Forms.TextBox
    $tb.Multiline = $true; $tb.ReadOnly = $true; $tb.ScrollBars = "Vertical"; $tb.Dock = "Fill"
    $tb.Font = New-Object System.Drawing.Font("Consolas", 9); $tb.Text = $text -replace "`r?`n", "`r`n"
    $f2.Controls.Add($tb); [void]$f2.ShowDialog($form)
})
$form.Controls.Add($about)

$play.Add_Click({
    try {
        $choice = ($radios.Keys | Where-Object { $radios[$_].Checked } | Select-Object -First 1)
        if ($choice -and $choice -ne (Get-CurrentSet)) { Set-Buttons $choice }
        if ($skip.Enabled -and ($skip.Checked -ne (Get-LogosSkipped))) {
            $src = if ($skip.Checked) { $movieSkip } else { $movieOrig }
            Copy-Item $src $movie -Force -ErrorAction Stop
        }
        if (-not (Test-Path $exe)) { throw "dsignition.exe not found. Run build_windows.ps1 first." }
        $gameArgs = @("--game_data_root=`"$root\extracted`"", "--gpu_plugin=xenos", "--mnk_mode=true",
                  "--log_file=`"$root\docs\run_windows.log`"")
        if ($full.Checked) { $gameArgs += "--license_mask=1" }
        try { @{ full_game = $full.Checked } | ConvertTo-Json | Set-Content $settingsPath -Encoding ASCII } catch { }
        Start-Process -FilePath $exe -ArgumentList $gameArgs -WorkingDirectory $exeDir
        $form.Close()
    } catch {
        [System.Windows.Forms.MessageBox]::Show("Could not start: $($_.Exception.Message)`n`nIf the game is already running, close it first.", "Dead Space Ignition") | Out-Null
    }
})

[void]$form.ShowDialog()
