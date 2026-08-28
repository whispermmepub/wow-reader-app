from pathlib import Path

P = Path('app/src/main/java/com/whisper/wowreader/BookReaderActivity.java')
s = P.read_text(encoding='utf-8')

def repl(old, new, count=1):
    global s
    n = s.count(old)
    if n < count:
        raise SystemExit(f'anchor missing ({n} < {count}): {old[:140]!r}')
    s = s.replace(old, new, count)

# Imports for the unified display sheet, progress scrubber and Night Light.
repl('import android.widget.ScrollView;\nimport android.widget.TextView;\n',
     'import android.widget.ScrollView;\nimport android.widget.SeekBar;\nimport android.widget.TextView;\n')
repl('import java.util.List;\nimport java.util.Locale;\n',
     'import java.util.List;\nimport java.util.Locale;\nimport java.util.Calendar;\n')

# Reader chrome state.
repl('    private LinearLayout selectionBar;\n    private SelectionData currentSelection;\n',
     '    private LinearLayout selectionBar;\n    private SeekBar readingSeek;\n    private boolean readingSeekDragging = false;\n    private View nightLightOverlay;\n    private Runnable chromeAutoHideRunnable;\n    private SelectionData currentSelection;\n')
repl('    private int brightnessPercent = -1;\n',
     '    private int brightnessPercent = -1;\n    private String nightLightMode = "off";\n')

# Load Night Light preference.
repl('        brightnessPercent = prefs.getInt("reader_brightness", -1);\n',
     '        brightnessPercent = prefs.getInt("reader_brightness", -1);\n        nightLightMode = prefs.getString("reader_night_light", "off");\n        if (!"off".equals(nightLightMode) && !"auto".equals(nightLightMode) && !"on".equals(nightLightMode)) nightLightMode = "off";\n')

# Add a warm overlay above page content but below reader controls.
repl('        if (isPdf) setupPdfView(content); else setupWebView(content);\n\n        topBar = new LinearLayout(this);\n',
     '        if (isPdf) setupPdfView(content); else setupWebView(content);\n\n        nightLightOverlay = new View(this);\n        nightLightOverlay.setClickable(false);\n        nightLightOverlay.setFocusable(false);\n        nightLightOverlay.setBackgroundColor(Color.rgb(255, 160, 72));\n        nightLightOverlay.setAlpha(0f);\n        root.addView(nightLightOverlay, new FrameLayout.LayoutParams(\n                ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.MATCH_PARENT));\n\n        topBar = new LinearLayout(this);\n')

# Add a Play-Books-style reading progress scrubber just above the bottom chrome.
anchor = '''        root.addView(bottomBar, bottomLp);\n\n        selectionBar = new LinearLayout(this);\n'''
insert = '''        root.addView(bottomBar, bottomLp);\n\n        readingSeek = new SeekBar(this);\n        readingSeek.setMax(1000);\n        readingSeek.setProgress(0);\n        readingSeek.setPadding(dp(2), 0, dp(2), 0);\n        readingSeek.setVisibility(View.GONE);\n        readingSeek.setAlpha(0f);\n        readingSeek.setContentDescription("Reading progress");\n        readingSeek.setOnSeekBarChangeListener(new SeekBar.OnSeekBarChangeListener() {\n            @Override public void onProgressChanged(SeekBar seekBar, int progress, boolean fromUser) {\n                if (!fromUser || positionView == null) return;\n                int percent = Math.max(0, Math.min(100, Math.round(progress / 10f)));\n                positionView.setText("" + percent + "%");\n            }\n            @Override public void onStartTrackingTouch(SeekBar seekBar) {\n                readingSeekDragging = true;\n                cancelChromeAutoHide();\n            }\n            @Override public void onStopTrackingTouch(SeekBar seekBar) {\n                int target = seekBar.getProgress();\n                readingSeekDragging = false;\n                seekToOverallProgress(target);\n                scheduleChromeAutoHide();\n            }\n        });\n        FrameLayout.LayoutParams seekLp = new FrameLayout.LayoutParams(\n                ViewGroup.LayoutParams.MATCH_PARENT, dp(32), Gravity.BOTTOM);\n        seekLp.leftMargin = dp(48);\n        seekLp.rightMargin = dp(48);\n        seekLp.bottomMargin = dp(64);\n        root.addView(readingSeek, seekLp);\n\n        selectionBar = new LinearLayout(this);\n'''
repl(anchor, insert)

