/**
 * WebView2 host bridge: the native shell closes the window when it receives
 * postMessage with action "close" (see host/IrisWebView2).
 */

type ChromeWebView = {
  postMessage: (message: string) => void;
};

function getChromeWebView(): ChromeWebView | undefined {
  const w = window as Window & { chrome?: { webview?: ChromeWebView } };
  return w.chrome?.webview;
}

export function isWebView2Host(): boolean {
  return typeof getChromeWebView()?.postMessage === 'function';
}

/** Ask the native WebView2 host to close the application window. */
export function requestHostClose(): void {
  const webview = getChromeWebView();
  if (!webview) {
    return;
  }
  try {
    webview.postMessage(JSON.stringify({ action: 'close', source: 'iris' }));
  } catch {
    /* ignore */
  }
}
