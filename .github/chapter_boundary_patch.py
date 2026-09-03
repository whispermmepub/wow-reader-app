from pathlib import Path

path = Path('app/src/main/java/com/whisper/wowreader/BookReaderActivity.java')
text = path.read_text(encoding='utf-8')

def replace_method(source: str, signature: str, replacement: str) -> str:
    start = source.find(signature)
    if start < 0:
        raise SystemExit(f'Could not locate {signature}')
    brace = source.find('{', start)
    if brace < 0:
        raise SystemExit(f'Could not locate opening brace for {signature}')
    depth = 0
    end = -1
    for i in range(brace, len(source)):
        if source[i] == '{':
            depth += 1
        elif source[i] == '}':
            depth -= 1
            if depth == 0:
                end = i + 1
                break
    if end < 0:
        raise SystemExit(f'Could not locate closing brace for {signature}')
    return source[:start] + replacement + source[end:]

# Only remove chapter-boundary visual animation. Preserve all existing load
# completion, lock release, curl cleanup and adjacent-chapter prewarm behavior.
text = replace_method(
    text,
    '    private void revealStableChapter()',
    '''    private void revealStableChapter() {
        if (webView != null) {
            webView.animate().cancel();
            webView.setAlpha(1f);
            // Chapter-boundary swaps are intentionally animation-free.
            // Page animation (None/Slide) still applies to pages inside a chapter.
            webView.setTranslationX(0f);
        }
        hideInitialReaderLoading();
        pageTurnLocked = false;
        chapterLoading = false;
        pendingChapterCurlDirection = 0;
        if (pageCurlView != null && !pageCurlView.isBusy()) pageCurlView.release();
        finishChapterFade();
        prewarmAdjacentChapters();
    }''',
)

text = replace_method(
    text,
    '    private void finishChapterFade()',
    '''    private void finishChapterFade() {
        // Keep the old frame only as a loading mask, then remove it instantly.
        // No fade, slide or translation is allowed between EPUB chapters.
        finishChapterFadeImmediate();
    }''',
)

required = [
    'hideInitialReaderLoading();',
    'pageTurnLocked = false;',
    'chapterLoading = false;',
    'pendingChapterCurlDirection = 0;',
    'prewarmAdjacentChapters();',
    'Chapter-boundary swaps are intentionally animation-free.',
]
for token in required:
    if token not in text:
        raise SystemExit(f'Required reader behavior missing after patch: {token}')
if 'long duration = "slide".equals(pageAnimation)' in text:
    raise SystemExit('Old chapter fade duration still present')
if 'webView.animate().translationX(0f).setDuration(175L)' in text:
    raise SystemExit('Old chapter slide-in still present')

path.write_text(text, encoding='utf-8')
