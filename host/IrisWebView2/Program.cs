namespace IrisWebView2;

internal static class Program
{
    [STAThread]
    private static void Main(string[] args)
    {
        ApplicationConfiguration.Initialize();
        var url = args.Length > 0 && !string.IsNullOrWhiteSpace(args[0])
            ? args[0].Trim()
            : "http://127.0.0.1:5173/";
        Application.Run(new MainForm(url));
    }
}