# Night Light and progress initialization.
repl('        updateChromeTheme();\n        updateAnnotationButton();\n        hideControls();\n',
     '        updateChromeTheme();\n        updateNightLightOverlay();\n        updateAnnotationButton();\n        hideControls();\n')

# Keep the progress scrubber out of a display cutout / gesture inset.
repl('                if (bottomBar != null) {\n                    FrameLayout.LayoutParams p = (FrameLayout.LayoutParams) bottomBar.getLayoutParams();\n                    int wanted = safeBottom + dp(12);\n                    if (p.bottomMargin != wanted) { p.bottomMargin = wanted; bottomBar.setLayoutParams(p); }\n                }\n                return insets;\n',
     '                if (bottomBar != null) {\n                    FrameLayout.LayoutParams p = (FrameLayout.LayoutParams) bottomBar.getLayoutParams();\n                    int wanted = safeBottom + dp(12);\n                    if (p.bottomMargin != wanted) { p.bottomMargin = wanted; bottomBar.setLayoutParams(p); }\n                }\n                if (readingSeek != null) {\n                    FrameLayout.LayoutParams p = (FrameLayout.LayoutParams) readingSeek.getLayoutParams();\n                    int wanted = safeBottom + dp(64);\n                    if (p.bottomMargin != wanted) { p.bottomMargin = wanted; readingSeek.setLayoutParams(p); }\n                }\n                return insets;\n')

# Update reading scrubber from EPUB state.
old = '''        if ("page".equals(readingMode))\n            positionView.setText("Page " + currentPageInChapter + " / " + pageCountInChapter + " · " + percent + "%");\n        else\n            positionView.setText(chapter + " · " + percent + "%");\n        prefs.edit().putInt("percent_" + bookFile.getName(), percent).apply();\n'''
new = '''        if ("page".equals(readingMode))\n            positionView.setText("Page " + currentPageInChapter + " / " + pageCountInChapter + " · " + percent + "%");\n        else\n            positionView.setText(chapter + " · " + percent + "%");\n        if (readingSeek != null && !readingSeekDragging)\n            readingSeek.setProgress(Math.max(0, Math.min(1000, (int) Math.round(overall * 1000.0))));\n        prefs.edit().putInt("percent_" + bookFile.getName(), percent).apply();\n'''
repl(old, new)

# Update reading scrubber from PDF state.
repl('            positionView.setText(\n                    "Page " + (currentPdfPage + 1) +\n                    " / " + pdfRenderer.getPageCount() +\n                    " · " + percent + "%");\n\n            prefs.edit()\n',
     '            positionView.setText(\n                    "Page " + (currentPdfPage + 1) +\n                    " / " + pdfRenderer.getPageCount() +\n                    " · " + percent + "%");\n            if (readingSeek != null && !readingSeekDragging && pdfRenderer.getPageCount() > 1)\n                readingSeek.setProgress((int) Math.round((currentPdfPage / (double) (pdfRenderer.getPageCount() - 1)) * 1000.0));\n\n            prefs.edit()\n')

# Overall-book scrubbing, including chapter changes for EPUBs.
needle = '    private void searchInBook() {\n'
method = r'''    private void seekToOverallProgress(int permille) {
        int p = Math.max(0, Math.min(1000, permille));
        if (isPdf) {
            if (pdfRenderer == null || pdfRenderer.getPageCount() <= 0) return;
            int target = Math.max(0, Math.min(pdfRenderer.getPageCount() - 1,
                    (int) Math.round((p / 1000.0) * (pdfRenderer.getPageCount() - 1))));
            if (target != currentPdfPage) {
                currentPdfPage = target;
                renderPdfPage();
            }
            return;
        }
        if (spine.isEmpty() || webView == null) return;
        double absolute = (p / 1000.0) * spine.size();
        int targetSpine = Math.min(spine.size() - 1, Math.max(0, (int) Math.floor(absolute)));
        int targetChapterProgress = targetSpine == spine.size() - 1 && p >= 1000
                ? 1000 : Math.max(0, Math.min(1000, (int) Math.round((absolute - targetSpine) * 1000.0)));
        if (targetSpine != currentSpine) {
            int direction = targetSpine > currentSpine ? 1 : -1;
            prepareChapterTransition(direction);
            currentSpine = targetSpine;
            currentProgressPermille = targetChapterProgress;
            saveEpubStateOnly();
            loadCurrentEpubChapter();
            return;
        }
        currentProgressPermille = targetChapterProgress;
        if ("page".equals(readingMode)) {
            try {
                webView.evaluateJavascript(
                        "(function(){var st=window.__wowPageEngine;if(!st||st.mode!=='page')return;" +
                        "st.page=st.clamp(Math.round(((st.count||1)-1)*" + (targetChapterProgress / 1000.0) + "),0,(st.count||1)-1);st.apply(false);st.report();})()",
                        null);
            } catch (Exception ignored) {}
        } else {
            try {
                webView.evaluateJavascript(
                        "(function(){var h=Math.max(0,document.documentElement.scrollHeight-window.innerHeight);window.scrollTo(0,h*" +
                                (targetChapterProgress / 1000.0) + ");})()", null);
            } catch (Exception ignored) {}
        }
        updateEpubProgress(targetChapterProgress);
        saveEpubStateOnly();
    }

'''
repl(needle, method + needle)

