from pathlib import Path

def must_replace(text, old, new, label):
    if old not in text:
        raise SystemExit(f"missing anchor: {label}")
    return text.replace(old, new, 1)

p = Path("app/src/main/java/com/whisper/wowreader/BookReaderActivity.java")
s = p.read_text()

s = must_replace(
    s,
    "import android.view.View;\nimport android.view.ViewGroup;",
    "import android.view.VelocityTracker;\nimport android.view.View;\nimport android.view.ViewConfiguration;\nimport android.view.ViewGroup;",
    "touch imports",
)

s = must_replace(
    s,
    "    private GestureDetector readerTapDetector;\n",
    """    private GestureDetector readerTapDetector;
    private VelocityTracker pageVelocityTracker;
    private int pageTouchSlop = 12;
    private float paperDownX;
    private float paperDownY;
    private float paperProgress;
    private float paperTouchY = 0.5f;
    private float paperReleaseVelocityX;
    private boolean paperGestureCandidate;
    private boolean paperGestureActive;
    private boolean paperGestureReady;
    private boolean paperGestureReleased;
    private boolean paperGestureCommit;
    private int paperGestureDirection;
    private int paperOriginalPageZero;
    private int paperTargetPageZero;
""",
    "gesture fields",
)

s = must_replace(
    s,
    "        readerTapDetector = new GestureDetector(this, new GestureDetector.SimpleOnGestureListener() {",
    """        pageTouchSlop = ViewConfiguration.get(this).getScaledTouchSlop();

        readerTapDetector = new GestureDetector(this, new GestureDetector.SimpleOnGestureListener() {""",
    "touch slop init",
)

s = must_replace(
    s,
    """        webView.setOnTouchListener((v, event) -> {
            readerTapDetector.onTouchEvent(event);
            return false;
        });
""",
    """        webView.setOnTouchListener((v, event) -> {
            boolean paperHandled = handlePaperGesture(event);
            if (!paperHandled) readerTapDetector.onTouchEvent(event);
            return paperHandled;
        });
""",
    "web touch listener",
)

