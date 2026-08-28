from pathlib import Path

MAIN = Path('app/src/main/java/com/whisper/wowreader/MainActivity.java')
READER = Path('app/src/main/java/com/whisper/wowreader/BookReaderActivity.java')
CURL = Path('app/src/main/java/com/whisper/wowreader/PageCurlView.java')
GRADLE = Path('app/build.gradle')


def replace_once(text, old, new, label):
    if old not in text:
        raise SystemExit(f'missing anchor: {label}')
    return text.replace(old, new, 1)

# ---------- Home / Explore / FAB ----------
main = MAIN.read_text(encoding='utf-8')
main = replace_once(main,
    'import android.graphics.Paint;\nimport android.graphics.Typeface;',
    'import android.graphics.Paint;\nimport android.graphics.Path;\nimport android.graphics.Typeface;',
    'Path import')

old_fab = '''        floatingAdd = new TextView(this);\n        floatingAdd.setText("＋");\n        floatingAdd.setTextSize(30);\n        floatingAdd.setTextColor(Color.WHITE);\n        floatingAdd.setGravity(Gravity.CENTER);\n        floatingAdd.setContentDescription("Add book");\n        floatingAdd.setBackground(roundRect(Color.rgb(82, 82, 214), dp(28), 0, 0));\n        floatingAdd.setElevation(dp(10));\n        floatingAdd.setOnClickListener(v -> chooseBook());\n        FrameLayout.LayoutParams fabLp = new FrameLayout.LayoutParams(dp(58), dp(58), Gravity.END | Gravity.BOTTOM);\n        fabLp.rightMargin = dp(18);\n        fabLp.bottomMargin = dp(22);\n        root.addView(floatingAdd, fabLp);'''
new_fab = '''        floatingAdd = new TextView(this);\n        floatingAdd.setText("＋  Add book");\n        floatingAdd.setTextSize(14.5f);\n        floatingAdd.setTypeface(Typeface.DEFAULT, Typeface.BOLD);\n        floatingAdd.setTextColor(Color.WHITE);\n        floatingAdd.setGravity(Gravity.CENTER);\n        floatingAdd.setPadding(dp(14), 0, dp(16), 0);\n        floatingAdd.setContentDescription("Add book");\n        floatingAdd.setBackground(gradientRoundRect(new int[]{\n                Color.rgb(92, 76, 226), Color.rgb(71, 113, 236)}, dp(29)));\n        floatingAdd.setElevation(dp(11));\n        floatingAdd.setOnClickListener(v -> {\n            try { v.performHapticFeedback(android.view.HapticFeedbackConstants.KEYBOARD_TAP); } catch (Exception ignored) {}\n            chooseBook();\n        });\n        floatingAdd.setOnTouchListener((v, e) -> {\n            int action = e.getActionMasked();\n            if (action == android.view.MotionEvent.ACTION_DOWN) {\n                v.animate().cancel();\n                v.animate().scaleX(0.955f).scaleY(0.955f).translationY(dp(1)).setDuration(72L).start();\n                v.setElevation(dp(7));\n            } else if (action == android.view.MotionEvent.ACTION_UP || action == android.view.MotionEvent.ACTION_CANCEL) {\n                v.animate().cancel();\n                v.animate().scaleX(1f).scaleY(1f).translationY(0f).setDuration(185L)\n                        .setInterpolator(new android.view.animation.OvershootInterpolator(1.18f)).start();\n                v.setElevation(dp(11));\n            }\n            return false;\n        });\n        FrameLayout.LayoutParams fabLp = new FrameLayout.LayoutParams(dp(124), dp(58), Gravity.END | Gravity.BOTTOM);\n        fabLp.rightMargin = dp(16);\n        fabLp.bottomMargin = dp(20);\n        root.addView(floatingAdd, fabLp);'''
main = replace_once(main, old_fab, new_fab, 'FAB')