# Chrome auto-hide + seek visibility.
old_hide = '''    private void hideControls() {\n        controlsVisible = false;\n'''
new_hide = '''    private void hideControls() {\n        cancelChromeAutoHide();\n        controlsVisible = false;\n'''
repl(old_hide, new_hide)
repl('        if (bottomBar != null && bottomBar.getVisibility() == View.VISIBLE) {\n            bottomBar.animate().cancel();\n            bottomBar.animate().alpha(0f).translationY(dp(14)).setDuration(145L)\n                    .withEndAction(() -> { bottomBar.setVisibility(View.GONE); bottomBar.setAlpha(1f); bottomBar.setTranslationY(0f); }).start();\n        }\n    }\n',
     '        if (bottomBar != null && bottomBar.getVisibility() == View.VISIBLE) {\n            bottomBar.animate().cancel();\n            bottomBar.animate().alpha(0f).translationY(dp(14)).setDuration(145L)\n                    .withEndAction(() -> { bottomBar.setVisibility(View.GONE); bottomBar.setAlpha(1f); bottomBar.setTranslationY(0f); }).start();\n        }\n        if (readingSeek != null && readingSeek.getVisibility() == View.VISIBLE) {\n            readingSeek.animate().cancel();\n            readingSeek.animate().alpha(0f).translationY(dp(8)).setDuration(130L)\n                    .withEndAction(() -> { readingSeek.setVisibility(View.GONE); readingSeek.setAlpha(1f); readingSeek.setTranslationY(0f); }).start();\n        }\n    }\n')
repl('        if (bottomBar != null) {\n            bottomBar.animate().cancel();\n            bottomBar.setVisibility(View.VISIBLE);\n            bottomBar.setAlpha(0f);\n            bottomBar.setTranslationY(dp(10));\n            bottomBar.animate().alpha(1f).translationY(0f).setDuration(175L).start();\n        }\n        enterImmersive();\n    }\n',
     '        if (bottomBar != null) {\n            bottomBar.animate().cancel();\n            bottomBar.setVisibility(View.VISIBLE);\n            bottomBar.setAlpha(0f);\n            bottomBar.setTranslationY(dp(10));\n            bottomBar.animate().alpha(1f).translationY(0f).setDuration(175L).start();\n        }\n        if (readingSeek != null) {\n            readingSeek.animate().cancel();\n            readingSeek.setVisibility(View.VISIBLE);\n            readingSeek.setAlpha(0f);\n            readingSeek.setTranslationY(dp(7));\n            readingSeek.animate().alpha(1f).translationY(0f).setDuration(190L).start();\n        }\n        scheduleChromeAutoHide();\n        enterImmersive();\n    }\n')

