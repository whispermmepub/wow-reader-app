from pathlib import Path


def replace(path, old, new, count=1):
    p = Path(path)
    text = p.read_text(encoding='utf-8')
    if old not in text:
        raise SystemExit(f'pattern not found in {path}: {old[:140]!r}')
    text = text.replace(old, new, count)
    p.write_text(text, encoding='utf-8')

# Version
replace('app/build.gradle', "versionCode 24\n        versionName '2.12.0'", "versionCode 25\n        versionName '2.13.0'")

# ---------------- MainActivity: app themes + durable app-owned library ----------------
MAIN='app/src/main/java/com/whisper/wowreader/MainActivity.java'
replace(MAIN,
'''    private TextView accountButton;\n    private String sortMode = "added";''',
'''    private TextView accountButton;\n    private TextView themeButton;\n    private String appTheme = "white";\n    private String sortMode = "added";''')

replace(MAIN,
'''        prefs = getSharedPreferences("wow_reader", MODE_PRIVATE);\n        // Google account / Drive sync is intentionally deferred for a later release.\n        gridMode = prefs.getBoolean("library_grid", true);''',
'''        prefs = getSharedPreferences("wow_reader", MODE_PRIVATE);\n        appTheme = prefs.getString("app_theme", "white");\n        if (!"white".equals(appTheme) && !"black".equals(appTheme) && !"navy".equals(appTheme)) appTheme = "white";\n        applySystemBarTheme();\n        // Google account / Drive sync is intentionally deferred for a later release.\n        gridMode = prefs.getBoolean("library_grid", true);''')

replace(MAIN, '        root.setBackgroundColor(Color.rgb(247, 248, 251));', '        root.setBackgroundColor(themeBackground());')
replace(MAIN,
'''        floatingAdd.setBackground(gradientRoundRect(new int[]{\n                Color.rgb(92, 76, 226), Color.rgb(71, 113, 236)}, dp(29)));''',
'''        floatingAdd.setBackground(gradientRoundRect(themeFabColors(), dp(29)));''')

replace(MAIN,
'''        v.setTextColor(Color.rgb(52, 55, 62));\n        v.setGravity(Gravity.CENTER);\n        v.setBackground(roundRect(Color.argb(188, 255, 255, 255), dp(22), dp(1), Color.argb(80, 210, 214, 222)));''',
'''        v.setTextColor(themePrimaryText());\n        v.setGravity(Gravity.CENTER);\n        v.setBackground(roundRect(themeControlSurface(), dp(22), dp(1), themeStroke()));''')

replace(MAIN, '        heading.setTextColor(Color.rgb(74, 78, 88));', '        heading.setTextColor(themeSecondaryText());')
replace(MAIN, '        card.setBackground(roundRect(background, dp(18), dp(1), Color.argb(46, 80, 88, 105)));', '        card.setBackground(roundRect(themeDiscoverySurface(background), dp(18), dp(1), themeStroke()));')
replace(MAIN, '        t.setTextColor(Color.rgb(35, 38, 45));', '        t.setTextColor(themePrimaryText());')
replace(MAIN, '        sub.setTextColor(Color.rgb(99, 104, 116));', '        sub.setTextColor(themeSecondaryText());')

replace(MAIN, '        card.setBackground(roundRect(Color.WHITE, dp(18), dp(1), Color.rgb(232, 234, 240)));', '        card.setBackground(roundRect(themeCardSurface(), dp(18), dp(1), themeStroke()));', 2)
replace(MAIN, '        title.setTextColor(Color.rgb(29, 31, 37));', '        title.setTextColor(themePrimaryText());', 2)
replace(MAIN, '        meta.setTextColor(Color.rgb(103, 108, 120));', '        meta.setTextColor(themeSecondaryText());', 2)
replace(MAIN, '        track.setBackground(roundRect(Color.rgb(236, 238, 243), dp(2), 0, 0));', '        track.setBackground(roundRect(themeTrackColor(), dp(2), 0, 0));')
replace(MAIN, '        fill.setBackground(roundRect(Color.rgb(82, 82, 214), dp(2), 0, 0));', '        fill.setBackground(roundRect(themeAccent(), dp(2), 0, 0));')
replace(MAIN, '        action.setTextColor(Color.rgb(82, 82, 214));', '        action.setTextColor(themeAccent());')

