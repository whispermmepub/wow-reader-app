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
        gridMode = prefs.getBoolean("library_grid", true);
        buildUi();
        handleIncomingIntent(getIntent());
    }

    @Override protected void onNewIntent(Intent intent) { super.onNewIntent(intent); setIntent(intent); handleIncomingIntent(intent); }
    @Override protected void onResume() { super.onResume(); if (libraryRecycler != null) refreshLibrary(); }

    private void buildUi() {
        FrameLayout root = new FrameLayout(this);
        root.setBackgroundColor(Color.rgb(247, 248, 251));

        libraryRecycler = new RecyclerView(this);
        libraryRecycler.setBackgroundColor(Color.TRANSPARENT);
        libraryRecycler.setClipToPadding(false);
        libraryRecycler.setOverScrollMode(View.OVER_SCROLL_NEVER);
        libraryRecycler.setItemAnimator(null);
        libraryRecycler.setPadding(0, 0, 0, dp(96));

        libraryAdapter = new LibraryAdapter();
        configureLibraryLayout();
        libraryRecycler.setAdapter(libraryAdapter);
        root.addView(libraryRecycler, new FrameLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.MATCH_PARENT));

        floatingAdd = new TextView(this);
        floatingAdd.setText("＋");
        floatingAdd.setTextSize(30);
        floatingAdd.setTextColor(Color.WHITE);
        floatingAdd.setGravity(Gravity.CENTER);
        floatingAdd.setContentDescription("Add book");
        floatingAdd.setBackground(roundRect(Color.rgb(82, 82, 214), dp(28), 0, 0));
        floatingAdd.setElevation(dp(10));
        floatingAdd.setOnClickListener(v -> chooseBook());
        FrameLayout.LayoutParams fabLp = new FrameLayout.LayoutParams(dp(58), dp(58), Gravity.END | Gravity.BOTTOM);
        fabLp.rightMargin = dp(18);
        fabLp.bottomMargin = dp(22);
        root.addView(floatingAdd, fabLp);

        libraryRecycler.addOnScrollListener(new RecyclerView.OnScrollListener() {
            @Override public void onScrolled(RecyclerView recyclerView, int dx, int dy) {
                if (floatingAdd == null) return;
                if (dy > dp(2) && recyclerView.canScrollVertically(-1)) {
                    floatingAdd.animate().translationY(dp(86)).alpha(0.16f).setDuration(180L).start();
                } else if (dy < -dp(2) || !recyclerView.canScrollVertically(-1)) {
                    floatingAdd.animate().translationY(0f).alpha(1f).setDuration(180L).start();
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
        v.setTextColor(Color.rgb(52, 55, 62));
        v.setGravity(Gravity.CENTER);
        v.setBackground(roundRect(Color.argb(188, 255, 255, 255), dp(22), dp(1), Color.argb(80, 210, 214, 222)));
        v.setClickable(true);
        v.setElevation(dp(1));
        return v;
    }


    private void addDiscoverySection(LinearLayout root) {
        TextView heading = new TextView(this);
        heading.setText("Explore");
        heading.setTextSize(14);
        heading.setTextColor(Color.rgb(74, 78, 88));
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
                {"T", "Telegram", "New books", "https://t.me/TheBookR"},
                {"D", "Discussion", "Reader community", "https://t.me/+rUiqzi2mdhNiNGZl"},
                {"W", "Book Website", "saroatsin.com", "https://saroatsin.com"},
                {"R", "Book Reviews", "အညွှန်း & review", "https://whispermmepub.github.io/Review/"}
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


    private View discoveryCard(String letter, String title, String subtitle, int background, String url) {
        LinearLayout card = new LinearLayout(this);
        card.setOrientation(LinearLayout.HORIZONTAL);
        card.setGravity(Gravity.CENTER_VERTICAL);
        card.setPadding(dp(10), dp(9), dp(8), dp(9));
        card.setBackground(roundRect(background, dp(18), dp(1), Color.argb(46, 80, 88, 105)));
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

        TextView badge = new TextView(this);
        badge.setText(letter);
        badge.setTextSize(14);
        badge.setTypeface(Typeface.DEFAULT, Typeface.BOLD);
        badge.setTextColor(Color.rgb(55, 60, 72));
        badge.setGravity(Gravity.CENTER);
        badge.setBackground(roundRect(Color.argb(185, 255, 255, 255), dp(18), 0, 0));
        card.addView(badge, new LinearLayout.LayoutParams(dp(38), dp(38)));

        LinearLayout copy = new LinearLayout(this);
        copy.setOrientation(LinearLayout.VERTICAL);
        copy.setPadding(dp(9), 0, 0, 0);
        TextView t = new TextView(this);
        t.setText(title);
        t.setTextSize(12.5f);
        t.setTypeface(Typeface.DEFAULT, Typeface.BOLD);
        t.setTextColor(Color.rgb(35, 38, 45));
        t.setMaxLines(1);
        TextView sub = new TextView(this);
        sub.setText(subtitle);
        sub.setTextSize(9.5f);
        sub.setTextColor(Color.rgb(99, 104, 116));
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
        Arrays.sort(all, (a, b) -> {
            long aa = prefs.getLong("last_opened_" + a.getName(), a.lastModified());
            long bb = prefs.getLong("last_opened_" + b.getName(), b.lastModified());
            return Long.compare(bb, aa);
        });
        visibleBooks.clear();
        for (File f : all) {
            if (searchQuery.isEmpty() || stripExtension(f.getName()).toLowerCase(Locale.ROOT).contains(searchQuery))
                visibleBooks.add(f);
        }
        if (libraryAdapter != null) libraryAdapter.submit(visibleBooks);
        if (countView != null) countView.setText(visibleBooks.size() + (visibleBooks.size() == 1 ? " book" : " books"));
    }


    private void addGrid(List<File> files) {
        // Retained for binary/source compatibility. The v2.6 library uses RecyclerView.
        if (libraryAdapter != null) libraryAdapter.submit(files);
    }


    private View createGridCard(File file,int cellWidth) {
        LinearLayout card = new LinearLayout(this);
        card.setOrientation(LinearLayout.VERTICAL);
        card.setPadding(dp(7), dp(7), dp(7), dp(9));
        card.setBackground(roundRect(Color.WHITE, dp(18), dp(1), Color.rgb(232, 234, 240)));
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
        title.setTextColor(Color.rgb(29, 31, 37));
        title.setTypeface(Typeface.DEFAULT, Typeface.BOLD);
        title.setMaxLines(2);
        title.setLineSpacing(0f, 1.05f);
        title.setPadding(dp(2), dp(9), dp(2), 0);
        card.addView(title);

        int progress = prefs.getInt("percent_" + file.getName(), 0);
        TextView meta = new TextView(this);
        meta.setText((file.getName().toLowerCase(Locale.ROOT).endsWith(".pdf") ? "PDF" : "EPUB") + " · " + progress + "%");
        meta.setTextSize(10.5f);
        meta.setTextColor(Color.rgb(103, 108, 120));
        meta.setSingleLine(true);
        meta.setPadding(dp(2), dp(5), dp(2), dp(6));
        card.addView(meta);

        LinearLayout track = new LinearLayout(this);
        track.setGravity(Gravity.START);
        track.setBackground(roundRect(Color.rgb(236, 238, 243), dp(2), 0, 0));
        View fill = new View(this);
        fill.setBackground(roundRect(Color.rgb(82, 82, 214), dp(2), 0, 0));
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
        card.setBackground(roundRect(Color.WHITE, dp(18), dp(1), Color.rgb(232, 234, 240)));
        card.setElevation(dp(1));
        card.setOnClickListener(v -> openBook(file));
        card.setOnLongClickListener(v -> { confirmDelete(file); return true; });

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
        title.setTextColor(Color.rgb(29, 31, 37));
        title.setTypeface(Typeface.DEFAULT, Typeface.BOLD);
        title.setMaxLines(2);
        text.addView(title);

        int progress = prefs.getInt("percent_" + file.getName(), 0);
        TextView meta = new TextView(this);
        meta.setText((file.getName().toLowerCase(Locale.ROOT).endsWith(".pdf") ? "PDF" : "EPUB") + " · " + progress + "% read");
        meta.setTextSize(12);
        meta.setTextColor(Color.rgb(103, 108, 120));
        meta.setPadding(0, dp(7), 0, 0);
        text.addView(meta);

        TextView action = new TextView(this);
        action.setText(progress > 0 ? "Continue reading  ›" : "Start reading  ›");
        action.setTextSize(12.5f);
        action.setTextColor(Color.rgb(82, 82, 214));
        action.setTypeface(Typeface.DEFAULT, Typeface.BOLD);
        action.setPadding(0, dp(10), 0, 0);
        text.addView(action);
        card.addView(text, new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f));
        loadBookVisual(file, cover, title, meta);
        return card;
    }



    private void configureLibraryLayout() {
        if (libraryRecycler == null) return;
        int widthDp = Math.round(getResources().getDisplayMetrics().widthPixels /
                Math.max(1f, getResources().getDisplayMetrics().density));
        if (!gridMode) libraryColumns = 1;
        else if (widthDp >= 900) libraryColumns = 5;
        else if (widthDp >= 680) libraryColumns = 4;
        else if (widthDp >= 430) libraryColumns = 3;
        else libraryColumns = 2;

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

    private int libraryCardWidth() {
        int screen = getResources().getDisplayMetrics().widthPixels;
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
        hero.setBackground(gradientRoundRect(new int[]{Color.rgb(239, 243, 255), Color.rgb(255, 247, 242)}, dp(24)));

        LinearLayout brandRow = new LinearLayout(this);
        brandRow.setOrientation(LinearLayout.HORIZONTAL);
        brandRow.setGravity(Gravity.CENTER_VERTICAL);
        LinearLayout brandCopy = new LinearLayout(this);
        brandCopy.setOrientation(LinearLayout.VERTICAL);
        TextView brand = new TextView(this);
        brand.setText("WoW Reader");
        brand.setTextSize(27);
        brand.setTextColor(Color.rgb(27, 29, 35));
        brand.setTypeface(Typeface.DEFAULT, Typeface.BOLD);
        TextView sub = new TextView(this);
        sub.setText("Your books, beautifully organized");
        sub.setTextSize(11.5f);
        sub.setTextColor(Color.rgb(100, 104, 116));
        sub.setPadding(0, dp(2), 0, 0);
        brandCopy.addView(brand);
        brandCopy.addView(sub);
        brandRow.addView(brandCopy, new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f));

        TextView backup = iconButton("⇅");
        backup.setTextSize(18);
        backup.setContentDescription("Backup and restore");
        backup.setOnClickListener(v -> showCloudMenu());
        brandRow.addView(backup, new LinearLayout.LayoutParams(dp(44), dp(44)));

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
        searchInput.setTextColor(Color.rgb(31, 34, 40));
        searchInput.setHintTextColor(Color.rgb(118, 123, 136));
        searchInput.setPadding(dp(16), 0, dp(16), 0);
        searchInput.setBackground(roundRect(Color.argb(218, 255, 255, 255), dp(23), dp(1), Color.argb(70, 180, 185, 198)));
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
        row.setPadding(dp(20), dp(8), dp(20), dp(8));
        TextView label = new TextView(this);
        label.setText("Library");
        label.setTextSize(18);
        label.setTextColor(Color.rgb(31, 34, 40));
        label.setTypeface(Typeface.DEFAULT, Typeface.BOLD);
        row.addView(label, new LinearLayout.LayoutParams(0, dp(42), 1f));
        countView = new TextView(this);
        countView.setTextSize(12);
        countView.setTextColor(Color.rgb(106, 111, 124));
        countView.setGravity(Gravity.CENTER_VERTICAL | Gravity.END);
        row.addView(countView, new LinearLayout.LayoutParams(dp(100), dp(42)));
        return row;
    }

    private View buildEmptyState() {
        TextView empty = new TextView(this);
        empty.setTextSize(15);
        empty.setTextColor(Color.rgb(104, 109, 121));
        empty.setGravity(Gravity.CENTER);
        empty.setPadding(dp(30), dp(72), dp(30), dp(96));
        return empty;
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
        new Thread(()->{ String title=stripExtension(file.getName()),author=""; Bitmap bitmap=null; try{ if(file.getName().toLowerCase(Locale.ROOT).endsWith(".epub")){ EpubUtil.Summary s=EpubUtil.extractSummary(file,coverCacheDir); if(s.title!=null&&!s.title.isEmpty()) title=s.title; if(s.author!=null) author=s.author; if(s.cover!=null&&s.cover.isFile()) bitmap=BitmapFactory.decodeFile(s.cover.getAbsolutePath()); } else bitmap=renderPdfCover(file); }catch(Exception ignored){}
            String ft=title,fa=author; Bitmap fb=bitmap; int progress=prefs.getInt("percent_"+file.getName(),0); runOnUiThread(()->{ if(fb!=null) cover.setImageBitmap(fb); titleView.setText(ft); String type=file.getName().toLowerCase(Locale.ROOT).endsWith(".pdf")?"PDF":"EPUB"; metaView.setText(fa.isEmpty()?type+" · "+progress+"%":fa+" · "+progress+"%"); }); }).start();
    }

    private Bitmap renderPdfCover(File file){ ParcelFileDescriptor pfd=null; PdfRenderer renderer=null; PdfRenderer.Page page=null; try{ pfd=ParcelFileDescriptor.open(file,ParcelFileDescriptor.MODE_READ_ONLY); renderer=new PdfRenderer(pfd); if(renderer.getPageCount()==0)return null; page=renderer.openPage(0); int width=360,height=Math.max(1,Math.round(width*(page.getHeight()/(float)page.getWidth()))); Bitmap b=Bitmap.createBitmap(width,height,Bitmap.Config.ARGB_8888); b.eraseColor(Color.WHITE); page.render(b,null,null,PdfRenderer.Page.RENDER_MODE_FOR_DISPLAY); return b; }catch(Exception e){return null;} finally{try{if(page!=null)page.close();}catch(Exception ignored){} try{if(renderer!=null)renderer.close();}catch(Exception ignored){} try{if(pfd!=null)pfd.close();}catch(Exception ignored){}} }

    private Bitmap placeholderBitmap(String title,int width,int height){ Bitmap b=Bitmap.createBitmap(Math.max(1,width),Math.max(1,height),Bitmap.Config.ARGB_8888); Canvas c=new Canvas(b); Paint p=new Paint(Paint.ANTI_ALIAS_FLAG); p.setColor(colorForName(title)); c.drawRect(0,0,b.getWidth(),b.getHeight(),p); p.setColor(Color.WHITE); p.setTypeface(Typeface.create(Typeface.DEFAULT,Typeface.BOLD)); p.setTextSize(Math.min(width,height)*.25f); p.setTextAlign(Paint.Align.CENTER); String letter=title==null||title.trim().isEmpty()?"W":title.trim().substring(0,1).toUpperCase(Locale.ROOT); Paint.FontMetrics fm=p.getFontMetrics(); float y=height/2f-(fm.ascent+fm.descent)/2f; c.drawText(letter,width/2f,y,p); return b; }

    private void chooseBook(){ Intent i=new Intent(Intent.ACTION_OPEN_DOCUMENT); i.addCategory(Intent.CATEGORY_OPENABLE); i.setType("*/*"); i.putExtra(Intent.EXTRA_MIME_TYPES,new String[]{"application/epub+zip","application/pdf"}); startActivityForResult(i,REQ_IMPORT); }
    private void handleIncomingIntent(Intent intent){ if(intent==null||!Intent.ACTION_VIEW.equals(intent.getAction()))return; Uri data=intent.getData(); if(data!=null) importBook(data,true); }

    private void importBook(Uri uri,boolean openAfter){ new Thread(()->{ try{ String name=queryDisplayName(uri); if(name==null||name.trim().isEmpty())name="book_"+System.currentTimeMillis(); String lower=name.toLowerCase(Locale.ROOT),mime=getContentResolver().getType(uri); if(!lower.endsWith(".epub")&&!lower.endsWith(".pdf")){ if("application/pdf".equals(mime))name+=".pdf"; else if("application/epub+zip".equals(mime))name+=".epub"; else throw new Exception("Only EPUB and PDF files are supported"); } File out=uniqueFile(name); try(InputStream in=getContentResolver().openInputStream(uri);OutputStream os=new FileOutputStream(out)){if(in==null)throw new Exception("Unable to open file");copy(in,os);} runOnUiThread(()->{Toast.makeText(this,"Added to WoW Reader",Toast.LENGTH_SHORT).show();refreshLibrary();if(openAfter)openBook(out);}); }catch(Exception e){runOnUiThread(()->Toast.makeText(this,e.getMessage(),Toast.LENGTH_LONG).show());} }).start(); }

    private String queryDisplayName(Uri uri){ if("file".equalsIgnoreCase(uri.getScheme()))return new File(uri.getPath()).getName(); Cursor c=null; try{c=getContentResolver().query(uri,new String[]{android.provider.OpenableColumns.DISPLAY_NAME},null,null,null);if(c!=null&&c.moveToFirst())return c.getString(0);}catch(Exception ignored){}finally{if(c!=null)c.close();}return null; }
    private File uniqueFile(String originalName){ String safe=originalName.replaceAll("[\\\\/:*?\"<>|]","_"); File f=new File(libraryDir,safe);if(!f.exists())return f;int dot=safe.lastIndexOf('.');String base=dot>0?safe.substring(0,dot):safe,ext=dot>0?safe.substring(dot):"";return new File(libraryDir,base+"_"+System.currentTimeMillis()+ext); }
    private void openBook(File file){prefs.edit().putLong("last_opened_"+file.getName(),System.currentTimeMillis()).apply();Intent i=new Intent(this,BookReaderActivity.class);i.putExtra("path",file.getAbsolutePath());startActivity(i);}
    private void confirmDelete(File file){new AlertDialog.Builder(this).setTitle("Remove from library?").setMessage(stripExtension(file.getName())).setNegativeButton("Cancel",null).setPositiveButton("Remove",(d,w)->{if(file.delete()){prefs.edit().remove("percent_"+file.getName()).apply();refreshLibrary();}}).show();}

    private void showCloudMenu(){new AlertDialog.Builder(this).setTitle("Backup & restore").setItems(new String[]{"Backup library","Restore books"},(dialog,which)->{Intent i=new Intent(Intent.ACTION_OPEN_DOCUMENT_TREE);i.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION|Intent.FLAG_GRANT_WRITE_URI_PERMISSION|Intent.FLAG_GRANT_PERSISTABLE_URI_PERMISSION);startActivityForResult(i,which==0?REQ_BACKUP:REQ_RESTORE);}).show();}
    @SuppressLint("WrongConstant")
    @Override protected void onActivityResult(int requestCode,int resultCode,Intent data){super.onActivityResult(requestCode,resultCode,data);if(resultCode!=RESULT_OK||data==null||data.getData()==null)return;Uri uri=data.getData();if(requestCode==REQ_IMPORT){importBook(uri,false);return;}try{getContentResolver().takePersistableUriPermission(uri,data.getFlags()&(Intent.FLAG_GRANT_READ_URI_PERMISSION|Intent.FLAG_GRANT_WRITE_URI_PERMISSION));}catch(Exception ignored){}if(requestCode==REQ_BACKUP)backupLibrary(uri);else if(requestCode==REQ_RESTORE)restoreLibrary(uri);}

    private void backupLibrary(Uri treeUri){new Thread(()->{int count=0;try{File[] files=libraryDir.listFiles();if(files!=null)for(File file:files){if(!isBook(file.getName()))continue;Uri target=findChild(treeUri,file.getName());if(target==null){String mime=file.getName().toLowerCase(Locale.ROOT).endsWith(".pdf")?"application/pdf":"application/epub+zip";target=DocumentsContract.createDocument(getContentResolver(),treeDocumentUri(treeUri),mime,file.getName());}if(target!=null)try(InputStream in=new FileInputStream(file);OutputStream out=getContentResolver().openOutputStream(target,"wt")){if(out!=null){copy(in,out);count++;}}}int n=count;runOnUiThread(()->Toast.makeText(this,"Backup complete: "+n+" books",Toast.LENGTH_LONG).show());}catch(Exception e){runOnUiThread(()->Toast.makeText(this,"Backup failed: "+e.getMessage(),Toast.LENGTH_LONG).show());}}).start();}
    private void restoreLibrary(Uri treeUri){new Thread(()->{int count=0;Cursor c=null;try{Uri children=DocumentsContract.buildChildDocumentsUriUsingTree(treeUri,DocumentsContract.getTreeDocumentId(treeUri));c=getContentResolver().query(children,new String[]{DocumentsContract.Document.COLUMN_DOCUMENT_ID,DocumentsContract.Document.COLUMN_DISPLAY_NAME},null,null,null);if(c!=null)while(c.moveToNext()){String id=c.getString(0),name=c.getString(1);if(!isBook(name))continue;Uri doc=DocumentsContract.buildDocumentUriUsingTree(treeUri,id);File out=new File(libraryDir,name.replaceAll("[\\\\/:*?\"<>|]","_"));try(InputStream in=getContentResolver().openInputStream(doc);OutputStream os=new FileOutputStream(out)){if(in!=null){copy(in,os);count++;}}}int n=count;runOnUiThread(()->{refreshLibrary();Toast.makeText(this,"Restored: "+n+" books",Toast.LENGTH_LONG).show();});}catch(Exception e){runOnUiThread(()->Toast.makeText(this,"Restore failed: "+e.getMessage(),Toast.LENGTH_LONG).show());}finally{if(c!=null)c.close();}}).start();}
    private Uri findChild(Uri treeUri,String name){Cursor c=null;try{Uri children=DocumentsContract.buildChildDocumentsUriUsingTree(treeUri,DocumentsContract.getTreeDocumentId(treeUri));c=getContentResolver().query(children,new String[]{DocumentsContract.Document.COLUMN_DOCUMENT_ID,DocumentsContract.Document.COLUMN_DISPLAY_NAME},null,null,null);if(c!=null)while(c.moveToNext())if(name.equals(c.getString(1)))return DocumentsContract.buildDocumentUriUsingTree(treeUri,c.getString(0));}catch(Exception ignored){}finally{if(c!=null)c.close();}return null;}
    private Uri treeDocumentUri(Uri treeUri){return DocumentsContract.buildDocumentUriUsingTree(treeUri,DocumentsContract.getTreeDocumentId(treeUri));}
    private boolean isBook(String n){String s=n==null?"":n.toLowerCase(Locale.ROOT);return s.endsWith(".epub")||s.endsWith(".pdf");}
    private static void copy(InputStream in,OutputStream out)throws Exception{byte[] b=new byte[64*1024];int n;while((n=in.read(b))>0)out.write(b,0,n);}
    private String stripExtension(String name){int dot=name.lastIndexOf('.');return dot>0?name.substring(0,dot):name;}
    private int colorForName(String name){int[] colors={Color.rgb(96,74,139),Color.rgb(55,102,136),Color.rgb(151,78,74),Color.rgb(76,111,82),Color.rgb(130,89,55)};return colors[Math.abs(name==null?0:name.hashCode())%colors.length];}
    private GradientDrawable roundRect(int color,float radius,int strokeWidth,int strokeColor){GradientDrawable g=new GradientDrawable();g.setColor(color);g.setCornerRadius(radius);if(strokeWidth>0)g.setStroke(strokeWidth,strokeColor);return g;}
    private int dp(int v){return Math.round(v*getResources().getDisplayMetrics().density);}
}
