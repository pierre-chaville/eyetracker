/**
 * Fullscreen API helpers. Always await exit calls — bare document.exitFullscreen()
 * returns a Promise; rejections (e.g. "Document not active") are otherwise uncaught.
 */

export type FullscreenCapableDocument = Document & {
  webkitFullscreenElement?: Element | null;
  msFullscreenElement?: Element | null;
  webkitExitFullscreen?: () => Promise<void>;
  msExitFullscreen?: () => Promise<void>;
};

export function isDocumentElementFullscreen(doc: Document = document): boolean {
  const d = doc as FullscreenCapableDocument;
  return !!(d.fullscreenElement || d.webkitFullscreenElement || d.msFullscreenElement);
}

/**
 * Exit browser fullscreen if this document is actually in fullscreen.
 * Swallows rejections (inactive document, double-exit, etc.).
 */
export async function safeExitFullscreen(doc: Document = document): Promise<void> {
  if (!isDocumentElementFullscreen(doc)) {
    return;
  }
  const d = doc as FullscreenCapableDocument;
  try {
    if (d.exitFullscreen) {
      await d.exitFullscreen();
    } else if (d.webkitExitFullscreen) {
      await d.webkitExitFullscreen();
    } else if (d.msExitFullscreen) {
      await d.msExitFullscreen();
    }
  } catch {
    /* InvalidStateError, Document not active, etc. */
  }
}