replace(MAIN,
'''        hero.setBackground(gradientRoundRect(new int[]{Color.rgb(239, 243, 255), Color.rgb(255, 247, 242)}, dp(24)));''',
'''        hero.setBackground(gradientRoundRect(themeHeroColors(), dp(24)));''')
replace(MAIN, '        brand.setTextColor(Color.rgb(27, 29, 35));', '        brand.setTextColor(themePrimaryText());')
replace(MAIN, '        sub.setTextColor(Color.rgb(100, 104, 116));', '        sub.setTextColor(themeSecondaryText());', 1)

replace(MAIN,
'''        brandRow.addView(brandCopy, new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f));\n\n        viewModeButton = iconButton(gridMode ? "☷" : "▦");''',
'''        brandRow.addView(brandCopy, new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f));\n\n        themeButton = iconButton("navy".equals(appTheme) ? "✦" : "◐");\n        themeButton.setTextSize(17);\n        themeButton.setContentDescription("App theme");\n        themeButton.setOnClickListener(v -> showAppThemeDialog());\n        brandRow.addView(themeButton, new LinearLayout.LayoutParams(dp(44), dp(44)));\n\n        viewModeButton = iconButton(gridMode ? "☷" : "▦");''')

replace(MAIN, '        searchInput.setTextColor(Color.rgb(31, 34, 40));', '        searchInput.setTextColor(themePrimaryText());')
replace(MAIN, '        searchInput.setHintTextColor(Color.rgb(118, 123, 136));', '        searchInput.setHintTextColor(themeSecondaryText());')
replace(MAIN, '        searchInput.setBackground(roundRect(Color.argb(218, 255, 255, 255), dp(23), dp(1), Color.argb(70, 180, 185, 198)));', '        searchInput.setBackground(roundRect(themeSearchSurface(), dp(23), dp(1), themeStroke()));')

replace(MAIN, '        label.setTextColor(Color.rgb(31, 34, 40));', '        label.setTextColor(themePrimaryText());')
replace(MAIN, '        countView.setTextColor(Color.rgb(112, 116, 128));', '        countView.setTextColor(themeSecondaryText());')
replace(MAIN, '        sortButton.setTextColor(Color.rgb(67, 68, 190));', '        sortButton.setTextColor(themeAccent());')
replace(MAIN, '        sortButton.setBackground(roundRect(Color.argb(220, 255, 255, 255), dp(19), dp(1), Color.argb(72, 126, 126, 210)));', '        sortButton.setBackground(roundRect(themeControlSurface(), dp(19), dp(1), themeStroke()));')
replace(MAIN, '        authorButton.setTextColor(Color.rgb(67, 68, 190));', '        authorButton.setTextColor(themeAccent());')
replace(MAIN, '        authorButton.setBackground(roundRect(Color.argb(220, 255, 255, 255), dp(19), dp(1), Color.argb(72, 126, 126, 210)));', '        authorButton.setBackground(roundRect(themeControlSurface(), dp(19), dp(1), themeStroke()));')
replace(MAIN, '        empty.setTextColor(Color.rgb(104, 109, 121));', '        empty.setTextColor(themeSecondaryText());')

