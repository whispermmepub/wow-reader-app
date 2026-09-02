package com.whisper.wowreader;

import android.annotation.SuppressLint;
import android.app.Activity;
import android.app.AlertDialog;
import android.content.Intent;
import android.content.SharedPreferences;
import android.database.Cursor;
import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.Paint;
import android.graphics.Path;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.graphics.pdf.PdfRenderer;
import android.net.Uri;
import android.os.Bundle;
import android.os.ParcelFileDescriptor;
import android.provider.DocumentsContract;
import android.text.Editable;
import android.text.TextWatcher;
import android.view.Gravity;
import android.view.View;
import android.view.ViewGroup;
import android.widget.EditText;
import android.widget.FrameLayout;
import android.widget.HorizontalScrollView;
import android.widget.ImageView;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;
import android.widget.Toast;

import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.InputStream;
import java.io.OutputStream;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.text.Collator;
import java.util.Locale;

import androidx.recyclerview.widget.GridLayoutManager;
import androidx.recyclerview.widget.RecyclerView;

public class MainActivity extends Activity {
    private static final int REQ_IMPORT = 1001;
    private static final int REQ_BACKUP = 1002;
    private static final int REQ_RESTORE = 1003;
    private File libraryDir;
    private File coverCacheDir;
    private LinearLayout booksContainer;
    private RecyclerView libraryRecycler;
    private LibraryAdapter libraryAdapter;
    private final List<File> visibleBooks = new ArrayList<>();
    private EditText searchInput;
    private TextView floatingAdd;
    private int libraryColumns = 2;
    private TextView countView;
    private TextView viewModeButton;
    private SharedPreferences prefs;
    private boolean gridMode;
    private String searchQuery = "";
    private Typeface pyidaungsuTypeface;
    private TextView sortButton;
    private TextView authorButton;
    private TextView accountButton;
    private TextView themeButton;
    private String appTheme = "white";
    private String sortMode = "added";
    private String authorFilter = "";
    private GoogleDriveSync googleDrive;
    private GoogleDriveSync.Profile googleProfile;
    private boolean googleSyncBusy = false;
    private long lastAutoSyncAttemptMs = 0L;
    private Runnable googleSyncRetryRunnable;
    private volatile boolean metadataWarmupRunning = false;
    private final Collator myanmarCollator = Collator.getInstance(new Locale("my", "MM"));
    private final Collator englishCollator = Collator.getInstance(Locale.ENGLISH);