interactive_methods = r"""
    private boolean handlePaperGesture(MotionEvent event) {
        if (event == null || webView == null || !"page".equals(readingMode) ||
                !"paper".equals(pageAnimation) || currentSelection != null) return false;

        int action = event.getActionMasked();
        if (action == MotionEvent.ACTION_DOWN) {
            resetPaperGestureState();
            if (chapterLoading || pageTurnLocked || (pageCurlView != null && pageCurlView.isBusy())) return false;

            paperGestureCandidate = true;
            paperDownX = event.getX();
            paperDownY = event.getY();
            paperTouchY = webView.getHeight() <= 0 ? 0.5f :
                    Math.max(0f, Math.min(1f, event.getY() / (float) webView.getHeight()));
            pageVelocityTracker = VelocityTracker.obtain();
            pageVelocityTracker.addMovement(event);
            return false;
        }

        if (!paperGestureCandidate && !paperGestureActive) return false;
        if (pageVelocityTracker != null) pageVelocityTracker.addMovement(event);

        if (action == MotionEvent.ACTION_MOVE) {
            float dx = event.getX() - paperDownX;
            float dy = event.getY() - paperDownY;

            if (!paperGestureActive) {
                if (Math.abs(dx) < pageTouchSlop) return false;
                if (Math.abs(dx) < Math.abs(dy) * 1.15f) {
                    resetPaperGestureState();
                    return false;
                }

                int direction = dx < 0f ? 1 : -1;
                int targetPage = currentPageInChapter + direction;
                if (targetPage < 1 || targetPage > pageCountInChapter) {
                    // Let the existing fling/chapter path handle chapter boundaries.
                    resetPaperGestureState();
                    return false;
                }

                if (!beginInteractivePaperTurn(direction, targetPage - 1)) {
                    resetPaperGestureState();
                    return false;
                }
                paperGestureActive = true;
            }

            float width = Math.max(1f, webView.getWidth());
            paperProgress = Math.max(0f, Math.min(1f, Math.abs(dx) / (width * 0.94f)));
            paperTouchY = webView.getHeight() <= 0 ? 0.5f :
                    Math.max(0.08f, Math.min(0.92f, event.getY() / (float) webView.getHeight()));

            if (paperGestureReady && pageCurlView != null) {
                pageCurlView.updateInteractive(paperProgress, paperTouchY);
            }
            return true;
        }

        if (action == MotionEvent.ACTION_UP || action == MotionEvent.ACTION_CANCEL) {
            if (!paperGestureActive) {
                resetPaperGestureState();
                return false;
            }

            float velocityX = 0f;
            if (pageVelocityTracker != null) {
                pageVelocityTracker.computeCurrentVelocity(1000);
                velocityX = pageVelocityTracker.getXVelocity();
            }
            paperReleaseVelocityX = velocityX;

            float width = Math.max(1f, webView.getWidth());
            float towardTurn = (-paperGestureDirection * velocityX) / width;
            float projected = paperProgress + towardTurn * 0.115f;
            boolean commit = action != MotionEvent.ACTION_CANCEL && projected >= 0.42f;

            paperGestureCommit = commit;
            paperGestureReleased = true;
            recyclePageVelocityTracker();

            if (paperGestureReady) settlePaperGesture();
            return true;
        }

        return paperGestureActive;
    }

    private boolean beginInteractivePaperTurn(int direction, int targetZeroBased) {
        if (pageCurlView == null || webView == null) return false;
        Bitmap current = captureWebViewBitmap();
        if (current == null) return false;

        paperGestureDirection = direction < 0 ? -1 : 1;
        paperOriginalPageZero = Math.max(0, currentPageInChapter - 1);
        paperTargetPageZero = Math.max(0, targetZeroBased);
        paperGestureReady = false;
        paperGestureReleased = false;
        paperGestureCommit = false;
        paperProgress = 0f;
        pageTurnLocked = true;
        lastPageTurnMs = System.currentTimeMillis();
        pageCurlView.hold(current);

        String jump = "(function(){var st=window.__wowPageEngine;if(!st||st.mode!=='page')return 'unavailable';" +
                "st.locked=true;st.page=st.clamp(" + paperTargetPageZero +
                ",0,(st.count||1)-1);st.apply(false);return 'ok';})()";
        try {
            webView.evaluateJavascript(jump, result -> {
                if (result == null || result.contains("unavailable")) {
                    if (pageCurlView != null) pageCurlView.release();
                    pageTurnLocked = false;
                    resetPaperGestureState();
                    return;
                }

                webView.postOnAnimation(() -> webView.postOnAnimation(() -> {
                    if (!paperGestureActive && !paperGestureReleased) {
                        restorePaperOriginalPage();
                        return;
                    }
                    Bitmap target = captureWebViewBitmap();
                    if (target == null || pageCurlView == null) {
                        restorePaperOriginalPage();
                        return;
                    }

                    pageCurlView.beginInteractive(target, paperGestureDirection,
                            paperProgress, paperTouchY);
                    paperGestureReady = true;
                    if (paperGestureReleased) settlePaperGesture();
                }));
            });
            return true;
        } catch (Exception e) {
            if (pageCurlView != null) pageCurlView.release();
            pageTurnLocked = false;
            return false;
        }
    }

    private void settlePaperGesture() {
        if (!paperGestureReady || pageCurlView == null) return;
        paperGestureReady = false;
        boolean commit = paperGestureCommit;
        float velocityX = paperReleaseVelocityX;

        pageCurlView.settleInteractive(commit, velocityX, () -> {
            if (commit) {
                finishNativePageCurl();
            } else {
                restorePaperOriginalPage();
            }
        });
    }

    private void restorePaperOriginalPage() {
        if (webView == null) {
            if (pageCurlView != null) pageCurlView.release();
            pageTurnLocked = false;
            resetPaperGestureState();
            return;
        }

        String restore = "(function(){var st=window.__wowPageEngine;if(!st)return;" +
                "st.page=st.clamp(" + paperOriginalPageZero +
                ",0,(st.count||1)-1);st.apply(false);st.locked=false;})()";
        try {
            webView.evaluateJavascript(restore, result -> webView.postOnAnimation(() -> {
                if (pageCurlView != null) pageCurlView.release();
                pageTurnLocked = false;
                resetPaperGestureState();
            }));
        } catch (Exception e) {
            if (pageCurlView != null) pageCurlView.release();
            pageTurnLocked = false;
            resetPaperGestureState();
        }
    }

    private void recyclePageVelocityTracker() {
        if (pageVelocityTracker != null) {
            pageVelocityTracker.recycle();
            pageVelocityTracker = null;
        }
    }

    private void resetPaperGestureState() {
        recyclePageVelocityTracker();
        paperGestureCandidate = false;
        paperGestureActive = false;
        paperGestureReady = false;
        paperGestureReleased = false;
        paperGestureCommit = false;
        paperGestureDirection = 0;
        paperProgress = 0f;
        paperReleaseVelocityX = 0f;
        paperTouchY = 0.5f;
    }

"""