# Local-copy ownership semantics. Import already streams into app-private libraryDir; make it explicit and preserve it.
replace(MAIN,
'''                        .putString("library_author_"+out.getName(),displayAuthor)\n                        .putLong("sync_updated_ms",System.currentTimeMillis())''',
'''                        .putString("library_author_"+out.getName(),displayAuthor)\n                        .putBoolean("library_owned_"+out.getName(),true)\n                        .putLong("sync_updated_ms",System.currentTimeMillis())''')
replace(MAIN, '                    Toast.makeText(this,"Added to Library",Toast.LENGTH_SHORT).show();', '                    Toast.makeText(this,"Added to Library · local copy saved",Toast.LENGTH_SHORT).show();')
replace(MAIN,
'''    private void confirmDelete(File file){new AlertDialog.Builder(this).setTitle("Remove from library?").setMessage(stripExtension(file.getName())).setNegativeButton("Cancel",null).setPositiveButton("Remove",(d,w)->{if(file.delete()){prefs.edit().remove("percent_"+file.getName()).remove("library_title_"+file.getName()).remove("library_author_"+file.getName()).remove("added_at_"+file.getName()).remove("last_opened_"+file.getName()).putLong("sync_updated_ms",System.currentTimeMillis()).apply();refreshLibrary();maybeAutoGoogleSync();}}).show();}''',
'''    private void confirmDelete(File file){new AlertDialog.Builder(this).setTitle("Remove from WoW Reader?").setMessage(stripExtension(file.getName())+"\\n\\nThis deletes WoW Reader's saved local copy. The original file you imported from Downloads or another folder is not changed.").setNegativeButton("Cancel",null).setPositiveButton("Remove",(d,w)->{if(file.delete()){prefs.edit().remove("percent_"+file.getName()).remove("library_title_"+file.getName()).remove("library_author_"+file.getName()).remove("library_owned_"+file.getName()).remove("added_at_"+file.getName()).remove("last_opened_"+file.getName()).putLong("sync_updated_ms",System.currentTimeMillis()).apply();refreshLibrary();maybeAutoGoogleSync();}}).show();}''')

