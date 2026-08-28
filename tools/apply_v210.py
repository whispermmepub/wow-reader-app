from pathlib import Path

P = Path('app/src/main/java/com/whisper/wowreader/BookReaderActivity.java')
s = P.read_text(encoding='utf-8')

def repl(old, new, count=1):
    global s
    n = s.count(old)
    if n < count:
        raise SystemExit(f'anchor missing ({n} < {count}): {old[:120]!r}')
    s = s.replace(old, new, count)

# Default animation is now None, while 3D curl remains selectable.
repl('    private String pageAnimation = "paper";\n', '    private String pageAnimation = "none";\n')
repl('    private long lastChapterNavMs = 0L;\n', '    private long lastChapterNavMs = 0L;\n    private int chapterLoadGeneration = 0;\n')
repl('        pageAnimation = prefs.getString("epub_page_animation", "paper");\n        if (!"paper".equals(pageAnimation) && !"slide".equals(pageAnimation) && !"none".equals(pageAnimation))\n            pageAnimation = "paper";\n',
     '        pageAnimation = prefs.getString("epub_page_animation", "none");\n        if (!"paper".equals(pageAnimation) && !"slide".equals(pageAnimation) && !"none".equals(pageAnimation))\n            pageAnimation = "none";\n')
repl('        if (!prefs.getBoolean("reader_v20_defaults_applied", false)) {\n            pageAnimation = "paper";\n            prefs.edit().putString("epub_page_animation", "paper").putBoolean("reader_v20_defaults_applied", true).apply();\n        }\n',
     '        if (!prefs.getBoolean("reader_v20_defaults_applied", false)) {\n            pageAnimation = "none";\n            prefs.edit().putString("epub_page_animation", "none").putBoolean("reader_v20_defaults_applied", true).apply();\n        }\n        if (!prefs.getBoolean("reader_v210_animation_default_applied", false)) {\n            pageAnimation = "none";\n            prefs.edit().putString("epub_page_animation", "none")\n                    .putBoolean("reader_v210_animation_default_applied", true).apply();\n        }\n')

# Keep a generation token for every chapter navigation and hide the raw WebView until stable.
repl('        currentSelection = null;\n        hideSelectionBar();\n        chapterLoading = true;\n        pageTurnLocked = "page".equals(readingMode);\n        currentPageInChapter = 1;\n        pageCountInChapter = 1;\n        try {\n',
     '        currentSelection = null;\n        hideSelectionBar();\n        final int loadGeneration = ++chapterLoadGeneration;\n        chapterLoading = true;\n        pageTurnLocked = "page".equals(readingMode);\n        currentPageInChapter = 1;\n        pageCountInChapter = 1;\n        webView.animate().cancel();\n        webView.setAlpha(0f);\n        try {\n')

# onPageFinished no longer exposes an unstable chapter. It waits for page-ready stability.
old = '''            public void onPageFinished(WebView view, String url) {
                super.onPageFinished(view, url);
                applyReaderStyle(true);
                webView.postDelayed(() -> applySavedAnnotations(), 420L);
                webView.postDelayed(() -> applySavedAnnotations(), 1350L);
                webView.postDelayed(() -> installSelectionWatcher(), 500L);
                if ("scroll".equals(readingMode)) {
                    webView.postDelayed(() -> {
                        chapterLoading = false;
                        pageTurnLocked = false;
                        finishChapterFade();
                    }, 90L);
                } else {
                    // Page mode waits for onPageReady so pagination and fonts are
                    // final before the old chapter is removed from the screen.
                    webView.postDelayed(() -> {
                        if (!chapterLoading) return;
                        chapterLoading = false;
                        pageTurnLocked = false;
                        pendingChapterCurlDirection = 0;
                        if (pageCurlView != null) pageCurlView.release();
                        finishChapterFade();
                    }, 3200L);
                }
            }
'''
new = '''            public void onPageFinished(WebView view, String url) {
                super.onPageFinished(view, url);
                final int generation = chapterLoadGeneration;
                applyReaderStyle(true);
                webView.postDelayed(() -> {
                    if (generation == chapterLoadGeneration) applySavedAnnotations();
                }, 520L);
                webView.postDelayed(() -> {
                    if (generation == chapterLoadGeneration) applySavedAnnotations();
                }, 1450L);
                webView.postDelayed(() -> {
                    if (generation == chapterLoadGeneration) installSelectionWatcher();
                }, 560L);
                if ("scroll".equals(readingMode)) {
                    webView.postDelayed(() -> {
                        if (generation != chapterLoadGeneration) return;
                        revealStableChapter();
                    }, 110L);
                } else {
                    // Recheck if a device changes its edge-to-edge viewport just after navigation.
                    webView.postDelayed(() -> {
                        if (generation == chapterLoadGeneration && chapterLoading)
                            forceChapterRepaginate(generation);
                    }, 2100L);
                    webView.postDelayed(() -> {
                        if (generation == chapterLoadGeneration && chapterLoading)
                            forceChapterRepaginate(generation);
                    }, 3900L);
                }
            }
'''
repl(old, new)