old_scroll = '''                if (dy > dp(2) && recyclerView.canScrollVertically(-1)) {\n                    floatingAdd.animate().translationY(dp(86)).alpha(0.16f).setDuration(180L).start();\n                } else if (dy < -dp(2) || !recyclerView.canScrollVertically(-1)) {\n                    floatingAdd.animate().translationY(0f).alpha(1f).setDuration(180L).start();\n                }'''
new_scroll = '''                floatingAdd.animate().cancel();\n                if (dy > dp(2) && recyclerView.canScrollVertically(-1)) {\n                    floatingAdd.animate().translationY(dp(88)).alpha(0f).setDuration(165L)\n                            .setInterpolator(new android.view.animation.DecelerateInterpolator()).start();\n                } else if (dy < -dp(2) || !recyclerView.canScrollVertically(-1)) {\n                    floatingAdd.animate().translationY(0f).alpha(1f).setDuration(210L)\n                            .setInterpolator(new android.view.animation.DecelerateInterpolator(1.35f)).start();\n                }'''
main = replace_once(main, old_scroll, new_scroll, 'FAB scroll motion')

old_data = '''        String[][] data = {\n                {"T", "Telegram", "New books", "https://t.me/TheBookR"},\n                {"D", "Discussion", "Reader community", "https://t.me/+rUiqzi2mdhNiNGZl"},\n                {"W", "Book Website", "saroatsin.com", "https://saroatsin.com"},\n                {"R", "Book Reviews", "အညွှန်း & review", "https://whispermmepub.github.io/Review/"}\n        };'''
new_data = '''        String[][] data = {\n                {"telegram", "Telegram", "New books", "https://t.me/TheBookR"},\n                {"discussion", "Discussion", "Reader community", "https://t.me/+rUiqzi2mdhNiNGZl"},\n                {"website", "Book Website", "saroatsin.com", "https://saroatsin.com"},\n                {"review", "Book Reviews", "အညွှန်း & review", "https://whispermmepub.github.io/Review/"}\n        };'''
main = replace_once(main, old_data, new_data, 'explore data')

main = replace_once(main,
    '    private View discoveryCard(String letter, String title, String subtitle, int background, String url) {',
    '    private View discoveryCard(String kind, String title, String subtitle, int background, String url) {',
    'discovery signature')

old_badge = '''        TextView badge = new TextView(this);\n        badge.setText(letter);\n        badge.setTextSize(14);\n        badge.setTypeface(Typeface.DEFAULT, Typeface.BOLD);\n        badge.setTextColor(Color.rgb(55, 60, 72));\n        badge.setGravity(Gravity.CENTER);\n        badge.setBackground(roundRect(Color.argb(185, 255, 255, 255), dp(18), 0, 0));\n        card.addView(badge, new LinearLayout.LayoutParams(dp(38), dp(38)));'''
new_badge = '''        ExploreLogoView badge = new ExploreLogoView(this, kind);\n        card.addView(badge, new LinearLayout.LayoutParams(dp(42), dp(42)));'''
main = replace_once(main, old_badge, new_badge, 'explore badge')

# Give list cards the same responsive press feedback as grid cards.
old_list_click = '''        card.setElevation(dp(1));\n        card.setOnClickListener(v -> openBook(file));\n        card.setOnLongClickListener(v -> { confirmDelete(file); return true; });\n\n        ImageView cover = new ImageView(this);'''
new_list_click = '''        card.setElevation(dp(1));\n        card.setOnClickListener(v -> openBook(file));\n        card.setOnLongClickListener(v -> { confirmDelete(file); return true; });\n        card.setOnTouchListener((v, e) -> {\n            int action = e.getActionMasked();\n            if (action == android.view.MotionEvent.ACTION_DOWN) {\n                v.animate().cancel();\n                v.animate().scaleX(0.986f).scaleY(0.986f).setDuration(65L).start();\n            } else if (action == android.view.MotionEvent.ACTION_UP || action == android.view.MotionEvent.ACTION_CANCEL) {\n                v.animate().cancel();\n                v.animate().scaleX(1f).scaleY(1f).setDuration(145L)\n                        .setInterpolator(new android.view.animation.DecelerateInterpolator()).start();\n            }\n            return false;\n        });\n\n        ImageView cover = new ImageView(this);'''
main = replace_once(main, old_list_click, new_list_click, 'list card motion')