# Add theme helpers before gradientRoundRect.
replace(MAIN,
'''    private GradientDrawable gradientRoundRect(int[] colors, int radius) {''',
'''    private boolean isBlackAppTheme() { return "black".equals(appTheme); }\n    private boolean isNavyAppTheme() { return "navy".equals(appTheme); }\n\n    private int themeBackground() {\n        if (isBlackAppTheme()) return Color.rgb(12, 13, 16);\n        if (isNavyAppTheme()) return Color.rgb(3, 28, 48);\n        return Color.rgb(247, 248, 251);\n    }\n\n    private int themeCardSurface() {\n        if (isBlackAppTheme()) return Color.rgb(27, 29, 34);\n        if (isNavyAppTheme()) return Color.rgb(7, 44, 70);\n        return Color.WHITE;\n    }\n\n    private int themeControlSurface() {\n        if (isBlackAppTheme()) return Color.rgb(35, 37, 43);\n        if (isNavyAppTheme()) return Color.rgb(10, 51, 79);\n        return Color.argb(232, 255, 255, 255);\n    }\n\n    private int themeSearchSurface() {\n        if (isBlackAppTheme()) return Color.rgb(28, 30, 35);\n        if (isNavyAppTheme()) return Color.rgb(6, 42, 67);\n        return Color.argb(232, 255, 255, 255);\n    }\n\n    private int themePrimaryText() {\n        return (isBlackAppTheme() || isNavyAppTheme()) ? Color.rgb(244, 247, 250) : Color.rgb(31, 34, 40);\n    }\n\n    private int themeSecondaryText() {\n        if (isBlackAppTheme()) return Color.rgb(178, 183, 192);\n        if (isNavyAppTheme()) return Color.rgb(165, 196, 213);\n        return Color.rgb(105, 110, 122);\n    }\n\n    private int themeAccent() {\n        if (isBlackAppTheme()) return Color.rgb(151, 166, 255);\n        if (isNavyAppTheme()) return Color.rgb(239, 194, 91);\n        return Color.rgb(82, 82, 214);\n    }\n\n    private int themeStroke() {\n        if (isBlackAppTheme()) return Color.rgb(55, 59, 68);\n        if (isNavyAppTheme()) return Color.rgb(26, 91, 120);\n        return Color.rgb(224, 227, 234);\n    }\n\n    private int themeTrackColor() {\n        if (isBlackAppTheme()) return Color.rgb(50, 53, 61);\n        if (isNavyAppTheme()) return Color.rgb(18, 67, 91);\n        return Color.rgb(236, 238, 243);\n    }\n\n    private int[] themeHeroColors() {\n        if (isBlackAppTheme()) return new int[]{Color.rgb(30, 32, 39), Color.rgb(19, 20, 25)};\n        if (isNavyAppTheme()) return new int[]{Color.rgb(4, 45, 73), Color.rgb(2, 29, 51), Color.rgb(4, 52, 74)};\n        return new int[]{Color.rgb(239, 243, 255), Color.rgb(255, 247, 242)};\n    }\n\n    private int[] themeFabColors() {\n        if (isBlackAppTheme()) return new int[]{Color.rgb(104, 91, 226), Color.rgb(63, 79, 170)};\n        if (isNavyAppTheme()) return new int[]{Color.rgb(8, 174, 199), Color.rgb(10, 105, 145)};\n        return new int[]{Color.rgb(92, 76, 226), Color.rgb(71, 113, 236)};\n    }\n\n    private int themeDiscoverySurface(int lightFallback) {\n        if (isBlackAppTheme()) return Color.rgb(29, 32, 38);\n        if (isNavyAppTheme()) return Color.rgb(7, 49, 77);\n        return lightFallback;\n    }\n\n    private void applySystemBarTheme() {\n        int bg = themeBackground();\n        getWindow().setStatusBarColor(bg);\n        getWindow().setNavigationBarColor(bg);\n        int flags = 0;\n        if (!isBlackAppTheme() && !isNavyAppTheme()) flags = View.SYSTEM_UI_FLAG_LIGHT_STATUS_BAR | View.SYSTEM_UI_FLAG_LIGHT_NAVIGATION_BAR;\n        getWindow().getDecorView().setSystemUiVisibility(flags);\n    }\n\n    private void showAppThemeDialog() {\n        String[] labels = {"White", "Black", "Navy Premium"};\n        String[] values = {"white", "black", "navy"};\n        int selected = isBlackAppTheme() ? 1 : (isNavyAppTheme() ? 2 : 0);\n        new AlertDialog.Builder(this)\n                .setTitle("App theme")\n                .setSingleChoiceItems(labels, selected, (dialog, which) -> {\n                    String chosen = values[which];\n                    if (!chosen.equals(appTheme)) {\n                        appTheme = chosen;\n                        prefs.edit().putString("app_theme", appTheme).apply();\n                        dialog.dismiss();\n                        recreate();\n                    } else dialog.dismiss();\n                })\n                .setNegativeButton("Cancel", null)\n                .show();\n    }\n\n    private GradientDrawable gradientRoundRect(int[] colors, int radius) {''')

# ---------------- BookReaderActivity: distinct native Slide + faster chapter transition ----------------
READER='app/src/main/java/com/whisper/wowreader/BookReaderActivity.java'
replace(READER,
'''    private ImageView readerStyleOverlay;\n    private Bitmap readerStyleBitmap;''',
'''    private ImageView readerStyleOverlay;\n    private ImageView pageSlideOverlay;\n    private Bitmap pageSlideBitmap;\n    private Bitmap readerStyleBitmap;''')

replace(READER,
'''        readerStyleOverlay.setFocusable(false);\n        content.addView(readerStyleOverlay, new FrameLayout.LayoutParams(\n                ViewGroup.LayoutParams.MATCH_PARENT,\n                ViewGroup.LayoutParams.MATCH_PARENT));\n\n        pageCurlView = new PageCurlView(this);''',
'''        readerStyleOverlay.setFocusable(false);\n        content.addView(readerStyleOverlay, new FrameLayout.LayoutParams(\n                ViewGroup.LayoutParams.MATCH_PARENT,\n                ViewGroup.LayoutParams.MATCH_PARENT));\n\n        pageSlideOverlay = new ImageView(this);\n        pageSlideOverlay.setScaleType(ImageView.ScaleType.FIT_XY);\n        pageSlideOverlay.setVisibility(View.GONE);\n        pageSlideOverlay.setClickable(false);\n        pageSlideOverlay.setFocusable(false);\n        content.addView(pageSlideOverlay, new FrameLayout.LayoutParams(\n                ViewGroup.LayoutParams.MATCH_PARENT,\n                ViewGroup.LayoutParams.MATCH_PARENT));\n\n        pageCurlView = new PageCurlView(this);''')

