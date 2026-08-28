from pathlib import Path

ROOT = Path('.')
reader_path = ROOT / 'app/src/main/java/com/whisper/wowreader/BookReaderActivity.java'
main_path = ROOT / 'app/src/main/java/com/whisper/wowreader/MainActivity.java'
reader = reader_path.read_text(encoding='utf-8')
main = main_path.read_text(encoding='utf-8')


def replace_once(text, old, new, label):
    if old not in text:
        raise SystemExit(f'missing anchor: {label}')
    return text.replace(old, new, 1)

# Google account UI remains deferred for now. Keep the underlying experimental source dormant,
# but do not initialize it, auto-sync, or expose an account button in this release.
main = replace_once(main,
'''        googleDrive = new GoogleDriveSync(this);\n        restoreStoredGoogleProfile();\n''',
'''        // Google account / Drive sync is intentionally deferred for a later release.\n''',
'google init')
main = replace_once(main,
'''        if (libraryRecycler != null) refreshLibrary();\n        maybeAutoGoogleSync();\n''',
'''        if (libraryRecycler != null) refreshLibrary();\n''',
'google auto sync')
main = replace_once(main,
'''        accountButton = iconButton("G");\n        accountButton.setTextSize(15);\n        accountButton.setTypeface(Typeface.DEFAULT, Typeface.BOLD);\n        accountButton.setContentDescription("Google account and sync");\n        accountButton.setOnClickListener(v -> showAccountMenu());\n        updateAccountButton();\n        brandRow.addView(accountButton, new LinearLayout.LayoutParams(dp(44), dp(44)));\n\n''',
'',
'google account button')

# Initial reader loading surface.
reader = replace_once(reader,
'''    private boolean controlsVisible = false;\n\n    private WebView webView;\n''',
'''    private boolean controlsVisible = false;\n    private FrameLayout readerLoadingOverlay;\n\n    private WebView webView;\n''',
'loading field')

reader = replace_once(reader,
'''        if (isPdf) setupPdfView(content); else setupWebView(content);\n\n        nightLightOverlay = new View(this);\n''',
'''        if (isPdf) setupPdfView(content); else setupWebView(content);\n\n        if (!isPdf) {\n            readerLoadingOverlay = new FrameLayout(this);\n            readerLoadingOverlay.setClickable(true);\n            int loadingBg = readerTheme == 2 ? Color.rgb(18, 18, 18) :\n                    (readerTheme == 1 ? Color.rgb(244, 236, 216) : Color.rgb(250, 250, 252));\n            readerLoadingOverlay.setBackgroundColor(loadingBg);\n\n            LinearLayout loadingCard = new LinearLayout(this);\n            loadingCard.setOrientation(LinearLayout.VERTICAL);\n            loadingCard.setGravity(Gravity.CENTER);\n            loadingCard.setPadding(dp(24), dp(20), dp(24), dp(20));\n\n            ImageView loadingLogo = new ImageView(this);\n            loadingLogo.setImageResource(R.drawable.wow_logo);\n            loadingLogo.setScaleType(ImageView.ScaleType.CENTER_INSIDE);\n            loadingLogo.setAlpha(0.96f);\n            loadingCard.addView(loadingLogo, new LinearLayout.LayoutParams(dp(72), dp(72)));\n\n            TextView loadingTitle = new TextView(this);\n            loadingTitle.setText("Opening book…");\n            loadingTitle.setTextSize(16);\n            loadingTitle.setTypeface(android.graphics.Typeface.DEFAULT, android.graphics.Typeface.BOLD);\n            loadingTitle.setTextColor(readerTheme == 2 ? Color.rgb(235, 237, 241) : Color.rgb(52, 54, 61));\n            loadingTitle.setGravity(Gravity.CENTER);\n            LinearLayout.LayoutParams loadingTitleLp = new LinearLayout.LayoutParams(\n                    ViewGroup.LayoutParams.WRAP_CONTENT, ViewGroup.LayoutParams.WRAP_CONTENT);\n            loadingTitleLp.topMargin = dp(12);\n            loadingCard.addView(loadingTitle, loadingTitleLp);\n\n            TextView loadingSub = new TextView(this);\n            loadingSub.setText("Preparing your reading page");\n            loadingSub.setTextSize(12.5f);\n            loadingSub.setTextColor(readerTheme == 2 ? Color.rgb(168, 172, 181) : Color.rgb(112, 116, 126));\n            loadingSub.setGravity(Gravity.CENTER);\n            LinearLayout.LayoutParams loadingSubLp = new LinearLayout.LayoutParams(\n                    ViewGroup.LayoutParams.WRAP_CONTENT, ViewGroup.LayoutParams.WRAP_CONTENT);\n            loadingSubLp.topMargin = dp(5);\n            loadingCard.addView(loadingSub, loadingSubLp);\n\n            FrameLayout.LayoutParams loadingCardLp = new FrameLayout.LayoutParams(\n                    ViewGroup.LayoutParams.WRAP_CONTENT, ViewGroup.LayoutParams.WRAP_CONTENT, Gravity.CENTER);\n            readerLoadingOverlay.addView(loadingCard, loadingCardLp);\n            root.addView(readerLoadingOverlay, new FrameLayout.LayoutParams(\n                    ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.MATCH_PARENT));\n            loadingCard.setScaleX(0.97f);\n            loadingCard.setScaleY(0.97f);\n            loadingCard.setAlpha(0f);\n            loadingCard.animate().alpha(1f).scaleX(1f).scaleY(1f).setDuration(220L)\n                    .setInterpolator(new android.view.animation.DecelerateInterpolator(1.35f)).start();\n        }\n\n        nightLightOverlay = new View(this);\n''',
'loading overlay')