# Capture the generation in the injected page engine.
repl('        int restore = restoreProgress ? currentProgressPermille : -1;\n',
     '        final int styleGeneration = chapterLoadGeneration;\n        int restore = restoreProgress ? currentProgressPermille : -1;\n')

old_measure = '''                    "st.measure=function(r){st.layout();st.page=0;st.pageMap=[0];flow.style.transition='none';flow.style.transform='translate3d('+st.marginPx+'px,0,0)';st.applyTypography();st.preparePagination();requestAnimationFrame(function(){requestAnimationFrame(function(){st.layout();var map=st.collectPageMap();if(!map.length){st.count=0;st.locked=false;WoW.onEmptyChapter();return;}st.pageMap=map;st.count=map.length;st.page=st.clamp(Math.round((st.count-1)*st.clamp(r,0,1)),0,st.count-1);st.apply(false);st.locked=false;st.report();WoW.onPageReady(st.page+1,st.count,st.progress());});});};" +
'''
new_measure = '''                    "st.measure=function(r){st.measureEpoch=(st.measureEpoch||0)+1;var epoch=st.measureEpoch,ratio=st.clamp(r,0,1),attempt=0,lastSig='',stableHits=0;" +
                    "var run=function(){if(epoch!==st.measureEpoch)return;st.layout();st.page=0;st.pageMap=[0];flow.style.transition='none';flow.style.transform='translate3d('+st.marginPx+'px,0,0)';st.applyTypography();st.preparePagination();" +
                    "requestAnimationFrame(function(){requestAnimationFrame(function(){if(epoch!==st.measureEpoch)return;st.layout();var map=st.collectPageMap();if(!map.length){st.count=0;st.locked=false;WoW.onEmptyChapter();return;}" +
                    "var sig=(viewport.clientWidth||0)+'x'+(viewport.clientHeight||0)+'|'+Math.round(flow.scrollWidth||0)+'|'+map.join(',');if(sig===lastSig)stableHits++;else{lastSig=sig;stableHits=0;}attempt++;" +
                    "if(stableHits<1&&attempt<7){setTimeout(run,76);return;}st.pageMap=map;st.count=map.length;st.page=st.clamp(Math.round((st.count-1)*ratio),0,st.count-1);st.apply(false);" +
                    "requestAnimationFrame(function(){if(epoch!==st.measureEpoch)return;var verify=st.collectPageMap();var sig2=(viewport.clientWidth||0)+'x'+(viewport.clientHeight||0)+'|'+Math.round(flow.scrollWidth||0)+'|'+verify.join(',');" +
                    "if(sig2!==sig&&attempt<9){lastSig=sig2;stableHits=0;setTimeout(run,64);return;}st.locked=false;st.report();WoW.onPageReady(" + styleGeneration + ",st.page+1,st.count,st.progress());});});});};run();};" +
'''
repl(old_measure, new_measure)