s = must_replace(
    s,
    "    private void turnPage(int delta) {\n",
    interactive_methods + "    private void turnPage(int delta) {\n",
    "interactive methods insertion",
)

s = must_replace(
    s,
    """        } catch (Exception ignored) {}
        pageTurnLocked = false;
    }

    private void performJsPageTurn(int delta) {
""",
    """        } catch (Exception ignored) {}
        pageTurnLocked = false;
        resetPaperGestureState();
    }

    private void performJsPageTurn(int delta) {
""",
    "finish native reset",
)

s = must_replace(
    s,
    '        String[] labels = {"Natural paper · default", "Smooth slide", "None"};',
    '        String[] labels = {"3D page curl · default", "Smooth slide", "None"};',
    "animation label",
)

p.write_text(s)

g = Path("app/build.gradle")
gs = g.read_text()
gs = must_replace(gs, "versionCode 16", "versionCode 17", "version code")
gs = must_replace(gs, "versionName '2.4.0'", "versionName '2.5.0'", "version name")
g.write_text(gs)

w = Path(".github/workflows/build-apk.yml")
ws = w.read_text()
ws = ws.replace("versionCode 16", "versionCode 17")
ws = ws.replace("versionName '2.4.0'", "versionName '2.5.0'")
ws = ws.replace("versionCode='16'", "versionCode='17'")
ws = ws.replace("versionName='2.4.0'", "versionName='2.5.0'")
ws = ws.replace("WoW-Reader-v2.4.0", "WoW-Reader-v2.5.0")
ws = ws.replace('grep -q "MESH_W = 48" app/src/main/java/com/whisper/wowreader/PageCurlView.java',
                'grep -q "MESH_W = 60" app/src/main/java/com/whisper/wowreader/PageCurlView.java')
ws = ws.replace('grep -q "setDuration(430L)" app/src/main/java/com/whisper/wowreader/PageCurlView.java',
                'grep -q "beginInteractive" app/src/main/java/com/whisper/wowreader/PageCurlView.java\\n          grep -q "settleInteractive" app/src/main/java/com/whisper/wowreader/PageCurlView.java\\n          grep -q "VelocityTracker" app/src/main/java/com/whisper/wowreader/BookReaderActivity.java\\n          grep -q "handlePaperGesture" app/src/main/java/com/whisper/wowreader/BookReaderActivity.java\\n          grep -q "postOnAnimation" app/src/main/java/com/whisper/wowreader/BookReaderActivity.java')
w.write_text(ws)

print("Applied WoW Reader v2.5 interactive 3D page curl")
