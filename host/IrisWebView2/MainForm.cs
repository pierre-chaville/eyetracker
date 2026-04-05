using System.Text.Json;
using Microsoft.Web.WebView2.Core;
using Microsoft.Web.WebView2.WinForms;

namespace IrisWebView2;

/// <summary>
/// Hosts the Vue UI in WebView2. The page requests shutdown via
/// <c>chrome.webview.postMessage(JSON.stringify({ action: 'close' }))</c>.
/// </summary>
public sealed class MainForm : Form
{
    private readonly WebView2 _webView = new() { Dock = DockStyle.Fill };
    private readonly string _startUrl;

    public MainForm(string startUrl)
    {
        _startUrl = startUrl;
        Text = "Iris";
        // No title bar / window chrome — use in-app Exit (or Alt+F4) to close.
        FormBorderStyle = FormBorderStyle.None;
        StartPosition = FormStartPosition.CenterScreen;
        WindowState = FormWindowState.Maximized;
        Controls.Add(_webView);
        Shown += async (_, _) => await InitializeWebViewAsync();
    }

    private async Task InitializeWebViewAsync()
    {
        try
        {
            await _webView.EnsureCoreWebView2Async();
        }
        catch (Exception ex)
        {
            MessageBox.Show(
                this,
                "WebView2 runtime is required. Install the WebView2 Runtime from Microsoft, then try again.\n\n" + ex.Message,
                "Iris — WebView2",
                MessageBoxButtons.OK,
                MessageBoxIcon.Error);
            Close();
            return;
        }

        var core = _webView.CoreWebView2;
        core.Settings.IsStatusBarEnabled = false;
        core.Settings.AreDefaultContextMenusEnabled = true;
        core.Settings.IsZoomControlEnabled = true;
        core.WebMessageReceived += OnWebMessageReceived;
        core.Navigate(_startUrl);
    }

    private void OnWebMessageReceived(object? sender, CoreWebView2WebMessageReceivedEventArgs e)
    {
        string? raw = null;
        try
        {
            raw = e.TryGetWebMessageAsString();
        }
        catch
        {
            /* ignore */
        }

        if (string.IsNullOrEmpty(raw))
            return;

        if (string.Equals(raw, "close", StringComparison.OrdinalIgnoreCase)
            || string.Equals(raw, "exit", StringComparison.OrdinalIgnoreCase))
        {
            BeginInvoke(Close);
            return;
        }

        try
        {
            using var doc = JsonDocument.Parse(raw);
            var root = doc.RootElement;
            if (root.TryGetProperty("action", out var a)
                && a.GetString() is { } action
                && (action.Equals("close", StringComparison.OrdinalIgnoreCase)
                    || action.Equals("exit", StringComparison.OrdinalIgnoreCase)))
            {
                BeginInvoke(Close);
            }
        }
        catch
        {
            /* not JSON */
        }
    }

}