# Resize always relocks the page engine while reflow is happening.
repl("                    \"if(!st.resizeBound){st.resizeBound=true;window.addEventListener('resize',function(){if(st.mode!=='page')return;clearTimeout(st.resizeTimer);st.resizeTimer=setTimeout(function(){var r=st.progress()/1000;st.measure(r);},280);});}\" +\n",
     "                    \"if(!st.resizeBound){st.resizeBound=true;window.addEventListener('resize',function(){if(st.mode!=='page')return;st.locked=true;clearTimeout(st.resizeTimer);st.resizeTimer=setTimeout(function(){var r=st.progress()/1000;st.measure(r);},220);});}\" +\n")

# Page-ready callback is generation-aware and only reveals stable content once.
repl('    private void completePageReady() {\n        emptyChapterSkipCount = 0;\n',
     '    private void completePageReady(int generation) {\n        if (generation != chapterLoadGeneration || !chapterLoading) return;\n        emptyChapterSkipCount = 0;\n')
repl('            pageTurnLocked = false;\n            chapterLoading = false;\n            finishChapterFade();\n        });\n    }\n\n\n    private void skipEmptyEpubSpine() {',
     '            revealStableChapter();\n        });\n    }\n\n    private void revealStableChapter() {\n        if (webView != null) {\n            webView.animate().cancel();\n            webView.setAlpha(1f);\n        }\n        pageTurnLocked = false;\n        chapterLoading = false;\n        pendingChapterCurlDirection = 0;\n        if (pageCurlView != null && !pageCurlView.isBusy()) pageCurlView.release();\n        finishChapterFade();\n    }\n\n    private void forceChapterRepaginate(int generation) {\n        if (webView == null || generation != chapterLoadGeneration || !chapterLoading || !"page".equals(readingMode)) return;\n        try {\n            webView.evaluateJavascript(\n                    "(function(){var st=window.__wowPageEngine;if(!st||st.mode!==\'page\'||!st.measure)return false;st.locked=true;st.measure(st.progress()/1000);return true;})()",\n                    null);\n        } catch (Exception ignored) {}\n    }\n\n\n    private void skipEmptyEpubSpine() {')

# JavaScript bridge accepts the generation token.
repl('        public void onPageReady(int page, int count, int p) {\n            runOnUiThread(() -> {\n                if (!"page".equals(readingMode)) return;\n                updateEpubPageProgress(page, count, p);\n                completePageReady();\n            });\n        }\n',
     '        public void onPageReady(int generation, int page, int count, int p) {\n            runOnUiThread(() -> {\n                if (!"page".equals(readingMode) || generation != chapterLoadGeneration) return;\n                updateEpubPageProgress(page, count, p);\n                completePageReady(generation);\n            });\n        }\n')

# Reset and menu present None as the default.
repl('        String[] labels = {"3D page curl · default", "Smooth slide", "None"};\n        String[] values = {"paper", "slide", "none"};\n        int selected = "slide".equals(pageAnimation) ? 1 : ("none".equals(pageAnimation) ? 2 : 0);\n',
     '        String[] labels = {"None · default", "3D page curl", "Smooth slide"};\n        String[] values = {"none", "paper", "slide"};\n        int selected = "paper".equals(pageAnimation) ? 1 : ("slide".equals(pageAnimation) ? 2 : 0);\n')
repl('        pageAnimation = "paper";\n        readerTheme = 0;\n', '        pageAnimation = "none";\n        readerTheme = 0;\n')

P.write_text(s, encoding='utf-8')

B = Path('app/build.gradle')
b = B.read_text(encoding='utf-8')
b = b.replace('versionCode 21', 'versionCode 22')
b = b.replace("versionName '2.9.0'", "versionName '2.10.0'")
B.write_text(b, encoding='utf-8')

print('Applied WoW Reader v2.10.0 stable chapter pagination fix')