# Auto-hide and Night Light helpers.
needle = '    private void toggleControls() {\n'
helpers = r'''    private void cancelChromeAutoHide() {
        if (root != null && chromeAutoHideRunnable != null) root.removeCallbacks(chromeAutoHideRunnable);
        chromeAutoHideRunnable = null;
    }

    private void scheduleChromeAutoHide() {
        cancelChromeAutoHide();
        if (!controlsVisible || root == null || readingSeekDragging) return;
        chromeAutoHideRunnable = () -> {
            chromeAutoHideRunnable = null;
            if (controlsVisible && !readingSeekDragging && currentSelection == null) hideControls();
        };
        root.postDelayed(chromeAutoHideRunnable, 4200L);
    }

    private void updateNightLightOverlay() {
        if (nightLightOverlay == null) return;
        boolean active = "on".equals(nightLightMode);
        if ("auto".equals(nightLightMode)) {
            int hour = Calendar.getInstance().get(Calendar.HOUR_OF_DAY);
            active = hour >= 19 || hour < 6;
        }
        if (readerTheme == 2) active = false;
        nightLightOverlay.animate().cancel();
        nightLightOverlay.animate().alpha(active ? 0.095f : 0f).setDuration(240L).start();
    }

'''
repl(needle, helpers + needle)

# Theme changes also refresh Night Light.
repl('        if (root != null) root.setBackgroundColor(solid);\n        if (webView != null) webView.setBackgroundColor(solid);\n    }\n',
     '        if (root != null) root.setBackgroundColor(solid);\n        if (webView != null) webView.setBackgroundColor(solid);\n        updateNightLightOverlay();\n    }\n')

# Resume refreshes auto Night Light schedule.
repl('        applyWindowPreferences();\n        getWindow().getDecorView().postDelayed(this::enterImmersive, 80L);\n',
     '        applyWindowPreferences();\n        updateNightLightOverlay();\n        getWindow().getDecorView().postDelayed(this::enterImmersive, 80L);\n')

# Persist Night Light with the rest of reader settings.
repl('                .putInt("reader_brightness", brightnessPercent)\n',
     '                .putInt("reader_brightness", brightnessPercent)\n                .putString("reader_night_light", nightLightMode)\n')