replace(READER,
'''        if ("paper".equals(pageAnimation) && pageCurlView != null) {\n            float touch = webView.getHeight() <= 0 ? 0.5f : Math.max(0.12f, Math.min(0.88f, tapY / (float) webView.getHeight()));\n            startNativeTapCurl(direction, targetPage - 1, touch);\n        } else {\n            performJsPageTurn(direction);\n        }''',
'''        if ("slide".equals(pageAnimation)) startNativeSlidePageTurn(direction, targetPage - 1);\n        else performJsPageTurn(direction);''')

replace(READER,
'''        if ("paper".equals(pageAnimation) && pageCurlView != null)\n            startNativePageCurl(direction, targetPage - 1);\n        else\n            performJsPageTurn(direction);''',
'''        if ("slide".equals(pageAnimation)) startNativeSlidePageTurn(direction, targetPage - 1);\n        else performJsPageTurn(direction);''')

# Insert native slide implementation before old curl code. Old 3D code stays unreachable/backward-compatible but is not exposed.
replace(READER,
'''    private void startNativePageCurl(int direction, int targetZeroBased) {''',
'''    private void startNativeSlidePageTurn(int direction, int targetZeroBased) {\n        if (webView == null || pageSlideOverlay == null) { performJsPageTurn(direction); return; }\n        Bitmap current = captureWebViewBitmap();\n        if (current == null) { performJsPageTurn(direction); return; }\n        if (pageSlideBitmap != null && !pageSlideBitmap.isRecycled()) pageSlideBitmap.recycle();\n        pageSlideBitmap = current;\n        pageTurnLocked = true;\n        pageSlideOverlay.animate().cancel();\n        pageSlideOverlay.setImageBitmap(current);\n        pageSlideOverlay.setAlpha(1f);\n        pageSlideOverlay.setTranslationX(0f);\n        pageSlideOverlay.setVisibility(View.VISIBLE);\n        pageSlideOverlay.bringToFront();\n\n        String jump = "(function(){var st=window.__wowPageEngine;if(!st||st.mode!=='page')return 'unavailable';" +\n                "st.locked=true;st.page=st.clamp(" + targetZeroBased + ",0,(st.count||1)-1);st.apply(false);return 'ok';})()";\n        try {\n            webView.evaluateJavascript(jump, result -> {\n                if (result == null || result.contains("unavailable")) {\n                    finishNativeSlidePageTurn(false);\n                    performJsPageTurn(direction);\n                    return;\n                }\n                webView.postOnAnimation(() -> {\n                    float distance = Math.max(1f, webView.getWidth());\n                    webView.animate().cancel();\n                    webView.setTranslationX(direction > 0 ? distance * 0.055f : -distance * 0.055f);\n                    webView.setAlpha(0.92f);\n                    webView.animate().translationX(0f).alpha(1f).setDuration(205L)\n                            .setInterpolator(new android.view.animation.DecelerateInterpolator(1.45f)).start();\n                    pageSlideOverlay.animate().translationX(direction > 0 ? -distance : distance).alpha(0.18f)\n                            .setDuration(215L).setInterpolator(new android.view.animation.DecelerateInterpolator(1.28f))\n                            .withEndAction(() -> finishNativeSlidePageTurn(true)).start();\n                });\n            });\n        } catch (Exception e) {\n            finishNativeSlidePageTurn(false);\n            performJsPageTurn(direction);\n        }\n    }\n\n    private void finishNativeSlidePageTurn(boolean report) {\n        if (pageSlideOverlay != null) {\n            pageSlideOverlay.animate().cancel();\n            pageSlideOverlay.setVisibility(View.GONE);\n            pageSlideOverlay.setImageDrawable(null);\n            pageSlideOverlay.setAlpha(1f);\n            pageSlideOverlay.setTranslationX(0f);\n        }\n        if (pageSlideBitmap != null && !pageSlideBitmap.isRecycled()) pageSlideBitmap.recycle();\n        pageSlideBitmap = null;\n        if (webView != null) {\n            webView.animate().cancel();\n            webView.setTranslationX(0f);\n            webView.setAlpha(1f);\n            try {\n                webView.evaluateJavascript(report\n                        ? "(function(){var st=window.__wowPageEngine;if(!st)return;st.locked=false;st.report();WoW.onPageTurnComplete((st.page||0)+1,st.count||1,st.progress());})()"\n                        : "if(window.__wowPageEngine)window.__wowPageEngine.locked=false", null);\n            } catch (Exception ignored) {}\n        }\n        pageTurnLocked = false;\n    }\n\n    private void startNativePageCurl(int direction, int targetZeroBased) {''')

