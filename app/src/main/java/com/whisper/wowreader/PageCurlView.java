package com.whisper.wowreader;

import android.animation.Animator;
import android.animation.AnimatorListenerAdapter;
import android.animation.ValueAnimator;
import android.content.Context;
import android.graphics.Bitmap;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.LinearGradient;
import android.graphics.Paint;
import android.graphics.Path;
import android.graphics.Shader;
import android.view.View;
import android.view.animation.PathInterpolator;

final class PageCurlView extends View {
    private static final int MESH_W = 48;
    private static final int MESH_H = 18;

    private final Paint pagePaint = new Paint(Paint.ANTI_ALIAS_FLAG | Paint.FILTER_BITMAP_FLAG);
    private final Paint castShadowPaint = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final Paint foldShadePaint = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final Paint backsidePaint = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final Paint creasePaint = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final Paint outerEdgePaint = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final float[] verts = new float[(MESH_W + 1) * (MESH_H + 1) * 2];
    private final Path foldPath = new Path();
    private final Path creasePath = new Path();
    private final Path outerPath = new Path();

    private Bitmap fromBitmap;
    private Bitmap toBitmap;
    private ValueAnimator animator;
    private float progress;
    private int direction = 1;
    private Runnable completion;

    PageCurlView(Context context) {
        super(context);
        setVisibility(GONE);
        setClickable(false);
        setLayerType(View.LAYER_TYPE_HARDWARE, null);
        float d = getResources().getDisplayMetrics().density;
        creasePaint.setStyle(Paint.Style.STROKE);
        creasePaint.setStrokeWidth(Math.max(1f, d * 1.15f));
        outerEdgePaint.setStyle(Paint.Style.STROKE);
        outerEdgePaint.setStrokeWidth(Math.max(1f, d * 0.7f));
    }

    boolean isBusy() {
        return getVisibility() == VISIBLE || (animator != null && animator.isRunning());
    }

    void hold(Bitmap current) {
        cancelAnimator(false);
        recycleBitmaps();
        fromBitmap = current;
        toBitmap = null;
        progress = 0f;
        direction = 1;
        setAlpha(1f);
        setVisibility(VISIBLE);
        bringToFront();
        invalidate();
    }

    void startCurl(Bitmap target, int direction, Runnable completion) {
        if (fromBitmap == null || target == null) {
            if (target != null && !target.isRecycled()) target.recycle();
            finishImmediately(completion);
            return;
        }
        this.toBitmap = target;
        this.direction = direction < 0 ? -1 : 1;
        this.completion = completion;
        this.progress = 0f;

        cancelAnimator(false);
        animator = ValueAnimator.ofFloat(0f, 1f);
        animator.setDuration(430L);
        animator.setInterpolator(new PathInterpolator(0.16f, 0.00f, 0.18f, 1.00f));
        animator.addUpdateListener(a -> {
            progress = (float) a.getAnimatedValue();
            invalidate();
        });
        animator.addListener(new AnimatorListenerAdapter() {
            private boolean cancelled;

            @Override public void onAnimationCancel(Animator animation) {
                cancelled = true;
            }

            @Override public void onAnimationEnd(Animator animation) {
                Runnable done = PageCurlView.this.completion;
                PageCurlView.this.completion = null;
                PageCurlView.this.animator = null;
                setVisibility(GONE);
                recycleBitmaps();
                if (!cancelled && done != null) done.run();
            }
        });
        animator.start();
    }

    void release() {
        cancelAnimator(false);
        completion = null;
        setVisibility(GONE);
        recycleBitmaps();
    }

    private void finishImmediately(Runnable done) {
        setVisibility(GONE);
        recycleBitmaps();
        if (done != null) done.run();
    }

    private void cancelAnimator(boolean notify) {
        if (animator == null) return;
        Runnable old = completion;
        completion = null;
        ValueAnimator a = animator;
        animator = null;
        a.cancel();
        if (notify && old != null) old.run();
    }