# Insert a tiny vector-like logo view; no network image loading and no extra runtime cost.
insert_before = '    private int dp(int v){return Math.round(v*getResources().getDisplayMetrics().density);}\n}'
logo_class = r'''    private final class ExploreLogoView extends View {
        private final String kind;
        private final Paint p = new Paint(Paint.ANTI_ALIAS_FLAG);
        private final Paint stroke = new Paint(Paint.ANTI_ALIAS_FLAG);
        private final Path path = new Path();

        ExploreLogoView(android.content.Context context, String kind) {
            super(context);
            this.kind = kind == null ? "website" : kind;
            setLayerType(View.LAYER_TYPE_HARDWARE, null);
            stroke.setStyle(Paint.Style.STROKE);
            stroke.setStrokeCap(Paint.Cap.ROUND);
            stroke.setStrokeJoin(Paint.Join.ROUND);
        }

        @Override protected void onDraw(Canvas c) {
            super.onDraw(c);
            float w = getWidth(), h = getHeight();
            float cx = w * .5f, cy = h * .5f, r = Math.min(w, h) * .47f;
            if ("telegram".equals(kind) || "discussion".equals(kind)) drawTelegram(c, cx, cy, r);
            else if ("review".equals(kind)) drawReview(c, cx, cy, r);
            else drawWebsite(c, cx, cy, r);
        }

        private void drawTelegram(Canvas c, float cx, float cy, float r) {
            p.setStyle(Paint.Style.FILL);
            p.setColor(Color.rgb(42, 171, 238));
            c.drawCircle(cx, cy, r, p);
            path.reset();
            path.moveTo(cx - r * .57f, cy - r * .03f);
            path.lineTo(cx + r * .61f, cy - r * .49f);
            path.lineTo(cx + r * .28f, cy + r * .58f);
            path.lineTo(cx - r * .08f, cy + r * .27f);
            path.lineTo(cx - r * .31f, cy + r * .43f);
            path.lineTo(cx - r * .22f, cy + r * .13f);
            path.close();
            p.setColor(Color.WHITE);
            c.drawPath(path, p);
            p.setColor(Color.argb(88, 15, 105, 160));
            path.reset();
            path.moveTo(cx - r * .22f, cy + r * .13f);
            path.lineTo(cx + r * .39f, cy - r * .31f);
            path.lineTo(cx - r * .08f, cy + r * .27f);
            path.close();
            c.drawPath(path, p);
            if ("discussion".equals(kind)) {
                p.setColor(Color.WHITE);
                c.drawCircle(cx + r * .48f, cy + r * .47f, r * .24f, p);
                p.setColor(Color.rgb(74, 112, 226));
                c.drawCircle(cx + r * .48f, cy + r * .47f, r * .16f, p);
                p.setColor(Color.WHITE);
                c.drawCircle(cx + r * .43f, cy + r * .45f, r * .025f, p);
                c.drawCircle(cx + r * .50f, cy + r * .45f, r * .025f, p);
                c.drawCircle(cx + r * .57f, cy + r * .45f, r * .025f, p);
            }
        }

        private void drawWebsite(Canvas c, float cx, float cy, float r) {
            p.setStyle(Paint.Style.FILL);
            p.setColor(Color.rgb(39, 166, 124));
            c.drawCircle(cx, cy, r, p);
            stroke.setColor(Color.WHITE);
            stroke.setStrokeWidth(Math.max(1.6f, r * .10f));
            c.drawCircle(cx, cy, r * .58f, stroke);
            c.drawLine(cx - r * .55f, cy, cx + r * .55f, cy, stroke);
            c.drawOval(cx - r * .28f, cy - r * .58f, cx + r * .28f, cy + r * .58f, stroke);
        }

        private void drawReview(Canvas c, float cx, float cy, float r) {
            p.setStyle(Paint.Style.FILL);
            p.setColor(Color.rgb(239, 133, 72));
            c.drawCircle(cx, cy, r, p);
            p.setColor(Color.WHITE);
            float left = cx - r * .52f, top = cy - r * .45f, right = cx + r * .45f, bottom = cy + r * .49f;
            c.drawRoundRect(left, top, right, bottom, r * .10f, r * .10f, p);
            p.setColor(Color.rgb(239, 133, 72));
            c.drawRect(cx - r * .07f, top + r * .09f, cx + r * .01f, bottom - r * .08f, p);
            stroke.setColor(Color.rgb(239, 133, 72));
            stroke.setStrokeWidth(Math.max(1.4f, r * .075f));
            c.drawLine(left + r * .13f, cy - r * .12f, cx - r * .16f, cy - r * .12f, stroke);
            c.drawLine(cx + r * .10f, cy - r * .12f, right - r * .12f, cy - r * .12f, stroke);
            c.drawLine(left + r * .13f, cy + r * .13f, cx - r * .16f, cy + r * .13f, stroke);
            c.drawLine(cx + r * .10f, cy + r * .13f, right - r * .12f, cy + r * .13f, stroke);
        }
    }

    private int dp(int v){return Math.round(v*getResources().getDisplayMetrics().density);}
}'''
main = replace_once(main, insert_before, logo_class, 'logo class insertion')
MAIN.write_text(main, encoding='utf-8')

