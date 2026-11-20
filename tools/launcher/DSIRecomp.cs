// DSI Recomp.exe - starts the launcher (tools\launcher\launcher.ps1) without a console window.
// Built by build_windows.ps1 / make_release.ps1 with the C# compiler that ships with Windows
// (.NET Framework 4, csc.exe), with the DSI icon. MIT License, Killers' Heaven.
using System;
using System.Diagnostics;
using System.IO;
using System.Windows.Forms;

static class DsiRecompLauncher
{
    [STAThread]
    static void Main()
    {
        string root = AppDomain.CurrentDomain.BaseDirectory;
        string script = Path.Combine(root, @"tools\launcher\launcher.ps1");
        if (!File.Exists(script))
        {
            MessageBox.Show("tools\\launcher\\launcher.ps1 is missing. Unzip the whole DSI Recomp folder again.",
                            "DSI Recomp", MessageBoxButtons.OK, MessageBoxIcon.Error);
            return;
        }
        var psi = new ProcessStartInfo("powershell.exe",
            "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File \"" + script + "\"");
        psi.UseShellExecute = false;
        psi.CreateNoWindow = true;
        psi.WorkingDirectory = root;
        try { Process.Start(psi); }
        catch (Exception e)
        {
            MessageBox.Show("Could not start the launcher: " + e.Message, "DSI Recomp",
                            MessageBoxButtons.OK, MessageBoxIcon.Error);
        }
    }
}