# Chapter transition: make movement immediate and crossfade shorter; no frozen-feeling static overlay.
replace(READER,
'''        chapterTransitionOverlay.setAlpha(1f);\n        chapterTransitionOverlay.setVisibility(View.VISIBLE);\n        chapterTransitionOverlay.bringToFront();\n        pendingChapterFade = true;''',
'''        chapterTransitionOverlay.animate().cancel();\n        chapterTransitionOverlay.setAlpha(1f);\n        chapterTransitionOverlay.setTranslationX(0f);\n        chapterTransitionOverlay.setVisibility(View.VISIBLE);\n        chapterTransitionOverlay.bringToFront();\n        pendingChapterFade = true;\n        chapterTransitionOverlay.animate()\n                .translationX((direction < 0 ? 1f : -1f) * dp(10))\n                .alpha(0.94f).setDuration(135L)\n                .setInterpolator(new android.view.animation.DecelerateInterpolator(1.5f)).start();''')
replace(READER, '        chapterTransitionOverlay.animate().alpha(0f).setDuration(190L).withEndAction(this::finishChapterFadeImmediate).start();', '        chapterTransitionOverlay.animate().alpha(0f).translationX(0f).setDuration(115L).setInterpolator(new android.view.animation.DecelerateInterpolator(1.55f)).withEndAction(this::finishChapterFadeImmediate).start();')
replace(READER,
'''            chapterTransitionOverlay.setAlpha(1f);\n        }''',
'''            chapterTransitionOverlay.setAlpha(1f);\n            chapterTransitionOverlay.setTranslationX(0f);\n        }''', 1)

# Warm neighboring chapter bytes after a stable reveal so the next/previous file is in the OS cache before the user turns.
replace(READER,
'''        finishChapterFade();\n    }\n\n    private void forceChapterRepaginate''',
'''        finishChapterFade();\n        prewarmAdjacentChapters();\n    }\n\n    private void prewarmAdjacentChapters() {\n        if (spine.isEmpty()) return;\n        final int here = currentSpine;\n        new Thread(() -> {\n            byte[] buffer = new byte[64 * 1024];\n            int[] targets = {here - 1, here + 1};\n            for (int idx : targets) {\n                if (idx < 0 || idx >= spine.size()) continue;\n                File f = spine.get(idx);\n                try (InputStream in = new FileInputStream(f)) {\n                    int left = 512 * 1024;\n                    while (left > 0) {\n                        int n = in.read(buffer, 0, Math.min(buffer.length, left));\n                        if (n <= 0) break;\n                        left -= n;\n                    }\n                } catch (Exception ignored) {}\n            }\n        }, "wow-chapter-prewarm").start();\n    }\n\n    private void forceChapterRepaginate''')