# Rename old list-style settings to Advanced, then insert a unified display-options sheet.
repl('    private void showReaderSettings() {\n', '    private void showAdvancedReaderSettings() {\n', 1)
needle = '    private void showAdvancedReaderSettings() {\n'
new_sheet = r'''    private void showReaderSettings() {
        if (isPdf) {
            showPdfSettings();
            return;
        }
        final Dialog dialog = new Dialog(this);
        dialog.requestWindowFeature(Window.FEATURE_NO_TITLE);
        dialog.setCanceledOnTouchOutside(true);

        int panel = readerTheme == 2 ? Color.rgb(28, 29, 32) :
                readerTheme == 1 ? Color.rgb(249, 243, 226) : Color.rgb(250, 250, 252);
        int text = readerTheme == 2 ? Color.rgb(241, 243, 247) : Color.rgb(35, 37, 43);
        int sub = readerTheme == 2 ? Color.rgb(184, 188, 196) : Color.rgb(103, 108, 119);

        ScrollView scroll = new ScrollView(this);
        scroll.setVerticalScrollBarEnabled(false);
        LinearLayout card = new LinearLayout(this);
        card.setOrientation(LinearLayout.VERTICAL);
        card.setPadding(dp(18), dp(14), dp(18), dp(20));
        card.setBackground(glassPanel(Color.argb(248, Color.red(panel), Color.green(panel), Color.blue(panel)),
                dp(26), Color.argb(readerTheme == 2 ? 55 : 72, 150, 155, 168)));
        scroll.addView(card, new ScrollView.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT));

        LinearLayout header = new LinearLayout(this);
        header.setOrientation(LinearLayout.HORIZONTAL);
        header.setGravity(Gravity.CENTER_VERTICAL);
        TextView title = new TextView(this);
        title.setText("Display options");
        title.setTextSize(22);
        title.setTypeface(android.graphics.Typeface.DEFAULT, android.graphics.Typeface.BOLD);
        title.setTextColor(text);
        header.addView(title, new LinearLayout.LayoutParams(0, dp(48), 1f));
        TextView close = sheetChip("×", false);
        close.setTextSize(24);
        close.setOnClickListener(v -> dialog.dismiss());
        header.addView(close, new LinearLayout.LayoutParams(dp(48), dp(42)));
        card.addView(header);

        addSheetLabel(card, "Theme", sub);
        LinearLayout themeRow = sheetRow();
        TextView[] themeChips = {sheetChip("Light", readerTheme == 0), sheetChip("Sepia", readerTheme == 1), sheetChip("Dark", readerTheme == 2)};
        for (int i = 0; i < themeChips.length; i++) {
            final int value = i;
            themeChips[i].setOnClickListener(v -> {
                readerTheme = value;
                saveReaderPreferences();
                applyReaderStyle(true);
                updateChromeTheme();
                selectSheetChip(themeChips, value);
            });
            themeRow.addView(themeChips[i], sheetChipLp(i > 0));
        }
        card.addView(themeRow);

        addSheetLabel(card, "Night Light", sub);
        LinearLayout nightRow = sheetRow();
        String[] nightLabels = {"Off", "Auto", "On"};
        String[] nightValues = {"off", "auto", "on"};
        TextView[] nightChips = new TextView[3];
        for (int i = 0; i < 3; i++) {
            nightChips[i] = sheetChip(nightLabels[i], nightValues[i].equals(nightLightMode));
            final int idx = i;
            nightChips[i].setOnClickListener(v -> {
                nightLightMode = nightValues[idx];
                saveReaderPreferences();
                updateNightLightOverlay();
                selectSheetChip(nightChips, idx);
            });
            nightRow.addView(nightChips[i], sheetChipLp(i > 0));
        }
        card.addView(nightRow);

        addSheetLabel(card, "Text", sub);
        LinearLayout fontSizeRow = sheetRow();
        TextView minusFont = sheetChip("A−", false);
        TextView fontValue = sheetChip(fontPercent + "%", true);
        TextView plusFont = sheetChip("A+", false);
        minusFont.setOnClickListener(v -> { fontPercent = Math.max(80, fontPercent - 10); fontValue.setText(fontPercent + "%"); saveReaderPreferences(); applyReaderStyle(true); });
        plusFont.setOnClickListener(v -> { fontPercent = Math.min(200, fontPercent + 10); fontValue.setText(fontPercent + "%"); saveReaderPreferences(); applyReaderStyle(true); });
        fontSizeRow.addView(minusFont, sheetChipLp(false));
        fontSizeRow.addView(fontValue, sheetChipLp(true));
        fontSizeRow.addView(plusFont, sheetChipLp(true));
        TextView fontPick = sheetChip("Font · " + fontDisplayName(), false);
        fontPick.setOnClickListener(v -> { dialog.dismiss(); showFontDialog(); });
        fontSizeRow.addView(fontPick, sheetChipLp(true));
        card.addView(fontSizeRow);

        addSheetLabel(card, "Line height", sub);
        LinearLayout lineRow = sheetRow();
        TextView lineMinus = sheetChip("−", false);
        TextView lineValue = sheetChip(lineSpacingDisplay(), true);
        TextView linePlus = sheetChip("+", false);
        lineMinus.setOnClickListener(v -> { lineSpacing = Math.max(120, lineSpacing - 10); lineValue.setText(lineSpacingDisplay()); saveReaderPreferences(); applyReaderStyle(true); });
        linePlus.setOnClickListener(v -> { lineSpacing = Math.min(220, lineSpacing + 10); lineValue.setText(lineSpacingDisplay()); saveReaderPreferences(); applyReaderStyle(true); });
        lineRow.addView(lineMinus, sheetChipLp(false));
        lineRow.addView(lineValue, sheetChipLp(true));
        lineRow.addView(linePlus, sheetChipLp(true));
        card.addView(lineRow);

        addSheetLabel(card, "Alignment", sub);
        LinearLayout alignRow = sheetRow();
        String[] alignLabels = {"Justify", "Left", "Right"};
        String[] alignValues = {"justify", "left", "right"};
        TextView[] alignChips = new TextView[3];
        for (int i = 0; i < 3; i++) {
            alignChips[i] = sheetChip(alignLabels[i], alignValues[i].equals(textAlignment));
            final int idx = i;
            alignChips[i].setOnClickListener(v -> { textAlignment = alignValues[idx]; saveReaderPreferences(); applyReaderStyle(true); selectSheetChip(alignChips, idx); });
            alignRow.addView(alignChips[i], sheetChipLp(i > 0));
        }
        card.addView(alignRow);

        addSheetLabel(card, "Margins", sub);
        LinearLayout marginRow = sheetRow();
        String[] marginLabels = {"Narrow", "Normal", "Wide"};
        int[] marginValues = {4, 7, 11};
        int marginSelected = marginPercent <= 5 ? 0 : (marginPercent >= 9 ? 2 : 1);
        TextView[] marginChips = new TextView[3];
        for (int i = 0; i < 3; i++) {
            marginChips[i] = sheetChip(marginLabels[i], i == marginSelected);
            final int idx = i;
            marginChips[i].setOnClickListener(v -> { marginPercent = marginValues[idx]; saveReaderPreferences(); applyReaderStyle(true); selectSheetChip(marginChips, idx); });
            marginRow.addView(marginChips[i], sheetChipLp(i > 0));
        }
        card.addView(marginRow);

        addSheetLabel(card, "Reading", sub);
        LinearLayout modeRow = sheetRow();
        TextView[] modeChips = {sheetChip("Pages", "page".equals(readingMode)), sheetChip("Scroll", "scroll".equals(readingMode))};
        for (int i = 0; i < 2; i++) {
            final int idx = i;
            modeChips[i].setOnClickListener(v -> { readingMode = idx == 0 ? "page" : "scroll"; pageTurnLocked = false; saveReaderPreferences(); applyReaderStyle(true); selectSheetChip(modeChips, idx); });
            modeRow.addView(modeChips[i], sheetChipLp(i > 0));
        }
        card.addView(modeRow);

        addSheetLabel(card, "Page animation", sub);
        LinearLayout animRow = sheetRow();
        String[] animLabels = {"None", "3D", "Slide"};
        String[] animValues = {"none", "paper", "slide"};
        TextView[] animChips = new TextView[3];
        for (int i = 0; i < 3; i++) {
            animChips[i] = sheetChip(animLabels[i], animValues[i].equals(pageAnimation));
            final int idx = i;
            animChips[i].setOnClickListener(v -> { pageAnimation = animValues[idx]; saveReaderPreferences(); selectSheetChip(animChips, idx); });
            animRow.addView(animChips[i], sheetChipLp(i > 0));
        }
        card.addView(animRow);

        addSheetLabel(card, "Reading brightness", sub);
        LinearLayout brightRow = sheetRow();
        TextView brightValue = new TextView(this);
        brightValue.setText(brightnessPercent < 0 ? "System" : brightnessPercent + "%");
        brightValue.setTextSize(13);
        brightValue.setTextColor(text);
        brightValue.setGravity(Gravity.CENTER_VERTICAL);
        SeekBar brightSeek = new SeekBar(this);
        brightSeek.setMax(101);
        brightSeek.setProgress(brightnessPercent < 0 ? 0 : Math.max(1, Math.min(101, brightnessPercent + 1)));
        brightSeek.setOnSeekBarChangeListener(new SeekBar.OnSeekBarChangeListener() {
            @Override public void onProgressChanged(SeekBar seekBar, int progress, boolean fromUser) {
                if (!fromUser) return;
                brightnessPercent = progress == 0 ? -1 : progress - 1;
                brightValue.setText(brightnessPercent < 0 ? "System" : brightnessPercent + "%");
                saveReaderPreferences();
                applyWindowPreferences();
            }
            @Override public void onStartTrackingTouch(SeekBar seekBar) {}
            @Override public void onStopTrackingTouch(SeekBar seekBar) {}
        });
        brightRow.addView(brightSeek, new LinearLayout.LayoutParams(0, dp(44), 1f));
        brightRow.addView(brightValue, new LinearLayout.LayoutParams(dp(66), dp(44)));
        card.addView(brightRow);

        TextView more = sheetChip("More reader settings", false);
        more.setGravity(Gravity.CENTER);
        more.setOnClickListener(v -> { dialog.dismiss(); showAdvancedReaderSettings(); });
        LinearLayout.LayoutParams moreLp = new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, dp(48));
        moreLp.topMargin = dp(14);
        card.addView(more, moreLp);

        dialog.setContentView(scroll);
        dialog.show();
        Window w = dialog.getWindow();
        if (w != null) {
            w.setBackgroundDrawable(new ColorDrawable(Color.TRANSPARENT));
            w.addFlags(WindowManager.LayoutParams.FLAG_DIM_BEHIND);
            w.setDimAmount(0.20f);
            w.setGravity(Gravity.BOTTOM);
            int sw = getResources().getDisplayMetrics().widthPixels;
            int sh = getResources().getDisplayMetrics().heightPixels;
            w.setLayout(Math.min(sw, dp(620)), Math.min((int) (sh * 0.84f), dp(760)));
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
                w.addFlags(WindowManager.LayoutParams.FLAG_BLUR_BEHIND);
                w.setBackgroundBlurRadius(dp(20));
            }
        }
    }

    private void addSheetLabel(LinearLayout parent, String label, int color) {
        TextView v = new TextView(this);
        v.setText(label);
        v.setTextSize(12.5f);
        v.setTypeface(android.graphics.Typeface.DEFAULT, android.graphics.Typeface.BOLD);
        v.setTextColor(color);
        v.setPadding(dp(3), dp(12), dp(3), dp(6));
        parent.addView(v, new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT));
    }

    private LinearLayout sheetRow() {
        LinearLayout row = new LinearLayout(this);
        row.setOrientation(LinearLayout.HORIZONTAL);
        row.setGravity(Gravity.CENTER_VERTICAL);
        return row;
    }

    private LinearLayout.LayoutParams sheetChipLp(boolean spaced) {
        LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(0, dp(42), 1f);
        if (spaced) lp.leftMargin = dp(7);
        return lp;
    }

    private TextView sheetChip(String label, boolean selected) {
        TextView v = new TextView(this);
        v.setText(label);
        v.setTextSize(12.5f);
        v.setTypeface(android.graphics.Typeface.DEFAULT, android.graphics.Typeface.BOLD);
        v.setGravity(Gravity.CENTER);
        v.setClickable(true);
        styleSheetChip(v, selected);
        v.setOnTouchListener((view, event) -> {
            if (event.getActionMasked() == MotionEvent.ACTION_DOWN)
                view.animate().scaleX(0.97f).scaleY(0.97f).setDuration(55L).start();
            else if (event.getActionMasked() == MotionEvent.ACTION_UP || event.getActionMasked() == MotionEvent.ACTION_CANCEL)
                view.animate().scaleX(1f).scaleY(1f).setDuration(110L).start();
            return false;
        });
        return v;
    }

    private void styleSheetChip(TextView v, boolean selected) {
        int bg;
        int fg;
        int stroke;
        if (readerTheme == 2) {
            bg = selected ? Color.rgb(77, 88, 125) : Color.rgb(43, 45, 50);
            fg = Color.rgb(238, 241, 247);
            stroke = selected ? Color.rgb(145, 166, 235) : Color.rgb(70, 73, 80);
        } else {
            bg = selected ? Color.rgb(225, 230, 255) : Color.rgb(255, 255, 255);
            fg = selected ? Color.rgb(57, 65, 145) : Color.rgb(55, 58, 66);
            stroke = selected ? Color.rgb(151, 161, 225) : Color.rgb(220, 222, 228);
        }
        v.setTextColor(fg);
        v.setBackground(glassPanel(bg, dp(15), stroke));
    }

    private void selectSheetChip(TextView[] chips, int selected) {
        if (chips == null) return;
        for (int i = 0; i < chips.length; i++) if (chips[i] != null) styleSheetChip(chips[i], i == selected);
    }

'''
repl(needle, new_sheet + needle)