reader = replace_once(reader,
'''    private TextView iconButton(String text, int size) {\n''',
'''    private void hideInitialReaderLoading() {\n        if (readerLoadingOverlay == null || readerLoadingOverlay.getVisibility() != View.VISIBLE) return;\n        readerLoadingOverlay.animate().cancel();\n        readerLoadingOverlay.animate().alpha(0f).setDuration(160L)\n                .setInterpolator(new android.view.animation.DecelerateInterpolator())\n                .withEndAction(() -> {\n                    if (readerLoadingOverlay != null) {\n                        readerLoadingOverlay.setVisibility(View.GONE);\n                        readerLoadingOverlay.setAlpha(1f);\n                    }\n                }).start();\n    }\n\n    private TextView iconButton(String text, int size) {\n''',
'loading hide helper')

reader = replace_once(reader,
'''                    chapterLoading = false;\n                    Toast.makeText(this, "EPUB error: " + e.getMessage(), Toast.LENGTH_LONG).show();\n                    positionView.setText("Unable to open EPUB");\n''',
'''                    chapterLoading = false;\n                    hideInitialReaderLoading();\n                    Toast.makeText(this, "EPUB error: " + e.getMessage(), Toast.LENGTH_LONG).show();\n                    positionView.setText("Unable to open EPUB");\n''',
'epub error loading')
reader = replace_once(reader,
'''                    if (spine.isEmpty()) {\n                        chapterLoading = false;\n                        Toast.makeText(this, "This EPUB has no readable chapters", Toast.LENGTH_LONG).show();\n''',
'''                    if (spine.isEmpty()) {\n                        chapterLoading = false;\n                        hideInitialReaderLoading();\n                        Toast.makeText(this, "This EPUB has no readable chapters", Toast.LENGTH_LONG).show();\n''',
'empty epub loading')

reader = replace_once(reader,
'''    private void revealStableChapter() {\n        if (webView != null) {\n            webView.animate().cancel();\n            webView.setAlpha(1f);\n        }\n        pageTurnLocked = false;\n''',
'''    private void revealStableChapter() {\n        if (webView != null) {\n            webView.animate().cancel();\n            webView.animate().alpha(1f).setDuration(135L)\n                    .setInterpolator(new android.view.animation.DecelerateInterpolator()).start();\n        }\n        hideInitialReaderLoading();\n        pageTurnLocked = false;\n''',
'stable reveal')

# Make line height authoritative over publisher paragraph/span line-height rules.
reader = replace_once(reader,
'''                ".wow-reader-block{letter-spacing:normal !important;}" +\n''',
'''                ".wow-reader-block{line-height:" + line + " !important;letter-spacing:normal !important;}" +\n                ".wow-reader-block *{line-height:inherit !important;}" +\n''',
'line height css')

# Remove the 3D page curl choice from user-facing animation settings and migrate any old paper setting to None.
reader = replace_once(reader,
'''        pageAnimation = prefs.getString("epub_page_animation", "none");\n        if (!"paper".equals(pageAnimation) && !"slide".equals(pageAnimation) && !"none".equals(pageAnimation))\n            pageAnimation = "none";\n''',
'''        pageAnimation = prefs.getString("epub_page_animation", "none");\n        if ("paper".equals(pageAnimation)) {\n            pageAnimation = "none";\n            prefs.edit().putString("epub_page_animation", "none").apply();\n        }\n        if (!"slide".equals(pageAnimation) && !"none".equals(pageAnimation))\n            pageAnimation = "none";\n''',
'animation migration')

reader = replace_once(reader,
'''        String[] animLabels = {"None", "3D", "Slide"};\n        String[] animValues = {"none", "paper", "slide"};\n        TextView[] animChips = new TextView[3];\n        for (int i = 0; i < 3; i++) {\n''',
'''        String[] animLabels = {"None", "Slide"};\n        String[] animValues = {"none", "slide"};\n        TextView[] animChips = new TextView[2];\n        for (int i = 0; i < 2; i++) {\n''',
'animation sheet')

reader = replace_once(reader,
'''    private void showPageAnimationDialog() {\n        String[] labels = {"None · default", "3D page curl", "Smooth slide"};\n        String[] values = {"none", "paper", "slide"};\n        int selected = "paper".equals(pageAnimation) ? 1 : ("slide".equals(pageAnimation) ? 2 : 0);\n''',
'''    private void showPageAnimationDialog() {\n        String[] labels = {"None · default", "Smooth slide"};\n        String[] values = {"none", "slide"};\n        int selected = "slide".equals(pageAnimation) ? 1 : 0;\n''',
'animation dialog')

reader = replace_once(reader,
'''    private String pageAnimationDisplayName() {\n        if ("slide".equals(pageAnimation)) return "Slide";\n        if ("none".equals(pageAnimation)) return "None";\n        return "3D page curl";\n    }\n''',
'''    private String pageAnimationDisplayName() {\n        return "slide".equals(pageAnimation) ? "Slide" : "None";\n    }\n''',
'animation display name')

reader_path.write_text(reader, encoding='utf-8')
main_path.write_text(main, encoding='utf-8')
print('Applied v2.12 reader polish: deferred Google UI, loading surface, line height fix, removed 3D option')