    private void recycleBitmaps() {
        if (fromBitmap != null && !fromBitmap.isRecycled()) fromBitmap.recycle();
        if (toBitmap != null && toBitmap != fromBitmap && !toBitmap.isRecycled()) toBitmap.recycle();
        fromBitmap = null;
        toBitmap = null;
    }

    @Override
    protected void onDraw(Canvas canvas) {
        super.onDraw(canvas);
        if (fromBitmap == null || fromBitmap.isRecycled()) return;
        if (toBitmap == null || toBitmap.isRecycled()) {
            canvas.drawBitmap(fromBitmap, 0f, 0f, pagePaint);
            return;
        }

        // The destination page remains under the sheet. Only the current sheet curls.
        canvas.drawBitmap(toBitmap, 0f, 0f, pagePaint);
        drawNaturalCurl(canvas, fromBitmap, progress, direction);
    }

    private void drawNaturalCurl(Canvas canvas, Bitmap bitmap, float amount, int turnDirection) {
        float q = clamp(amount, 0f, 1f);
        int width = getWidth();
        int height = getHeight();
        if (width <= 0 || height <= 0) return;
        if (q < 0.001f) {
            canvas.drawBitmap(bitmap, 0f, 0f, pagePaint);
            return;
        }

        // Crease begins at the outside edge and travels slightly past the far edge.
        // The area before it remains flat while only the folded strip bends backwards.
        float creaseBase = width * (1f - q * 1.045f);
        float wave = (float) Math.sin(Math.PI * q);
        float bow = width * 0.0125f * wave;
        float backRatio = 0.64f + 0.22f * q;
        int out = 0;

        for (int row = 0; row <= MESH_H; row++) {
            float v = row / (float) MESH_H;
            float y = height * v;
            float creaseLogical = creaseBase + (float) Math.sin(Math.PI * v) * bow;
            float foldedWidth = Math.max(1f, width - creaseLogical);

            for (int col = 0; col <= MESH_W; col++) {
                float u = col / (float) MESH_W;
                float sourceX = width * u;
                float logicalX = turnDirection > 0 ? sourceX : width - sourceX;
                float nxLogical = logicalX;
                float ny = y;

                if (logicalX > creaseLogical) {
                    float t = clamp((logicalX - creaseLogical) / foldedWidth, 0f, 1f);
                    float cylinder = (float) Math.sin(Math.PI * t);
                    float shoulder = (float) Math.sin(Math.PI * 0.5f * t);
                    nxLogical = creaseLogical
                            - t * foldedWidth * backRatio
                            + cylinder * foldedWidth * (0.080f + 0.030f * wave)
                            - shoulder * width * 0.006f * q;

                    // Very small top/bottom bow keeps the sheet from feeling like plastic.
                    float vertical = cylinder * wave * height * 0.014f;
                    ny = y + vertical * ((v - 0.5f) * 2f);
                }

                verts[out++] = turnDirection > 0 ? nxLogical : width - nxLogical;
                verts[out++] = ny;
            }
        }

        canvas.drawBitmapMesh(bitmap, MESH_W, MESH_H, verts, 0, null, 0, pagePaint);
        if (q > 0.008f && q < 0.995f)
            drawFoldLighting(canvas, q, wave, creaseBase, bow, backRatio, turnDirection);
    }