# When old advanced settings loops back after a toggle, show the modern sheet.
# No further replacement is required; its existing calls to showReaderSettings() now do this.

# Reset includes Night Light off.
repl('        brightnessPercent = -1;\n        keepScreenOn = false;\n',
     '        brightnessPercent = -1;\n        nightLightMode = "off";\n        keepScreenOn = false;\n')

# Cancel timers on destroy.
repl('    protected void onDestroy() {\n        pendingChapterCurlDirection = 0;\n',
     '    protected void onDestroy() {\n        cancelChromeAutoHide();\n        pendingChapterCurlDirection = 0;\n')

P.write_text(s, encoding='utf-8')

# Smooth large libraries a little more by keeping more bound cards warm.
M = Path('app/src/main/java/com/whisper/wowreader/MainActivity.java')
m = M.read_text(encoding='utf-8')
m = m.replace('        libraryRecycler.setItemViewCacheSize(12);\n',
              '        libraryRecycler.setItemViewCacheSize(20);\n        libraryRecycler.setHasFixedSize(false);\n')
M.write_text(m, encoding='utf-8')

B = Path('app/build.gradle')
b = B.read_text(encoding='utf-8')
b = b.replace('versionCode 22', 'versionCode 23')
b = b.replace("versionName '2.10.0'", "versionName '2.11.0'")
B.write_text(b, encoding='utf-8')

print('Applied WoW Reader v2.11.0 Play Books UX polish')