# ---------- Reader gesture/tap ----------
reader = READER.read_text(encoding='utf-8')
old_tap = '''            @Override public boolean onSingleTapConfirmed(MotionEvent e) {\n                handleReaderTap(e.getX(), e.getY());\n                return true;\n            }'''
new_tap = '''            @Override public boolean onSingleTapUp(MotionEvent e) {\n                // Immediate edge tap: do not wait for the double-tap timeout.\n                handleReaderTap(e.getX(), e.getY());\n                return true;\n            }'''
reader = replace_once(reader, old_tap, new_tap, 'immediate tap')

reader = replace_once(reader,
    '                    if (ratio < 0.30f) turnPage(-1);\n                    else if (ratio > 0.70f) turnPage(1);',
    '                    if (ratio < 0.34f) turnPageFromTap(-1, y);\n                    else if (ratio > 0.66f) turnPageFromTap(1, y);',
    'tap zones')

reader = replace_once(reader,
    '            paperProgress = Math.max(0f, Math.min(1f, Math.abs(dx) / (width * 0.965f)));',
    '            paperProgress = Math.max(0f, Math.min(1f, Math.abs(dx) / (width * 0.90f)));',
    'drag progress')
reader = replace_once(reader,
    '                    (projected >= 0.37f || towardTurn > 0.52f);',
    '                    (projected >= 0.23f || towardTurn > 0.32f);',
    'drag commit threshold')