    @Override public void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        getWindow().setStatusBarColor(Color.rgb(247, 248, 251));
        getWindow().setNavigationBarColor(Color.rgb(247, 248, 251));
        getWindow().getDecorView().setSystemUiVisibility(View.SYSTEM_UI_FLAG_LIGHT_STATUS_BAR);
        libraryDir = new File(getFilesDir(), "library");
        coverCacheDir = new File(getFilesDir(), "cover_cache");
        if (!libraryDir.exists()) libraryDir.mkdirs();
        if (!coverCacheDir.exists()) coverCacheDir.mkdirs();
        prefs = getSharedPreferences("wow_reader", MODE_PRIVATE);
        appTheme = prefs.getString("app_theme", "white");
        if (!"white".equals(appTheme) && !"black".equals(appTheme) && !"navy".equals(appTheme)) appTheme = "white";
        applySystemBarTheme();
        googleDrive = new GoogleDriveSync(this);
        restoreStoredGoogleProfile();
        gridMode = prefs.getBoolean("library_grid", true);
        sortMode = prefs.getString("library_sort", "added");
        if (!"added".equals(sortMode) && !"opened".equals(sortMode) &&
                !"title_asc".equals(sortMode) && !"title_desc".equals(sortMode))
            sortMode = "added";
        myanmarCollator.setStrength(Collator.PRIMARY);
        englishCollator.setStrength(Collator.PRIMARY);
        try {
            pyidaungsuTypeface = Typeface.createFromAsset(getAssets(), "fonts/pyidaungsu_native.ttf");
        } catch (Exception ignored) {
            pyidaungsuTypeface = null;
        }
        buildUi();
        handleIncomingIntent(getIntent());
    }

    @Override protected void onNewIntent(Intent intent) { super.onNewIntent(intent); setIntent(intent); handleIncomingIntent(intent); }
    @Override protected void onResume() {
        super.onResume();
        if (libraryRecycler != null) refreshLibrary();
        maybeAutoGoogleSync();
    }

    private void buildUi() {
        FrameLayout root = new FrameLayout(this);
        root.setBackgroundColor(themeBackground());

        libraryRecycler = new RecyclerView(this);
        libraryRecycler.setBackgroundColor(Color.TRANSPARENT);
        libraryRecycler.setClipToPadding(false);
        libraryRecycler.setOverScrollMode(View.OVER_SCROLL_NEVER);
        androidx.recyclerview.widget.DefaultItemAnimator itemAnimator = new androidx.recyclerview.widget.DefaultItemAnimator();
        itemAnimator.setSupportsChangeAnimations(false);
        itemAnimator.setAddDuration(135L);
        itemAnimator.setRemoveDuration(110L);
        itemAnimator.setMoveDuration(170L);
        libraryRecycler.setItemAnimator(itemAnimator);
        libraryRecycler.setItemViewCacheSize(20);
        libraryRecycler.setHasFixedSize(false);
        libraryRecycler.setPadding(0, 0, 0, dp(96));

        libraryAdapter = new LibraryAdapter();
        configureLibraryLayout();
        libraryRecycler.setAdapter(libraryAdapter);
        libraryRecycler.addOnLayoutChangeListener((v, left, top, right, bottom,
                                                   oldLeft, oldTop, oldRight, oldBottom) -> {
            int width = right - left;
            if (width > 0 && width != oldRight - oldLeft)
                libraryRecycler.post(() -> updateLibraryColumnsForWidth(width));
        });
        root.addView(libraryRecycler, new FrameLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.MATCH_PARENT));

        floatingAdd = new TextView(this);
        floatingAdd.setText("＋  Add book");
        floatingAdd.setTextSize(14.5f);
        floatingAdd.setTypeface(Typeface.DEFAULT, Typeface.BOLD);
        floatingAdd.setTextColor(Color.WHITE);
        floatingAdd.setGravity(Gravity.CENTER);
        floatingAdd.setPadding(dp(14), 0, dp(16), 0);
        floatingAdd.setContentDescription("Add book");
        floatingAdd.setBackground(gradientRoundRect(themeFabColors(), dp(29)));
        floatingAdd.setElevation(dp(11));
        floatingAdd.setOnClickListener(v -> {
            try { v.performHapticFeedback(android.view.HapticFeedbackConstants.KEYBOARD_TAP); } catch (Exception ignored) {}
            chooseBook();
        });
        floatingAdd.setOnTouchListener((v, e) -> {
            int action = e.getActionMasked();
            if (action == android.view.MotionEvent.ACTION_DOWN) {
                v.animate().cancel();
                v.animate().scaleX(0.955f).scaleY(0.955f).translationY(dp(1)).setDuration(72L).start();
                v.setElevation(dp(7));
            } else if (action == android.view.MotionEvent.ACTION_UP || action == android.view.MotionEvent.ACTION_CANCEL) {
                v.animate().cancel();
                v.animate().scaleX(1f).scaleY(1f).translationY(0f).setDuration(185L)
                        .setInterpolator(new android.view.animation.OvershootInterpolator(1.18f)).start();
                v.setElevation(dp(11));
            }
            return false;
        });
        FrameLayout.LayoutParams fabLp = new FrameLayout.LayoutParams(dp(124), dp(58), Gravity.END | Gravity.BOTTOM);
        fabLp.rightMargin = dp(16);
        fabLp.bottomMargin = dp(20);
        root.addView(floatingAdd, fabLp);

        libraryRecycler.addOnScrollListener(new RecyclerView.OnScrollListener() {
            @Override public void onScrolled(RecyclerView recyclerView, int dx, int dy) {
                if (floatingAdd == null) return;
                floatingAdd.animate().cancel();
                if (dy > dp(2) && recyclerView.canScrollVertically(-1)) {
                    floatingAdd.animate().translationY(dp(88)).alpha(0f).setDuration(165L)
                            .setInterpolator(new android.view.animation.DecelerateInterpolator()).start();
                } else if (dy < -dp(2) || !recyclerView.canScrollVertically(-1)) {
                    floatingAdd.animate().translationY(0f).alpha(1f).setDuration(210L)
                            .setInterpolator(new android.view.animation.DecelerateInterpolator(1.35f)).start();
                }
            }
        });

        setContentView(root);
        refreshLibrary();
    }


    private TextView iconButton(String text) {
        TextView v = new TextView(this);
        v.setText(text);
        v.setTextSize(20);
        v.setTextColor(themePrimaryText());
        v.setGravity(Gravity.CENTER);
        v.setBackground(roundRect(themeControlSurface(), dp(22), dp(1), themeStroke()));
        v.setClickable(true);
        v.setElevation(dp(1));
        return v;
    }


    private void addDiscoverySection(LinearLayout root) {
        TextView heading = new TextView(this);
        heading.setText("Explore");
        heading.setTextSize(14);
        heading.setTextColor(themeSecondaryText());
        heading.setTypeface(Typeface.DEFAULT, Typeface.BOLD);
        heading.setPadding(dp(2), dp(12), dp(2), dp(8));
        root.addView(heading, new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT));

        HorizontalScrollView scroller = new HorizontalScrollView(this);
        scroller.setHorizontalScrollBarEnabled(false);
        scroller.setFillViewport(false);
        scroller.setOverScrollMode(View.OVER_SCROLL_NEVER);
        LinearLayout strip = new LinearLayout(this);
        strip.setOrientation(LinearLayout.HORIZONTAL);
        strip.setPadding(dp(1), 0, dp(12), dp(2));
        scroller.addView(strip, new HorizontalScrollView.LayoutParams(
                ViewGroup.LayoutParams.WRAP_CONTENT, ViewGroup.LayoutParams.WRAP_CONTENT));

        String[][] data = {
                {"telegram", "Telegram", "New books", "https://t.me/TheBookR"},
                {"discussion", "Discussion", "Reader community", "https://t.me/+rUiqzi2mdhNiNGZl"},
                {"website", "Book Website", "saroatsin.com", "https://saroatsin.com"},
                {"review", "Book Reviews", "အညွှန်း & review", "https://whispermmepub.github.io/Review/"}
        };
        int[] colors = {
                Color.rgb(232, 245, 255), Color.rgb(239, 238, 255),
                Color.rgb(235, 247, 239), Color.rgb(255, 241, 232)
        };
        for (int i = 0; i < data.length; i++) {
            LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(dp(154), dp(74));
            if (i > 0) lp.leftMargin = dp(10);
            strip.addView(discoveryCard(data[i][0], data[i][1], data[i][2], colors[i], data[i][3]), lp);
        }
        root.addView(scroller, new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, dp(78)));
    }


    private View discoveryCard(String kind, String title, String subtitle, int background, String url) {
        LinearLayout card = new LinearLayout(this);
        card.setOrientation(LinearLayout.HORIZONTAL);
        card.setGravity(Gravity.CENTER_VERTICAL);
        card.setPadding(dp(10), dp(9), dp(8), dp(9));
        card.setBackground(roundRect(themeDiscoverySurface(background), dp(18), dp(1), themeStroke()));
        card.setClickable(true);
        card.setElevation(dp(1));
        card.setOnClickListener(v -> openExternal(url));
        card.setOnTouchListener((v, e) -> {
            if (e.getActionMasked() == android.view.MotionEvent.ACTION_DOWN)
                v.animate().scaleX(0.975f).scaleY(0.975f).setDuration(80L).start();
            else if (e.getActionMasked() == android.view.MotionEvent.ACTION_UP || e.getActionMasked() == android.view.MotionEvent.ACTION_CANCEL)
                v.animate().scaleX(1f).scaleY(1f).setDuration(120L).start();
            return false;
        });

        ExploreLogoView badge = new ExploreLogoView(this, kind);
        card.addView(badge, new LinearLayout.LayoutParams(dp(42), dp(42)));

        LinearLayout copy = new LinearLayout(this);
        copy.setOrientation(LinearLayout.VERTICAL);
        copy.setPadding(dp(9), 0, 0, 0);
        TextView t = new TextView(this);
        t.setText(title);
        t.setTextSize(12.5f);
        t.setTypeface(Typeface.DEFAULT, Typeface.BOLD);
        t.setTextColor(themePrimaryText());
        t.setMaxLines(1);
        TextView sub = new TextView(this);
        sub.setText(subtitle);
        sub.setTextSize(9.5f);
        sub.setTextColor(themeSecondaryText());
        sub.setMaxLines(1);
        copy.addView(t);
        copy.addView(sub);
        card.addView(copy, new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f));
        return card;
    }


    private void openExternal(String url) {
        try {
            startActivity(new Intent(Intent.ACTION_VIEW, Uri.parse(url)));
        } catch (Exception e) {
            Toast.makeText(this, "Unable to open link", Toast.LENGTH_SHORT).show();
        }
    }

    private void refreshLibrary() {
        File[] all = libraryDir.listFiles(file -> file.isFile() && isBook(file.getName()));
        if (all == null) all = new File[0];
        sortLibraryFiles(all);

        visibleBooks.clear();
        for (File f : all) {
            String cachedTitle = cachedLibraryTitle(f).toLowerCase(Locale.ROOT);
            String fileTitle = stripExtension(f.getName()).toLowerCase(Locale.ROOT);
            String author = cachedLibraryAuthor(f);
            String authorLower = author.toLowerCase(Locale.ROOT);
            if (!authorFilter.isEmpty() && !authorFilter.equals(author)) continue;
            if (searchQuery.isEmpty() || cachedTitle.contains(searchQuery) || fileTitle.contains(searchQuery) || authorLower.contains(searchQuery))
                visibleBooks.add(f);
        }
        if (libraryAdapter != null) libraryAdapter.submit(visibleBooks);
        if (countView != null) {
            String suffix = visibleBooks.size() == 1 ? " book" : " books";
            countView.setText(visibleBooks.size() + suffix + (authorFilter.isEmpty() ? "" : " · " + authorFilter));
        }
        if (sortButton != null) sortButton.setText(sortButtonLabel());
        if (authorButton != null) authorButton.setText(authorButtonLabel());

        warmSortMetadataIfNeeded(all);
    }

    private void sortLibraryFiles(File[] files) {
        if (files == null || files.length < 2) return;
        Arrays.sort(files, (a, b) -> {
            if ("title_asc".equals(sortMode)) return compareBookTitles(a, b);
            if ("title_desc".equals(sortMode)) return -compareBookTitles(a, b);
            if ("opened".equals(sortMode)) {
                int c = Long.compare(openedTime(b), openedTime(a));
                return c != 0 ? c : compareBookTitles(a, b);
            }
            int c = Long.compare(addedTime(b), addedTime(a));
            return c != 0 ? c : compareBookTitles(a, b);
        });
    }

    private long addedTime(File file) {
        return prefs.getLong("added_at_" + file.getName(), file.lastModified());
    }

    private long openedTime(File file) {
        return prefs.getLong("last_opened_" + file.getName(), 0L);
    }

    private boolean isAlphabeticalSort() {
        return "title_asc".equals(sortMode) || "title_desc".equals(sortMode);
    }

    private String cachedLibraryTitle(File file) {
        String fallback = stripExtension(file.getName());
        String value = prefs.getString("library_title_" + file.getName(), fallback);
        return value == null || value.trim().isEmpty() ? fallback : value.trim();
    }

    private String cachedLibraryAuthor(File file) {
        String value = prefs.getString("library_author_" + file.getName(), "");
        return value == null ? "" : value.trim();
    }

    private int compareBookTitles(File a, File b) {
        String ta = normalizeSortTitle(cachedLibraryTitle(a));
        String tb = normalizeSortTitle(cachedLibraryTitle(b));
        int ga = titleScriptGroup(ta);
        int gb = titleScriptGroup(tb);
        if (ga != gb) return Integer.compare(ga, gb);
        int c;
        if (ga == 0) c = myanmarCollator.compare(ta, tb);
        else c = englishCollator.compare(ta, tb);
        if (c != 0) return c;
        return ta.compareToIgnoreCase(tb);
    }

    private String normalizeSortTitle(String value) {
        if (value == null) return "";
        String s = value.trim();
        int offset = 0;
        while (offset < s.length()) {
            int cp = s.codePointAt(offset);
            if (Character.isLetterOrDigit(cp) || isMyanmarCodePoint(cp)) break;
            offset += Character.charCount(cp);
        }
        return offset >= s.length() ? s : s.substring(offset);
    }

    private int titleScriptGroup(String value) {
        if (value == null || value.isEmpty()) return 3;
        for (int i = 0; i < value.length();) {
            int cp = value.codePointAt(i);
            if (isMyanmarCodePoint(cp)) return 0;
            if ((cp >= 'A' && cp <= 'Z') || (cp >= 'a' && cp <= 'z')) return 1;
            if (Character.isDigit(cp)) return 2;
            if (Character.isLetter(cp)) return 2;
            i += Character.charCount(cp);
        }
        return 3;
    }

    private boolean isMyanmarCodePoint(int cp) {
        return (cp >= 0x1000 && cp <= 0x109F) ||
                (cp >= 0xA9E0 && cp <= 0xA9FF) ||
                (cp >= 0xAA60 && cp <= 0xAA7F);
    }

    private void warmSortMetadataIfNeeded(File[] files) {
        if (metadataWarmupRunning || files == null || files.length == 0) return;
        boolean missing = false;
        for (File f : files) {
            if (f.getName().toLowerCase(Locale.ROOT).endsWith(".epub") &&
                    (!prefs.contains("library_title_" + f.getName()) ||
                     !prefs.contains("library_author_" + f.getName()))) {
                missing = true;
                break;
            }
        }
        if (!missing) return;
        metadataWarmupRunning = true;
        final File[] snapshot = files.clone();
        new Thread(() -> {
            SharedPreferences.Editor edit = prefs.edit();
            boolean changed = false;
            for (File f : snapshot) {
                if (!f.getName().toLowerCase(Locale.ROOT).endsWith(".epub")) continue;
                if (prefs.contains("library_title_" + f.getName()) && prefs.contains("library_author_" + f.getName())) continue;
                String title = stripExtension(f.getName());
                String author = "";
                try {
                    EpubUtil.Summary summary = EpubUtil.extractSummary(f, coverCacheDir);
                    if (summary.title != null && !summary.title.trim().isEmpty()) title = summary.title.trim();
                    if (summary.author != null && !summary.author.trim().isEmpty()) author = summary.author.trim();
                } catch (Exception ignored) {}
                edit.putString("library_title_" + f.getName(), title);
                edit.putString("library_author_" + f.getName(), author);
                changed = true;
            }
            edit.apply();
            final boolean shouldRefresh = changed;
            runOnUiThread(() -> {
                metadataWarmupRunning = false;
                if (shouldRefresh) refreshLibrary();
            });
        }, "wow-library-metadata").start();
    }

    private void addGrid(List<File> files) {
        // Retained for binary/source compatibility. The v2.6 library uses RecyclerView.
        if (libraryAdapter != null) libraryAdapter.submit(files);
    }


    private View createGridCard(File file,int cellWidth) {
        LinearLayout card = new LinearLayout(this);
        card.setOrientation(LinearLayout.VERTICAL);
        card.setPadding(dp(7), dp(7), dp(7), dp(9));
        card.setBackground(roundRect(themeCardSurface(), dp(18), dp(1), themeStroke()));
        card.setElevation(dp(1));
        card.setClickable(true);
        card.setOnClickListener(v -> openBook(file));
        card.setOnLongClickListener(v -> { confirmDelete(file); return true; });
        card.setOnTouchListener((v, e) -> {
            if (e.getActionMasked() == android.view.MotionEvent.ACTION_DOWN)
                v.animate().scaleX(0.985f).scaleY(0.985f).setDuration(70L).start();
            else if (e.getActionMasked() == android.view.MotionEvent.ACTION_UP || e.getActionMasked() == android.view.MotionEvent.ACTION_CANCEL)
                v.animate().scaleX(1f).scaleY(1f).setDuration(120L).start();
            return false;
        });

        int innerWidth = Math.max(dp(96), cellWidth - dp(26));
        int coverHeight = Math.round(innerWidth * 1.47f);
        ImageView cover = new ImageView(this);
        cover.setScaleType(ImageView.ScaleType.CENTER_CROP);
        String initial = stripExtension(file.getName());
        cover.setImageBitmap(placeholderBitmap(initial, Math.max(220, innerWidth), Math.max(320, coverHeight)));
        cover.setBackground(roundRect(Color.rgb(235, 237, 242), dp(13), 0, 0));
        cover.setClipToOutline(true);
        card.addView(cover, new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, coverHeight));

        TextView title = new TextView(this);
        title.setText(initial);
        title.setTextSize(14.5f);
        title.setTextColor(themePrimaryText());
        applyBookTitleTypeface(title);
        title.setMaxLines(2);
        title.setLineSpacing(0f, 1.05f);
        title.setPadding(dp(2), dp(9), dp(2), 0);
        card.addView(title);

        int progress = prefs.getInt("percent_" + file.getName(), 0);
        TextView meta = new TextView(this);
        meta.setText((file.getName().toLowerCase(Locale.ROOT).endsWith(".pdf") ? "PDF" : "EPUB") + " · " + progress + "%");
        meta.setTextSize(10.5f);
        meta.setTextColor(themeSecondaryText());
        meta.setSingleLine(true);
        meta.setPadding(dp(2), dp(5), dp(2), dp(6));
        card.addView(meta);

        LinearLayout track = new LinearLayout(this);
        track.setGravity(Gravity.START);
        track.setBackground(roundRect(themeTrackColor(), dp(2), 0, 0));
        View fill = new View(this);
        fill.setBackground(roundRect(themeAccent(), dp(2), 0, 0));
        int trackWidth = Math.max(1, innerWidth - dp(2));
        track.addView(fill, new LinearLayout.LayoutParams(Math.max(0, Math.round(trackWidth * progress / 100f)), dp(3)));
        card.addView(track, new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, dp(3)));

        loadBookVisual(file, cover, title, meta);
        return card;
    }


    private View createListCard(File file) {
        LinearLayout card = new LinearLayout(this);
        card.setOrientation(LinearLayout.HORIZONTAL);
        card.setGravity(Gravity.CENTER_VERTICAL);
        card.setPadding(dp(10), dp(10), dp(12), dp(10));
        card.setBackground(roundRect(themeCardSurface(), dp(18), dp(1), themeStroke()));
        card.setElevation(dp(1));
        card.setOnClickListener(v -> openBook(file));
        card.setOnLongClickListener(v -> { confirmDelete(file); return true; });
        card.setOnTouchListener((v, e) -> {
            int action = e.getActionMasked();
            if (action == android.view.MotionEvent.ACTION_DOWN) {
                v.animate().cancel();
                v.animate().scaleX(0.986f).scaleY(0.986f).setDuration(65L).start();
            } else if (action == android.view.MotionEvent.ACTION_UP || action == android.view.MotionEvent.ACTION_CANCEL) {
                v.animate().cancel();
                v.animate().scaleX(1f).scaleY(1f).setDuration(145L)
                        .setInterpolator(new android.view.animation.DecelerateInterpolator()).start();
            }
            return false;
        });

        ImageView cover = new ImageView(this);
        cover.setScaleType(ImageView.ScaleType.CENTER_CROP);
        String initial = stripExtension(file.getName());
        cover.setImageBitmap(placeholderBitmap(initial, 210, 300));
        cover.setBackground(roundRect(Color.rgb(235, 237, 242), dp(12), 0, 0));
        cover.setClipToOutline(true);
        card.addView(cover, new LinearLayout.LayoutParams(dp(76), dp(110)));

        LinearLayout text = new LinearLayout(this);
        text.setOrientation(LinearLayout.VERTICAL);
        text.setPadding(dp(14), dp(2), dp(4), dp(2));
        TextView title = new TextView(this);
        title.setText(initial);
        title.setTextSize(16);
        title.setTextColor(themePrimaryText());
        applyBookTitleTypeface(title);
        title.setMaxLines(2);
        text.addView(title);

        int progress = prefs.getInt("percent_" + file.getName(), 0);
        TextView meta = new TextView(this);
        meta.setText((file.getName().toLowerCase(Locale.ROOT).endsWith(".pdf") ? "PDF" : "EPUB") + " · " + progress + "% read");
        meta.setTextSize(12);
        meta.setTextColor(themeSecondaryText());
        meta.setPadding(0, dp(7), 0, 0);
        text.addView(meta);

        TextView action = new TextView(this);
        action.setText(progress > 0 ? "Continue reading  ›" : "Start reading  ›");
        action.setTextSize(12.5f);
        action.setTextColor(themeAccent());
        action.setTypeface(Typeface.DEFAULT, Typeface.BOLD);
        action.setPadding(0, dp(10), 0, 0);
        text.addView(action);
        card.addView(text, new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f));
        loadBookVisual(file, cover, title, meta);
        return card;
    }



    private int calculateLibraryColumns(int widthPx) {
        if (!gridMode) return 1;
        float density = Math.max(1f, getResources().getDisplayMetrics().density);
        float widthDp = Math.max(1f, widthPx / density);
        // Keep covers at a comfortable book-like size while using all available space.
        // This naturally produces 2 columns on phones and 3–6 on tablets/foldables/landscape.
        final float sideDp = 28f;
        final float gapDp = 12f;
        final float minCardDp = 154f;
        float usable = Math.max(minCardDp, widthDp - sideDp);
        int columns = (int) Math.floor((usable + gapDp) / (minCardDp + gapDp));
        return Math.max(2, Math.min(6, columns));
    }

    private void configureLibraryLayout() {
        if (libraryRecycler == null) return;
        int width = libraryRecycler.getWidth() > 0
                ? libraryRecycler.getWidth() : getResources().getDisplayMetrics().widthPixels;
        libraryColumns = calculateLibraryColumns(width);

        GridLayoutManager layout = new GridLayoutManager(this, libraryColumns);
        layout.setSpanSizeLookup(new GridLayoutManager.SpanSizeLookup() {
            @Override public int getSpanSize(int position) {
                if (position <= 1) return libraryColumns;
                if (visibleBooks.isEmpty() && position == 2) return libraryColumns;
                return 1;
            }
        });
        libraryRecycler.setLayoutManager(layout);
    }

    private void updateLibraryColumnsForWidth(int widthPx) {
        if (libraryRecycler == null || widthPx <= 0) return;
        int wanted = calculateLibraryColumns(widthPx);
        if (wanted == libraryColumns) return;
        libraryColumns = wanted;
        GridLayoutManager layout = new GridLayoutManager(this, libraryColumns);
        layout.setSpanSizeLookup(new GridLayoutManager.SpanSizeLookup() {
            @Override public int getSpanSize(int position) {
                if (position <= 1) return libraryColumns;
                if (visibleBooks.isEmpty() && position == 2) return libraryColumns;
                return 1;
            }
        });
        libraryRecycler.setLayoutManager(layout);
        if (libraryAdapter != null) libraryAdapter.notifyDataSetChanged();
    }

    private int libraryCardWidth() {
        int screen = libraryRecycler != null && libraryRecycler.getWidth() > 0
                ? libraryRecycler.getWidth() : getResources().getDisplayMetrics().widthPixels;
        int gap = dp(12);
        int side = dp(14);
        int columns = Math.max(1, libraryColumns);
        return Math.max(dp(118), (screen - side * 2 - gap * (columns - 1)) / columns);
    }

    private View buildLibraryHeader() {
        LinearLayout outer = new LinearLayout(this);
        outer.setOrientation(LinearLayout.VERTICAL);
        outer.setPadding(dp(14), dp(12), dp(14), dp(2));

        LinearLayout hero = new LinearLayout(this);
        hero.setOrientation(LinearLayout.VERTICAL);
        hero.setPadding(dp(16), dp(14), dp(12), dp(14));
        hero.setBackground(gradientRoundRect(themeHeroColors(), dp(24)));

        LinearLayout brandRow = new LinearLayout(this);
        brandRow.setOrientation(LinearLayout.HORIZONTAL);
        brandRow.setGravity(Gravity.CENTER_VERTICAL);
        LinearLayout brandCopy = new LinearLayout(this);
        brandCopy.setOrientation(LinearLayout.VERTICAL);
        TextView brand = new TextView(this);
        brand.setText("WoW Reader");
        brand.setTextSize(27);
        brand.setTextColor(themePrimaryText());
        brand.setTypeface(Typeface.DEFAULT, Typeface.BOLD);
        TextView sub = new TextView(this);
        sub.setText("Your books, beautifully organized");
        sub.setTextSize(11.5f);
        sub.setTextColor(themeSecondaryText());
        sub.setPadding(0, dp(2), 0, 0);
        brandCopy.addView(brand);
        brandCopy.addView(sub);
        brandRow.addView(brandCopy, new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f));

        accountButton = iconButton("G");
        accountButton.setTextSize(15);
        accountButton.setTypeface(Typeface.DEFAULT, Typeface.BOLD);
        accountButton.setContentDescription("Google account & cloud library");
        accountButton.setOnClickListener(v -> showAccountMenu());
        brandRow.addView(accountButton, new LinearLayout.LayoutParams(dp(44), dp(44)));
        updateAccountButton();

        themeButton = iconButton("navy".equals(appTheme) ? "✦" : "◐");
        themeButton.setTextSize(17);
        themeButton.setContentDescription("App theme");
        themeButton.setOnClickListener(v -> showAppThemeDialog());
        brandRow.addView(themeButton, new LinearLayout.LayoutParams(dp(44), dp(44)));

        viewModeButton = iconButton(gridMode ? "☷" : "▦");
        viewModeButton.setTextSize(17);
        viewModeButton.setContentDescription("Change library view");
        viewModeButton.setOnClickListener(v -> {
            gridMode = !gridMode;
            prefs.edit().putBoolean("library_grid", gridMode).apply();
            viewModeButton.setText(gridMode ? "☷" : "▦");
            configureLibraryLayout();
            if (libraryAdapter != null) libraryAdapter.notifyDataSetChanged();
        });
        LinearLayout.LayoutParams viewLp = new LinearLayout.LayoutParams(dp(44), dp(44));
        viewLp.leftMargin = dp(8);
        brandRow.addView(viewModeButton, viewLp);
        hero.addView(brandRow, new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, dp(52)));

        searchInput = new EditText(this);
        searchInput.setSingleLine(true);
        searchInput.setHint("Search title or book");
        searchInput.setTextSize(14.5f);
        searchInput.setTextColor(themePrimaryText());
        searchInput.setHintTextColor(themeSecondaryText());
        searchInput.setPadding(dp(16), 0, dp(16), 0);
        searchInput.setBackground(roundRect(themeSearchSurface(), dp(23), dp(1), themeStroke()));
        if (!searchQuery.isEmpty()) {
            searchInput.setText(searchQuery);
            searchInput.setSelection(searchInput.length());
        }
        searchInput.addTextChangedListener(new TextWatcher() {
            @Override public void beforeTextChanged(CharSequence s, int start, int count, int after) {}
            @Override public void onTextChanged(CharSequence s, int start, int before, int count) {
                searchQuery = s.toString().trim().toLowerCase(Locale.ROOT);
                refreshLibrary();
            }
            @Override public void afterTextChanged(Editable s) {}
        });
        LinearLayout.LayoutParams searchLp = new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, dp(46));
        searchLp.topMargin = dp(8);
        hero.addView(searchInput, searchLp);
        outer.addView(hero, new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT));
        addDiscoverySection(outer);
        return outer;
    }

    private View buildLibrarySectionHeader() {
        LinearLayout row = new LinearLayout(this);
        row.setOrientation(LinearLayout.HORIZONTAL);
        row.setGravity(Gravity.CENTER_VERTICAL);
        row.setPadding(dp(20), dp(7), dp(16), dp(9));

        LinearLayout copy = new LinearLayout(this);
        copy.setOrientation(LinearLayout.VERTICAL);
        copy.setGravity(Gravity.CENTER_VERTICAL);
        TextView label = new TextView(this);
        label.setText("Library");
        label.setTextSize(18);
        label.setTextColor(themePrimaryText());
        label.setTypeface(Typeface.DEFAULT, Typeface.BOLD);
        copy.addView(label);

        countView = new TextView(this);
        countView.setTextSize(10.5f);
        countView.setTextColor(themeSecondaryText());
        countView.setPadding(0, dp(1), 0, 0);
        copy.addView(countView);
        row.addView(copy, new LinearLayout.LayoutParams(0, dp(48), 1f));

        sortButton = new TextView(this);
        sortButton.setText(sortButtonLabel());
        sortButton.setTextSize(11.5f);
        sortButton.setTextColor(themeAccent());
        sortButton.setTypeface(Typeface.DEFAULT, Typeface.BOLD);
        sortButton.setGravity(Gravity.CENTER);
        sortButton.setPadding(dp(12), 0, dp(12), 0);
        sortButton.setSingleLine(true);
        sortButton.setBackground(roundRect(themeControlSurface(), dp(19), dp(1), themeStroke()));
        sortButton.setElevation(dp(1));
        sortButton.setOnClickListener(v -> showSortDialog());
        sortButton.setOnTouchListener((v, e) -> {
            if (e.getActionMasked() == android.view.MotionEvent.ACTION_DOWN)
                v.animate().scaleX(0.965f).scaleY(0.965f).setDuration(70L).start();
            else if (e.getActionMasked() == android.view.MotionEvent.ACTION_UP || e.getActionMasked() == android.view.MotionEvent.ACTION_CANCEL)
                v.animate().scaleX(1f).scaleY(1f).setDuration(110L).start();
            return false;
        });
        authorButton = new TextView(this);
        authorButton.setText(authorButtonLabel());
        authorButton.setTextSize(11.5f);
        authorButton.setTextColor(themeAccent());
        authorButton.setTypeface(Typeface.DEFAULT, Typeface.BOLD);
        authorButton.setGravity(Gravity.CENTER);
        authorButton.setPadding(dp(10), 0, dp(10), 0);
        authorButton.setSingleLine(true);
        authorButton.setMaxWidth(dp(126));
        authorButton.setEllipsize(android.text.TextUtils.TruncateAt.END);
        authorButton.setBackground(roundRect(themeControlSurface(), dp(19), dp(1), themeStroke()));
        authorButton.setOnClickListener(v -> showAuthorsDialog());
        LinearLayout.LayoutParams authorLp = new LinearLayout.LayoutParams(ViewGroup.LayoutParams.WRAP_CONTENT, dp(38));
        authorLp.rightMargin = dp(7);
        row.addView(authorButton, authorLp);

        row.addView(sortButton, new LinearLayout.LayoutParams(ViewGroup.LayoutParams.WRAP_CONTENT, dp(38)));
        return row;
    }

    private String authorButtonLabel() {
        return authorFilter.isEmpty() ? "Authors  ▾" : authorFilter + "  ×";
    }

    private void showAuthorsDialog() {
        File[] files = libraryDir.listFiles(file -> file.isFile() && isBook(file.getName()));
        if (files == null) files = new File[0];
        java.util.Map<String, Integer> counts = new java.util.HashMap<>();
        for (File f : files) {
            String author = cachedLibraryAuthor(f);
            if (author.isEmpty()) continue;
            Integer oldCount = counts.get(author);
            counts.put(author, (oldCount == null ? 0 : oldCount) + 1);
        }
        java.util.List<String> authors = new java.util.ArrayList<>(counts.keySet());
        java.util.Collections.sort(authors, (a, b) -> {
            int ga = titleScriptGroup(a), gb = titleScriptGroup(b);
            if (ga != gb) return Integer.compare(ga, gb);
            return ga == 0 ? myanmarCollator.compare(a, b) : englishCollator.compare(a, b);
        });
        String[] labels = new String[authors.size() + 1];
        labels[0] = "All authors · " + files.length + " books";
        for (int i = 0; i < authors.size(); i++) {
            String name = authors.get(i);
            labels[i + 1] = name + " · " + counts.get(name) + (counts.get(name) == 1 ? " book" : " books");
        }
        new AlertDialog.Builder(this)
                .setTitle("Authors")
                .setItems(labels, (dialog, which) -> {
                    authorFilter = which == 0 ? "" : authors.get(which - 1);
                    refreshLibrary();
                })
                .setNegativeButton("Cancel", null)
                .show();
        warmSortMetadataIfNeeded(files);
    }

    private String sortButtonLabel() {
        if ("opened".equals(sortMode)) return "Recently opened  ▾";
        if ("title_asc".equals(sortMode)) return "က–အ · A–Z  ▾";
        if ("title_desc".equals(sortMode)) return "အ–က · Z–A  ▾";
        return "Recently added  ▾";
    }

    private void showSortDialog() {
        String[] labels = {
                "Recently added",
                "Recently opened",
                "Title · က–အ / A–Z",
                "Title · အ–က / Z–A"
        };
        String[] values = {"added", "opened", "title_asc", "title_desc"};
        int selected = "opened".equals(sortMode) ? 1 :
                ("title_asc".equals(sortMode) ? 2 : ("title_desc".equals(sortMode) ? 3 : 0));
        new AlertDialog.Builder(this)
                .setTitle("Sort library")
                .setSingleChoiceItems(labels, selected, (dialog, which) -> {
                    sortMode = values[which];
                    prefs.edit().putString("library_sort", sortMode).apply();
                    if (sortButton != null) sortButton.setText(sortButtonLabel());
                    refreshLibrary();
                    dialog.dismiss();
                })
                .setNegativeButton("Cancel", null)
                .show();
    }

    private View buildEmptyState() {
        TextView empty = new TextView(this);
        empty.setTextSize(15);
        empty.setTextColor(themeSecondaryText());
        empty.setGravity(Gravity.CENTER);
        empty.setPadding(dp(30), dp(72), dp(30), dp(96));
        return empty;
    }

    private boolean isBlackAppTheme() { return "black".equals(appTheme); }
    private boolean isNavyAppTheme() { return "navy".equals(appTheme); }

    private int themeBackground() {
        if (isBlackAppTheme()) return Color.rgb(12, 13, 16);
        if (isNavyAppTheme()) return Color.rgb(3, 28, 48);
        return Color.rgb(247, 248, 251);
    }

    private int themeCardSurface() {
        if (isBlackAppTheme()) return Color.rgb(27, 29, 34);
        if (isNavyAppTheme()) return Color.rgb(7, 44, 70);
        return Color.WHITE;
    }

    private int themeControlSurface() {
        if (isBlackAppTheme()) return Color.rgb(35, 37, 43);
        if (isNavyAppTheme()) return Color.rgb(10, 51, 79);
        return Color.argb(232, 255, 255, 255);
    }

    private int themeSearchSurface() {
        if (isBlackAppTheme()) return Color.rgb(28, 30, 35);
        if (isNavyAppTheme()) return Color.rgb(6, 42, 67);
        return Color.argb(232, 255, 255, 255);
    }

    private int themePrimaryText() {
        return (isBlackAppTheme() || isNavyAppTheme()) ? Color.rgb(244, 247, 250) : Color.rgb(31, 34, 40);
    }

    private int themeSecondaryText() {
        if (isBlackAppTheme()) return Color.rgb(178, 183, 192);
        if (isNavyAppTheme()) return Color.rgb(165, 196, 213);
        return Color.rgb(105, 110, 122);
    }

    private int themeAccent() {
        if (isBlackAppTheme()) return Color.rgb(151, 166, 255);
        if (isNavyAppTheme()) return Color.rgb(239, 194, 91);
        return Color.rgb(82, 82, 214);
    }

    private int themeStroke() {
        if (isBlackAppTheme()) return Color.rgb(55, 59, 68);
        if (isNavyAppTheme()) return Color.rgb(26, 91, 120);
        return Color.rgb(224, 227, 234);
    }

    private int themeTrackColor() {
        if (isBlackAppTheme()) return Color.rgb(50, 53, 61);
        if (isNavyAppTheme()) return Color.rgb(18, 67, 91);
        return Color.rgb(236, 238, 243);
    }

    private int[] themeHeroColors() {
        if (isBlackAppTheme()) return new int[]{Color.rgb(30, 32, 39), Color.rgb(19, 20, 25)};
        if (isNavyAppTheme()) return new int[]{Color.rgb(4, 45, 73), Color.rgb(2, 29, 51), Color.rgb(4, 52, 74)};
        return new int[]{Color.rgb(239, 243, 255), Color.rgb(255, 247, 242)};
    }

    private int[] themeFabColors() {
        if (isBlackAppTheme()) return new int[]{Color.rgb(104, 91, 226), Color.rgb(63, 79, 170)};
        if (isNavyAppTheme()) return new int[]{Color.rgb(8, 174, 199), Color.rgb(10, 105, 145)};
        return new int[]{Color.rgb(92, 76, 226), Color.rgb(71, 113, 236)};
    }

    private int themeDiscoverySurface(int lightFallback) {
        if (isBlackAppTheme()) return Color.rgb(29, 32, 38);
        if (isNavyAppTheme()) return Color.rgb(7, 49, 77);
        return lightFallback;
    }

    private void applySystemBarTheme() {
        int bg = themeBackground();
        getWindow().setStatusBarColor(bg);
        getWindow().setNavigationBarColor(bg);
        int flags = 0;
        if (!isBlackAppTheme() && !isNavyAppTheme()) flags = View.SYSTEM_UI_FLAG_LIGHT_STATUS_BAR | View.SYSTEM_UI_FLAG_LIGHT_NAVIGATION_BAR;
        getWindow().getDecorView().setSystemUiVisibility(flags);
    }

    private void showAppThemeDialog() {
        String[] labels = {"White", "Black", "Navy Premium"};
        String[] values = {"white", "black", "navy"};
        int selected = isBlackAppTheme() ? 1 : (isNavyAppTheme() ? 2 : 0);
        new AlertDialog.Builder(this)
                .setTitle("App theme")
                .setSingleChoiceItems(labels, selected, (dialog, which) -> {
                    String chosen = values[which];
                    if (!chosen.equals(appTheme)) {
                        appTheme = chosen;
                        prefs.edit().putString("app_theme", appTheme).apply();
                        dialog.dismiss();
                        recreate();
                    } else dialog.dismiss();
                })
                .setNegativeButton("Cancel", null)
                .show();
    }

    private GradientDrawable gradientRoundRect(int[] colors, int radius) {
        GradientDrawable d = new GradientDrawable(GradientDrawable.Orientation.TL_BR, colors);
        d.setCornerRadius(radius);
        return d;
    }

    private final class LibraryAdapter extends RecyclerView.Adapter<LibraryHolder> {
        private static final int HEADER = 0;
        private static final int SECTION = 1;
        private static final int BOOK = 2;
        private static final int EMPTY = 3;
        private final List<File> items = new ArrayList<>();

        void submit(List<File> next) {
            items.clear();
            if (next != null) items.addAll(next);
            notifyDataSetChanged();
        }

        @Override public int getItemCount() {
            return 2 + (items.isEmpty() ? 1 : items.size());
        }

        @Override public int getItemViewType(int position) {
            if (position == 0) return HEADER;
            if (position == 1) return SECTION;
            if (items.isEmpty()) return EMPTY;
            return BOOK;
        }

        @Override public LibraryHolder onCreateViewHolder(ViewGroup parent, int viewType) {
            if (viewType == HEADER) return new LibraryHolder(buildLibraryHeader());
            if (viewType == SECTION) return new LibraryHolder(buildLibrarySectionHeader());
            if (viewType == EMPTY) return new LibraryHolder(buildEmptyState());
            FrameLayout shell = new FrameLayout(MainActivity.this);
            shell.setPadding(dp(7), 0, dp(7), dp(14));
            return new LibraryHolder(shell);
        }

        @Override public void onBindViewHolder(LibraryHolder holder, int position) {
            int type = getItemViewType(position);
            if (type == SECTION) {
                if (countView != null) countView.setText(items.size() + (items.size() == 1 ? " book" : " books"));
                return;
            }
            if (type == EMPTY) {
                ((TextView) holder.itemView).setText(searchQuery.isEmpty()
                        ? "Your library is ready.\nTap ＋ to add an EPUB or PDF."
                        : "No books match your search.");
                return;
            }
            if (type != BOOK) return;
            int index = position - 2;
            if (index < 0 || index >= items.size()) return;
            File file = items.get(index);
            FrameLayout shell = (FrameLayout) holder.itemView;
            shell.removeAllViews();
            View card = gridMode ? createGridCard(file, libraryCardWidth()) : createListCard(file);
            shell.addView(card, new FrameLayout.LayoutParams(
                    ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT));
        }
    }

    private static final class LibraryHolder extends RecyclerView.ViewHolder {
        LibraryHolder(View itemView) { super(itemView); }
    }

    private void loadBookVisual(File file,ImageView cover,TextView titleView,TextView metaView){
        new Thread(()->{ String title=stripExtension(file.getName()),author=cachedLibraryAuthor(file); Bitmap bitmap=null; try{ if(file.getName().toLowerCase(Locale.ROOT).endsWith(".epub")){ EpubUtil.Summary s=EpubUtil.extractSummary(file,coverCacheDir); if(s.title!=null&&!s.title.isEmpty()) title=s.title; if(s.author!=null&&!s.author.trim().isEmpty()) author=s.author.trim(); if(s.cover!=null&&s.cover.isFile()) bitmap=BitmapFactory.decodeFile(s.cover.getAbsolutePath()); } else bitmap=renderPdfCover(file); }catch(Exception ignored){}
            prefs.edit().putString("library_title_" + file.getName(), title).putString("library_author_" + file.getName(), author).apply();
            String ft=title,fa=author; Bitmap fb=bitmap; int progress=prefs.getInt("percent_"+file.getName(),0); runOnUiThread(()->{ if(fb!=null) cover.setImageBitmap(fb); titleView.setText(ft); applyBookTitleTypeface(titleView); String type=file.getName().toLowerCase(Locale.ROOT).endsWith(".pdf")?"PDF":"EPUB"; metaView.setText(fa.isEmpty()?type+" · "+progress+"%":fa+" · "+progress+"%"); if(!fa.isEmpty()){ if(pyidaungsuTypeface!=null) metaView.setTypeface(pyidaungsuTypeface); metaView.setClickable(true); metaView.setOnClickListener(v->{authorFilter=fa;refreshLibrary();}); } }); }).start();
    }

    private Bitmap renderPdfCover(File file){ ParcelFileDescriptor pfd=null; PdfRenderer renderer=null; PdfRenderer.Page page=null; try{ pfd=ParcelFileDescriptor.open(file,ParcelFileDescriptor.MODE_READ_ONLY); renderer=new PdfRenderer(pfd); if(renderer.getPageCount()==0)return null; page=renderer.openPage(0); int width=360,height=Math.max(1,Math.round(width*(page.getHeight()/(float)page.getWidth()))); Bitmap b=Bitmap.createBitmap(width,height,Bitmap.Config.ARGB_8888); b.eraseColor(Color.WHITE); page.render(b,null,null,PdfRenderer.Page.RENDER_MODE_FOR_DISPLAY); return b; }catch(Exception e){return null;} finally{try{if(page!=null)page.close();}catch(Exception ignored){} try{if(renderer!=null)renderer.close();}catch(Exception ignored){} try{if(pfd!=null)pfd.close();}catch(Exception ignored){}} }

    private Bitmap placeholderBitmap(String title,int width,int height){ Bitmap b=Bitmap.createBitmap(Math.max(1,width),Math.max(1,height),Bitmap.Config.ARGB_8888); Canvas c=new Canvas(b); Paint p=new Paint(Paint.ANTI_ALIAS_FLAG); p.setColor(colorForName(title)); c.drawRect(0,0,b.getWidth(),b.getHeight(),p); p.setColor(Color.WHITE); p.setTypeface(Typeface.create(pyidaungsuTypeface != null ? pyidaungsuTypeface : Typeface.DEFAULT,Typeface.BOLD)); p.setTextSize(Math.min(width,height)*.25f); p.setTextAlign(Paint.Align.CENTER); String letter=title==null||title.trim().isEmpty()?"W":title.trim().substring(0,1).toUpperCase(Locale.ROOT); Paint.FontMetrics fm=p.getFontMetrics(); float y=height/2f-(fm.ascent+fm.descent)/2f; c.drawText(letter,width/2f,y,p); return b; }

    private void chooseBook(){ Intent i=new Intent(Intent.ACTION_OPEN_DOCUMENT); i.addCategory(Intent.CATEGORY_OPENABLE); i.setType("*/*"); i.putExtra(Intent.EXTRA_MIME_TYPES,new String[]{"application/epub+zip","application/pdf"}); startActivityForResult(i,REQ_IMPORT); }
    private void handleIncomingIntent(Intent intent){
        if(intent==null)return;
        Uri data=null;
        String action=intent.getAction();
        if(Intent.ACTION_VIEW.equals(action)) data=intent.getData();
        else if(Intent.ACTION_SEND.equals(action)){
            try{Object stream=intent.getParcelableExtra(Intent.EXTRA_STREAM);if(stream instanceof Uri)data=(Uri)stream;}catch(Exception ignored){}
        }
        if(data!=null){
            intent.setAction(null);
            importBook(data,false);
        }
    }

    private void importBook(Uri uri,boolean openAfter){
        new Thread(()->{
            try{
                String name=queryDisplayName(uri);
                if(name==null||name.trim().isEmpty())name="book_"+System.currentTimeMillis();
                String lower=name.toLowerCase(Locale.ROOT),mime=getContentResolver().getType(uri);
                if(!lower.endsWith(".epub")&&!lower.endsWith(".pdf")){
                    if("application/pdf".equals(mime))name+=".pdf";
                    else if("application/epub+zip".equals(mime))name+=".epub";
                    else throw new Exception("Only EPUB and PDF files are supported");
                }
                File out=uniqueFile(name);
                try(InputStream in=getContentResolver().openInputStream(uri);OutputStream os=new FileOutputStream(out)){
                    if(in==null)throw new Exception("Unable to open file");
                    copy(in,os);
                }
                String displayTitle=stripExtension(out.getName());
                String displayAuthor="";
                if(out.getName().toLowerCase(Locale.ROOT).endsWith(".epub")){
                    try{
                        EpubUtil.Summary summary=EpubUtil.extractSummary(out,coverCacheDir);
                        if(summary.title!=null&&!summary.title.trim().isEmpty())displayTitle=summary.title.trim();
                        if(summary.author!=null&&!summary.author.trim().isEmpty())displayAuthor=summary.author.trim();
                    }catch(Exception ignored){}
                }
                prefs.edit()
                        .putLong("added_at_"+out.getName(),System.currentTimeMillis())
                        .putString("library_title_"+out.getName(),displayTitle)
                        .putString("library_author_"+out.getName(),displayAuthor)
                        .putBoolean("library_owned_"+out.getName(),true)
                        .putLong("sync_updated_ms",System.currentTimeMillis())
                        .apply();
                runOnUiThread(()->{
                    Toast.makeText(this,"Added to Library · local copy saved",Toast.LENGTH_SHORT).show();
                    refreshLibrary();
                    maybeAutoGoogleSync();
                });
            }catch(Exception e){
                runOnUiThread(()->Toast.makeText(this,e.getMessage(),Toast.LENGTH_LONG).show());
            }
        },"wow-import-book").start();
    }

    private void applyBookTitleTypeface(TextView view){
        if(view==null)return;
        if(pyidaungsuTypeface!=null)view.setTypeface(pyidaungsuTypeface,Typeface.BOLD);
        else view.setTypeface(Typeface.DEFAULT,Typeface.BOLD);
    }

    private String queryDisplayName(Uri uri){ if("file".equalsIgnoreCase(uri.getScheme()))return new File(uri.getPath()).getName(); Cursor c=null; try{c=getContentResolver().query(uri,new String[]{android.provider.OpenableColumns.DISPLAY_NAME},null,null,null);if(c!=null&&c.moveToFirst())return c.getString(0);}catch(Exception ignored){}finally{if(c!=null)c.close();}return null; }
    private File uniqueFile(String originalName){ String safe=originalName.replaceAll("[\\\\/:*?\"<>|]","_"); File f=new File(libraryDir,safe);if(!f.exists())return f;int dot=safe.lastIndexOf('.');String base=dot>0?safe.substring(0,dot):safe,ext=dot>0?safe.substring(dot):"";return new File(libraryDir,base+"_"+System.currentTimeMillis()+ext); }
    private void openBook(File file){prefs.edit().putLong("last_opened_"+file.getName(),System.currentTimeMillis()).apply();Intent i=new Intent(this,BookReaderActivity.class);i.putExtra("path",file.getAbsolutePath());startActivity(i);overridePendingTransition(android.R.anim.fade_in,android.R.anim.fade_out);}
    private void confirmDelete(File file){new AlertDialog.Builder(this).setTitle("Remove from WoW Reader?").setMessage(stripExtension(file.getName())+"\n\nThis deletes WoW Reader's saved local copy. The original file you imported from Downloads or another folder is not changed.").setNegativeButton("Cancel",null).setPositiveButton("Remove",(d,w)->{if(file.delete()){prefs.edit().remove("percent_"+file.getName()).remove("library_title_"+file.getName()).remove("library_author_"+file.getName()).remove("library_owned_"+file.getName()).remove("added_at_"+file.getName()).remove("last_opened_"+file.getName()).putLong("sync_updated_ms",System.currentTimeMillis()).apply();refreshLibrary();maybeAutoGoogleSync();}}).show();}

    private void restoreStoredGoogleProfile(){
        if(!prefs.getBoolean("google_sync_connected",false)) return;
        googleProfile=new GoogleDriveSync.Profile();
        googleProfile.name=prefs.getString("google_account_name","Google account");
        googleProfile.email=prefs.getString("google_account_email","");
        googleProfile.picture=prefs.getString("google_account_picture","");
    }

    private void updateAccountButton(){
        if(accountButton==null)return;
        boolean connected=prefs!=null&&prefs.getBoolean("google_sync_connected",false);
        String name=googleProfile==null?prefs.getString("google_account_name",""):googleProfile.name;
        String initial="G";
        if(connected&&name!=null&&!name.trim().isEmpty())initial=name.trim().substring(0,1).toUpperCase(Locale.ROOT);
        accountButton.setText(initial);
        accountButton.setTextColor(connected?Color.WHITE:Color.rgb(67,68,190));
        accountButton.setBackground(connected
                ?gradientRoundRect(new int[]{Color.rgb(91,76,220),Color.rgb(70,112,235)},dp(22))
                :roundRect(Color.argb(188,255,255,255),dp(22),dp(1),Color.argb(80,210,214,222)));
        accountButton.setContentDescription(connected?"Google account connected":"Connect Google account");
    }

    private void showAccountMenu(){
        boolean connected=prefs.getBoolean("google_sync_connected",false);
        if(!connected){
            new AlertDialog.Builder(this)
                    .setTitle("Account & backup")
                    .setMessage("Connect a Google account to privately sync books, notes, highlights and reading progress to your Drive.")
                    .setItems(new String[]{"Connect Google account","Manual folder backup","Manual folder restore"},(d,w)->{
                        if(w==0)connectGoogleAccount(true); else openManualCloudPicker(w==1);
                    }).show();
            return;
        }
        String name=prefs.getString("google_account_name","Google account");
        String email=prefs.getString("google_account_email","");
        boolean auto=prefs.getBoolean("google_sync_enabled",true);
        String[] items={"Sync now","Restore from Google Drive","Auto sync: "+(auto?"On":"Off"),"Switch Google account","Disconnect Google account","Manual folder backup","Manual folder restore"};
        new AlertDialog.Builder(this)
                .setTitle(name)
                .setMessage((email.isEmpty()?"":email+"\n")+"WoW Reader data is stored privately in this account's Google Drive app data.")
                .setItems(items,(d,w)->{
                    if(w==0)performGoogleBackup(true);
                    else if(w==1)confirmGoogleRestore();
                    else if(w==2){prefs.edit().putBoolean("google_sync_enabled",!auto).apply();Toast.makeText(this,"Auto sync "+(!auto?"on":"off"),Toast.LENGTH_SHORT).show();}
                    else if(w==3)connectGoogleAccount(true);
                    else if(w==4)disconnectGoogleAccount();
                    else openManualCloudPicker(w==5);
                }).show();
    }

    private void connectGoogleAccount(boolean chooseAccount){
        if(googleDrive==null)googleDrive=new GoogleDriveSync(this);
        googleDrive.authorize(chooseAccount,new GoogleDriveSync.AuthCallback(){
            @Override public void onReady(GoogleDriveSync.Profile profile){
                googleProfile=profile;
                prefs.edit()
                        .putBoolean("google_sync_connected",true)
                        .putBoolean("google_sync_enabled",true)
                        .putString("google_account_name",profile.name==null?"Google account":profile.name)
                        .putString("google_account_email",profile.email==null?"":profile.email)
                        .putString("google_account_picture",profile.picture==null?"":profile.picture)
                        .apply();
                updateAccountButton();
                GoogleDriveSync.hasBackup(MainActivity.this,profile.accessToken,found->{
                    File[] local=libraryDir.listFiles(file->file.isFile()&&isBook(file.getName()));
                    boolean empty=local==null||local.length==0;
                    if(found&&empty){
                        new AlertDialog.Builder(MainActivity.this).setTitle("Restore your library?")
                                .setMessage("A WoW Reader backup was found in this Google Drive. Restore your books, notes and highlights to this device?")
                                .setNegativeButton("Not now",null).setPositiveButton("Restore",(d,w)->performGoogleRestore()).show();
                    }else{
                        new AlertDialog.Builder(MainActivity.this).setTitle("Google Drive connected")
                                .setMessage("Auto sync is on. Back up this device now?")
                                .setNegativeButton("Later",null).setPositiveButton("Back up now",(d,w)->performGoogleBackup(true)).show();
                    }
                });
            }
            @Override public void onError(String message){Toast.makeText(MainActivity.this,message,Toast.LENGTH_LONG).show();}
        });
    }

    private void rememberGoogleProfile(GoogleDriveSync.Profile profile){
        googleProfile=profile;
        prefs.edit().putBoolean("google_sync_connected",true)
                .putString("google_account_name",profile.name==null?"Google account":profile.name)
                .putString("google_account_email",profile.email==null?"":profile.email)
                .putString("google_account_picture",profile.picture==null?"":profile.picture).apply();
        updateAccountButton();
    }

    private File readerFontsDir(){File d=new File(getFilesDir(),"reader_fonts");if(!d.exists())d.mkdirs();return d;}

    private void performGoogleBackup(boolean showToast){
        if(googleSyncBusy){scheduleGoogleSyncRetry(12000L);return;}
        googleSyncBusy=true;
        final long requestedChangeMs=prefs.getLong("sync_updated_ms",0L);
        googleDrive.authorize(false,new GoogleDriveSync.AuthCallback(){
            @Override public void onReady(GoogleDriveSync.Profile profile){
                rememberGoogleProfile(profile);
                GoogleDriveSync.backup(MainActivity.this,profile.accessToken,libraryDir,readerFontsDir(),prefs,new GoogleDriveSync.SyncCallback(){
                    @Override public void onSuccess(String message){prefs.edit().putLong("google_last_synced_change_ms",requestedChangeMs).apply();googleSyncBusy=false;if(showToast)Toast.makeText(MainActivity.this,message,Toast.LENGTH_LONG).show();maybeAutoGoogleSync();}
                    @Override public void onError(String message){googleSyncBusy=false;if(showToast)Toast.makeText(MainActivity.this,message,Toast.LENGTH_LONG).show();}
                });
            }
            @Override public void onError(String message){googleSyncBusy=false;if(showToast)Toast.makeText(MainActivity.this,message,Toast.LENGTH_LONG).show();}
        });
    }

    private void confirmGoogleRestore(){
        new AlertDialog.Builder(this).setTitle("Restore from Google Drive?")
                .setMessage("Books with the same stored name will be replaced. Notes, highlights, reading progress and reader settings from the backup will be restored.")
                .setNegativeButton("Cancel",null).setPositiveButton("Restore",(d,w)->performGoogleRestore()).show();
    }

    private void performGoogleRestore(){
        if(googleSyncBusy)return;
        googleSyncBusy=true;
        googleDrive.authorize(false,new GoogleDriveSync.AuthCallback(){
            @Override public void onReady(GoogleDriveSync.Profile profile){
                rememberGoogleProfile(profile);
                GoogleDriveSync.restore(MainActivity.this,profile.accessToken,libraryDir,readerFontsDir(),prefs,new GoogleDriveSync.SyncCallback(){
                    @Override public void onSuccess(String message){googleSyncBusy=false;authorFilter="";refreshLibrary();Toast.makeText(MainActivity.this,message,Toast.LENGTH_LONG).show();}
                    @Override public void onError(String message){googleSyncBusy=false;Toast.makeText(MainActivity.this,message,Toast.LENGTH_LONG).show();}
                });
            }
            @Override public void onError(String message){googleSyncBusy=false;Toast.makeText(MainActivity.this,message,Toast.LENGTH_LONG).show();}
        });
    }

    private void maybeAutoGoogleSync(){
        if(prefs==null||googleDrive==null)return;
        if(!prefs.getBoolean("google_sync_connected",false)||!prefs.getBoolean("google_sync_enabled",true))return;
        long changed=prefs.getLong("sync_updated_ms",0L);
        long synced=prefs.getLong("google_last_synced_change_ms",prefs.getLong("google_last_backup_ms",0L));
        if(changed<=synced)return;
        if(googleSyncBusy){scheduleGoogleSyncRetry(12000L);return;}
        long now=System.currentTimeMillis();
        long remaining=12000L-(now-lastAutoSyncAttemptMs);
        if(remaining>0L){scheduleGoogleSyncRetry(remaining);return;}
        lastAutoSyncAttemptMs=now;
        performGoogleBackup(false);
    }

    private void scheduleGoogleSyncRetry(long delayMs){
        if(libraryRecycler==null)return;
        if(googleSyncRetryRunnable!=null)libraryRecycler.removeCallbacks(googleSyncRetryRunnable);
        googleSyncRetryRunnable=()->{googleSyncRetryRunnable=null;maybeAutoGoogleSync();};
        libraryRecycler.postDelayed(googleSyncRetryRunnable,Math.max(1500L,delayMs));
    }

    private void disconnectGoogleAccount(){
        GoogleDriveSync.Profile profile=googleProfile;
        Runnable clear=()->runOnUiThread(()->{
            googleProfile=null;
            prefs.edit().remove("google_sync_connected").remove("google_sync_enabled").remove("google_account_name").remove("google_account_email").remove("google_account_picture").remove("google_last_synced_change_ms").apply();
            updateAccountButton();
            Toast.makeText(this,"Google account disconnected",Toast.LENGTH_SHORT).show();
        });
        if(googleDrive!=null)googleDrive.revoke(profile,clear);else clear.run();
    }

    private void openManualCloudPicker(boolean backup){
        Intent i=new Intent(Intent.ACTION_OPEN_DOCUMENT_TREE);
        i.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION|Intent.FLAG_GRANT_WRITE_URI_PERMISSION|Intent.FLAG_GRANT_PERSISTABLE_URI_PERMISSION);
        startActivityForResult(i,backup?REQ_BACKUP:REQ_RESTORE);
    }

    private void showCloudMenu(){new AlertDialog.Builder(this).setTitle("Backup & restore").setItems(new String[]{"Backup library","Restore books"},(dialog,which)->{Intent i=new Intent(Intent.ACTION_OPEN_DOCUMENT_TREE);i.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION|Intent.FLAG_GRANT_WRITE_URI_PERMISSION|Intent.FLAG_GRANT_PERSISTABLE_URI_PERMISSION);startActivityForResult(i,which==0?REQ_BACKUP:REQ_RESTORE);}).show();}
    @SuppressLint("WrongConstant")
    @Override protected void onActivityResult(int requestCode,int resultCode,Intent data){
        super.onActivityResult(requestCode,resultCode,data);
        if(googleDrive!=null&&googleDrive.handleActivityResult(requestCode,resultCode,data))return;
        if(resultCode!=RESULT_OK||data==null||data.getData()==null)return;
        Uri uri=data.getData();
        if(requestCode==REQ_IMPORT){importBook(uri,false);return;}
        try{getContentResolver().takePersistableUriPermission(uri,data.getFlags()&(Intent.FLAG_GRANT_READ_URI_PERMISSION|Intent.FLAG_GRANT_WRITE_URI_PERMISSION));}catch(Exception ignored){}
        if(requestCode==REQ_BACKUP)backupLibrary(uri);else if(requestCode==REQ_RESTORE)restoreLibrary(uri);
    }

    private void backupLibrary(Uri treeUri){new Thread(()->{int count=0;try{File[] files=libraryDir.listFiles();if(files!=null)for(File file:files){if(!isBook(file.getName()))continue;Uri target=findChild(treeUri,file.getName());if(target==null){String mime=file.getName().toLowerCase(Locale.ROOT).endsWith(".pdf")?"application/pdf":"application/epub+zip";target=DocumentsContract.createDocument(getContentResolver(),treeDocumentUri(treeUri),mime,file.getName());}if(target!=null)try(InputStream in=new FileInputStream(file);OutputStream out=getContentResolver().openOutputStream(target,"wt")){if(out!=null){copy(in,out);count++;}}}int n=count;runOnUiThread(()->Toast.makeText(this,"Backup complete: "+n+" books",Toast.LENGTH_LONG).show());}catch(Exception e){runOnUiThread(()->Toast.makeText(this,"Backup failed: "+e.getMessage(),Toast.LENGTH_LONG).show());}}).start();}
    private void restoreLibrary(Uri treeUri){new Thread(()->{int count=0;Cursor c=null;try{Uri children=DocumentsContract.buildChildDocumentsUriUsingTree(treeUri,DocumentsContract.getTreeDocumentId(treeUri));c=getContentResolver().query(children,new String[]{DocumentsContract.Document.COLUMN_DOCUMENT_ID,DocumentsContract.Document.COLUMN_DISPLAY_NAME},null,null,null);if(c!=null)while(c.moveToNext()){String id=c.getString(0),name=c.getString(1);if(!isBook(name))continue;Uri doc=DocumentsContract.buildDocumentUriUsingTree(treeUri,id);File out=new File(libraryDir,name.replaceAll("[\\\\/:*?\"<>|]","_"));try(InputStream in=getContentResolver().openInputStream(doc);OutputStream os=new FileOutputStream(out)){if(in!=null){copy(in,os);prefs.edit().putLong("added_at_"+out.getName(),System.currentTimeMillis()).apply();count++;}}}int n=count;runOnUiThread(()->{refreshLibrary();Toast.makeText(this,"Restored: "+n+" books",Toast.LENGTH_LONG).show();});}catch(Exception e){runOnUiThread(()->Toast.makeText(this,"Restore failed: "+e.getMessage(),Toast.LENGTH_LONG).show());}finally{if(c!=null)c.close();}}).start();}
    private Uri findChild(Uri treeUri,String name){Cursor c=null;try{Uri children=DocumentsContract.buildChildDocumentsUriUsingTree(treeUri,DocumentsContract.getTreeDocumentId(treeUri));c=getContentResolver().query(children,new String[]{DocumentsContract.Document.COLUMN_DOCUMENT_ID,DocumentsContract.Document.COLUMN_DISPLAY_NAME},null,null,null);if(c!=null)while(c.moveToNext())if(name.equals(c.getString(1)))return DocumentsContract.buildDocumentUriUsingTree(treeUri,c.getString(0));}catch(Exception ignored){}finally{if(c!=null)c.close();}return null;}
    private Uri treeDocumentUri(Uri treeUri){return DocumentsContract.buildDocumentUriUsingTree(treeUri,DocumentsContract.getTreeDocumentId(treeUri));}
    private boolean isBook(String n){String s=n==null?"":n.toLowerCase(Locale.ROOT);return s.endsWith(".epub")||s.endsWith(".pdf");}
    private static void copy(InputStream in,OutputStream out)throws Exception{byte[] b=new byte[64*1024];int n;while((n=in.read(b))>0)out.write(b,0,n);}
    private String stripExtension(String name){int dot=name.lastIndexOf('.');return dot>0?name.substring(0,dot):name;}
    private int colorForName(String name){int[] colors={Color.rgb(96,74,139),Color.rgb(55,102,136),Color.rgb(151,78,74),Color.rgb(76,111,82),Color.rgb(130,89,55)};return colors[Math.abs(name==null?0:name.hashCode())%colors.length];}
    private GradientDrawable roundRect(int color,float radius,int strokeWidth,int strokeColor){GradientDrawable g=new GradientDrawable();g.setColor(color);g.setCornerRadius(radius);if(strokeWidth>0)g.setStroke(strokeWidth,strokeColor);return g;}
    private final class ExploreLogoView extends View {
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
}