# JS Slide is now handled natively; keep JS instant to avoid double animation if called from fallback paths.
replace(READER,
'''                    "st.paperTurn=function(d,done){var mode=" + jsQuote(pageAnimation) + ";if(mode==='none'){st.apply(false);done();return;}st.apply(true);setTimeout(done,mode==='slide'?165:185);};" +''',
'''                    "st.paperTurn=function(d,done){st.apply(false);done();};" +''')

# ---------------- SplashActivity: follow selected app theme ----------------
SPLASH='app/src/main/java/com/whisper/wowreader/SplashActivity.java'
replace(SPLASH,
'''        int bg = Color.rgb(247, 248, 253);\n        getWindow().setStatusBarColor(bg);\n        getWindow().setNavigationBarColor(bg);\n        getWindow().getDecorView().setSystemUiVisibility(\n                View.SYSTEM_UI_FLAG_LIGHT_STATUS_BAR | View.SYSTEM_UI_FLAG_LIGHT_NAVIGATION_BAR);\n\n        FrameLayout root = new FrameLayout(this);\n        GradientDrawable background = new GradientDrawable(\n                GradientDrawable.Orientation.TL_BR,\n                new int[]{Color.rgb(242, 245, 255), Color.rgb(252, 248, 255), Color.rgb(255, 248, 242)});''',
'''        String appTheme = getSharedPreferences("wow_reader", MODE_PRIVATE).getString("app_theme", "white");\n        boolean black = "black".equals(appTheme);\n        boolean navy = "navy".equals(appTheme);\n        int bg = black ? Color.rgb(12, 13, 16) : (navy ? Color.rgb(3, 28, 48) : Color.rgb(247, 248, 253));\n        getWindow().setStatusBarColor(bg);\n        getWindow().setNavigationBarColor(bg);\n        getWindow().getDecorView().setSystemUiVisibility((black || navy) ? 0 :\n                (View.SYSTEM_UI_FLAG_LIGHT_STATUS_BAR | View.SYSTEM_UI_FLAG_LIGHT_NAVIGATION_BAR));\n\n        FrameLayout root = new FrameLayout(this);\n        int[] splashColors = black\n                ? new int[]{Color.rgb(23, 25, 30), Color.rgb(10, 11, 14), Color.rgb(18, 20, 24)}\n                : (navy\n                ? new int[]{Color.rgb(3, 41, 67), Color.rgb(2, 25, 44), Color.rgb(4, 51, 70)}\n                : new int[]{Color.rgb(242, 245, 255), Color.rgb(252, 248, 255), Color.rgb(255, 248, 242)});\n        GradientDrawable background = new GradientDrawable(\n                GradientDrawable.Orientation.TL_BR, splashColors);''')
replace(SPLASH, '        cardBg.setColor(Color.argb(238, 255, 255, 255));', '        cardBg.setColor(black ? Color.rgb(31, 34, 40) : (navy ? Color.rgb(7, 48, 75) : Color.argb(238, 255, 255, 255)));')
replace(SPLASH, '        title.setTextColor(Color.rgb(28, 30, 38));', '        title.setTextColor((black || navy) ? Color.rgb(244, 247, 250) : Color.rgb(28, 30, 38));')
replace(SPLASH, '        sub.setTextColor(Color.rgb(102, 106, 120));', '        sub.setTextColor(black ? Color.rgb(176, 181, 190) : (navy ? Color.rgb(161, 195, 213) : Color.rgb(102, 106, 120)));')
replace(SPLASH, '        dot.setTextColor(Color.rgb(83, 82, 211));', '        dot.setTextColor(navy ? Color.rgb(239, 194, 91) : Color.rgb(83, 82, 211));')
replace(SPLASH, '        whisper.setTextColor(Color.rgb(122, 126, 140));', '        whisper.setTextColor(black ? Color.rgb(154, 159, 169) : (navy ? Color.rgb(178, 202, 214) : Color.rgb(122, 126, 140)));')

print('Applied WoW Reader v2.13.0 migration')