turn_anchor = '''    private void turnPage(int delta) {\n        if (webView == null || chapterLoading || !"page".equals(readingMode) || delta == 0) return;'''
new_methods = '''    private void turnPageFromTap(int delta, float tapY) {\n        if (webView == null || chapterLoading || !"page".equals(readingMode) || delta == 0) return;\n        long now = System.currentTimeMillis();\n        if (pageTurnLocked || now - lastPageTurnMs < 135L) return;\n\n        lastPageTurnMs = now;\n        int direction = delta < 0 ? -1 : 1;\n        int targetPage = currentPageInChapter + direction;\n        boolean insideChapter = targetPage >= 1 && targetPage <= pageCountInChapter;\n        if (!insideChapter) {\n            navigateChapter(direction, direction < 0);\n            return;\n        }\n        if ("paper".equals(pageAnimation) && pageCurlView != null) {\n            float touch = webView.getHeight() <= 0 ? 0.5f : Math.max(0.12f, Math.min(0.88f, tapY / (float) webView.getHeight()));\n            startNativeTapCurl(direction, targetPage - 1, touch);\n        } else {\n            performJsPageTurn(direction);\n        }\n    }\n\n    private void startNativeTapCurl(int direction, int targetZeroBased, float touchY) {\n        Bitmap current = captureWebViewBitmap();\n        if (current == null || pageCurlView == null) {\n            performJsPageTurn(direction);\n            return;\n        }\n        pageTurnLocked = true;\n        pageCurlView.hold(current);\n        String jump = "(function(){var st=window.__wowPageEngine;if(!st||st.mode!=='page')return 'unavailable';" +\n                "st.locked=true;st.page=st.clamp(" + targetZeroBased + ",0,(st.count||1)-1);st.apply(false);return 'ok';})()";\n        try {\n            webView.evaluateJavascript(jump, result -> {\n                if (result == null || result.contains("unavailable")) {\n                    pageCurlView.release();\n                    pageTurnLocked = false;\n                    performJsPageTurn(direction);\n                    return;\n                }\n                webView.postOnAnimation(() -> webView.postOnAnimation(() -> {\n                    Bitmap target = captureWebViewBitmap();\n                    if (target == null || pageCurlView == null) {\n                        if (pageCurlView != null) pageCurlView.release();\n                        finishNativePageCurl();\n                        return;\n                    }\n                    pageCurlView.startTapCurl(target, direction, touchY, this::finishNativePageCurl);\n                }));\n            });\n        } catch (Exception e) {\n            if (pageCurlView != null) pageCurlView.release();\n            pageTurnLocked = false;\n            performJsPageTurn(direction);\n        }\n    }\n\n    private void turnPage(int delta) {\n        if (webView == null || chapterLoading || !"page".equals(readingMode) || delta == 0) return;'''
reader = replace_once(reader, turn_anchor, new_methods, 'tap curl methods')
READER.write_text(reader, encoding='utf-8')

# ---------- Curl renderer ----------
curl = CURL.read_text(encoding='utf-8')
old_start = '''    void startCurl(Bitmap target, int direction, Runnable completion) {\n        beginInteractive(target, direction, 0f, 0.5f);\n        // Tap-to-turn still uses the same 3D renderer; it just receives a synthetic flick.\n        float syntheticVelocity = (direction < 0 ? 1f : -1f) * Math.max(1500f, getWidth() * 2.2f);\n        settleInteractive(true, syntheticVelocity, completion);\n    }'''
new_start = '''    void startTapCurl(Bitmap target, int direction, float touchY, Runnable completion) {\n        // Edge taps use the exact same page mesh as finger drags. Starting a hair inside\n        // the edge makes the first rendered frame visibly curl instead of looking like a cut.\n        beginInteractive(target, direction, 0.012f, clamp(touchY, 0.10f, 0.90f));\n        float syntheticVelocity = (direction < 0 ? 1f : -1f) * Math.max(1250f, getWidth() * 1.55f);\n        settleInteractive(true, syntheticVelocity, completion);\n    }\n\n    void startCurl(Bitmap target, int direction, Runnable completion) {\n        startTapCurl(target, direction, 0.5f, completion);\n    }'''
curl = replace_once(curl, old_start, new_start, 'tap curl renderer')
CURL.write_text(curl, encoding='utf-8')

# ---------- version ----------
gradle = GRADLE.read_text(encoding='utf-8')
gradle = replace_once(gradle, 'versionCode 19', 'versionCode 20', 'versionCode')
gradle = replace_once(gradle, "versionName '2.7.0'", "versionName '2.8.0'", 'versionName')
GRADLE.write_text(gradle, encoding='utf-8')

print('WoW Reader v2.8 source migration complete')