    private void drawFoldLighting(Canvas canvas, float q, float wave, float creaseBase,
                                  float bow, float backRatio, int turnDirection) {
        int width = getWidth();
        int height = getHeight();
        foldPath.reset();
        creasePath.reset();
        outerPath.reset();

        final int samples = 24;
        float midCreaseLogical = creaseBase + bow;
        float midFolded = Math.max(1f, width - midCreaseLogical);
        float midOuterLogical = midCreaseLogical - midFolded * backRatio - width * 0.006f * q;
        float midCrease = screenX(midCreaseLogical, width, turnDirection);
        float midOuter = screenX(midOuterLogical, width, turnDirection);

        for (int i = 0; i <= samples; i++) {
            float v = i / (float) samples;
            float y = height * v;
            float creaseLogical = creaseBase + (float) Math.sin(Math.PI * v) * bow;
            float folded = Math.max(1f, width - creaseLogical);
            float outerLogical = creaseLogical - folded * backRatio - width * 0.006f * q;
            float cx = screenX(creaseLogical, width, turnDirection);
            if (i == 0) {
                foldPath.moveTo(cx, y);
                creasePath.moveTo(cx, y);
            } else {
                foldPath.lineTo(cx, y);
                creasePath.lineTo(cx, y);
            }
        }
        for (int i = samples; i >= 0; i--) {
            float v = i / (float) samples;
            float y = height * v;
            float creaseLogical = creaseBase + (float) Math.sin(Math.PI * v) * bow;
            float folded = Math.max(1f, width - creaseLogical);
            float outerLogical = creaseLogical - folded * backRatio - width * 0.006f * q;
            float ox = screenX(outerLogical, width, turnDirection);
            foldPath.lineTo(ox, y);
            if (i == samples) outerPath.moveTo(ox, y); else outerPath.lineTo(ox, y);
        }
        foldPath.close();

        // Light grey paper backside hides the artificial mirrored-text appearance.
        backsidePaint.setShader(new LinearGradient(
                midOuter, 0f, midCrease, 0f,
                new int[]{
                        Color.argb((int) (155f * wave), 214, 215, 218),
                        Color.argb((int) (92f * wave), 248, 248, 246),
                        Color.argb((int) (55f * wave), 255, 255, 253),
                        Color.argb((int) (126f * wave), 199, 201, 205)
                },
                new float[]{0f, 0.28f, 0.63f, 1f}, Shader.TileMode.CLAMP));
        canvas.drawPath(foldPath, backsidePaint);
        backsidePaint.setShader(null);

        // Cast shadow moves over the page underneath as the crease travels.
        float castWidth = Math.max(18f, Math.min(width * 0.13f, width * (0.035f + 0.085f * wave)));
        float castEnd = turnDirection > 0 ? midCrease + castWidth : midCrease - castWidth;
        castShadowPaint.setShader(new LinearGradient(
                midCrease, 0f, castEnd, 0f,
                new int[]{Color.argb((int) (142f * wave), 0, 0, 0),
                        Color.argb((int) (55f * wave), 0, 0, 0), Color.TRANSPARENT},
                new float[]{0f, 0.34f, 1f}, Shader.TileMode.CLAMP));
        canvas.drawRect(Math.min(midCrease, castEnd), 0f,
                Math.max(midCrease, castEnd), height, castShadowPaint);
        castShadowPaint.setShader(null);

        // Self-shadow on the folded face gives the crease a rounded paper thickness.
        float selfWidth = Math.max(12f, Math.min(width * 0.075f, Math.abs(midCrease - midOuter) * 0.22f));
        float selfEnd = turnDirection > 0 ? midCrease - selfWidth : midCrease + selfWidth;
        foldShadePaint.setShader(new LinearGradient(
                selfEnd, 0f, midCrease, 0f,
                new int[]{Color.TRANSPARENT, Color.argb((int) (90f * wave), 50, 50, 52),
                        Color.argb((int) (38f * wave), 255, 255, 255)},
                new float[]{0f, 0.72f, 1f}, Shader.TileMode.CLAMP));
        canvas.save();
        canvas.clipPath(foldPath);
        canvas.drawRect(Math.min(selfEnd, midCrease), 0f,
                Math.max(selfEnd, midCrease), height, foldShadePaint);
        canvas.restore();
        foldShadePaint.setShader(null);

        creasePaint.setColor(Color.argb((int) (185f * wave), 255, 255, 255));
        canvas.drawPath(creasePath, creasePaint);
        outerEdgePaint.setColor(Color.argb((int) (82f * wave), 38, 39, 41));
        canvas.drawPath(outerPath, outerEdgePaint);
    }

    private float screenX(float logical, int width, int turnDirection) {
        return turnDirection > 0 ? logical : width - logical;
    }

    private float clamp(float v, float lo, float hi) {
        return Math.max(lo, Math.min(hi, v));
    }

    @Override
    protected void onDetachedFromWindow() {
        release();
        super.onDetachedFromWindow();
    }
}
