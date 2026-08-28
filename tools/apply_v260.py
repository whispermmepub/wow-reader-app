from pathlib import Path


def replace_method(text, signature, replacement):
    start = text.find(signature)
    if start < 0:
        raise SystemExit('missing method: ' + signature)
    brace = text.find('{', start)
    if brace < 0:
        raise SystemExit('missing brace: ' + signature)
    depth = 0
    i = brace
    in_string = False
    in_char = False
    escape = False
    line_comment = False
    block_comment = False
    while i < len(text):
        c = text[i]
        n = text[i + 1] if i + 1 < len(text) else ''
        if line_comment:
            if c == '\n': line_comment = False
        elif block_comment:
            if c == '*' and n == '/':
                block_comment = False
                i += 1
        elif in_string:
            if escape: escape = False
            elif c == '\\': escape = True
            elif c == '"': in_string = False
        elif in_char:
            if escape: escape = False
            elif c == '\\': escape = True
            elif c == "'": in_char = False
        else:
            if c == '/' and n == '/': line_comment = True; i += 1
            elif c == '/' and n == '*': block_comment = True; i += 1
            elif c == '"': in_string = True
            elif c == "'": in_char = True
            elif c == '{': depth += 1
            elif c == '}':
                depth -= 1
                if depth == 0:
                    return text[:start] + replacement.rstrip() + '\n' + text[i + 1:]
        i += 1
    raise SystemExit('unclosed method: ' + signature)


def add_once(text, anchor, addition, label):
    if addition.strip() in text:
        return text
    if anchor not in text:
        raise SystemExit('missing anchor: ' + label)
    return text.replace(anchor, anchor + addition, 1)


main_path = Path('app/src/main/java/com/whisper/wowreader/MainActivity.java')
main = main_path.read_text()

main = add_once(main, 'import android.widget.EditText;\n', 'import android.widget.FrameLayout;\nimport android.widget.HorizontalScrollView;\n', 'main widget imports')
main = add_once(main, 'import java.util.Locale;\n', '\nimport androidx.recyclerview.widget.GridLayoutManager;\nimport androidx.recyclerview.widget.RecyclerView;\n', 'recycler imports')
main = add_once(main, '    private LinearLayout booksContainer;\n', '''    private RecyclerView libraryRecycler;\n    private LibraryAdapter libraryAdapter;\n    private final List<File> visibleBooks = new ArrayList<>();\n    private EditText searchInput;\n    private TextView floatingAdd;\n    private int libraryColumns = 2;\n''', 'library fields')
main = main.replace('@Override protected void onResume() { super.onResume(); if (booksContainer != null) refreshLibrary(); }',
                    '@Override protected void onResume() { super.onResume(); if (libraryRecycler != null) refreshLibrary(); }')
main = main.replace('getWindow().setStatusBarColor(Color.WHITE);', 'getWindow().setStatusBarColor(Color.rgb(247, 248, 251));')
main = main.replace('getWindow().setNavigationBarColor(Color.WHITE);', 'getWindow().setNavigationBarColor(Color.rgb(247, 248, 251));')

main = replace_method(main, '    private void buildUi()', r'''    private void buildUi() {
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
    }''')

main = replace_method(main, '    private TextView iconButton(String text)', r'''    private TextView iconButton(String text) {
        TextView v = new TextView(this);
        v.setText(text);
        v.setTextSize(20);
        v.setTextColor(Color.rgb(52, 55, 62));
        v.setGravity(Gravity.CENTER);
        v.setBackground(roundRect(Color.argb(188, 255, 255, 255), dp(22), dp(1), Color.argb(80, 210, 214, 222)));
        v.setClickable(true);
        v.setElevation(dp(1));
        return v;
    }''')

main = replace_method(main, '    private void addDiscoverySection(LinearLayout root)', r'''    private void addDiscoverySection(LinearLayout root) {
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
    }''')

main = replace_method(main, '    private View discoveryCard(String letter, String title, String subtitle, int background, String url)', r'''    private View discoveryCard(String letter, String title, String subtitle, int background, String url) {
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
    }''')

main = replace_method(main, '    private void refreshLibrary()', r'''    private void refreshLibrary() {
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
    }''')

main = replace_method(main, '    private void addGrid(List<File> files)', r'''    private void addGrid(List<File> files) {
        // Retained for binary/source compatibility. The v2.6 library uses RecyclerView.
        if (libraryAdapter != null) libraryAdapter.submit(files);
    }''')

main = replace_method(main, '    private View createGridCard(File file,int cellWidth)', r'''    private View createGridCard(File file,int cellWidth) {
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
    }''')

main = replace_method(main, '    private View createListCard(File file)', r'''    private View createListCard(File file) {
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
    }''')

extra_main = r'''
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

'''
if '    private void configureLibraryLayout()' not in main:
    marker = '    private void loadBookVisual(File file,ImageView cover,TextView titleView,TextView metaView)'
    if marker not in main: raise SystemExit('missing loadBookVisual marker')
    main = main.replace(marker, extra_main + marker, 1)

main = main.replace('    private void openBook(File file){Intent i=new Intent(this,BookReaderActivity.class);i.putExtra("path",file.getAbsolutePath());startActivity(i);}',
                    '    private void openBook(File file){prefs.edit().putLong("last_opened_"+file.getName(),System.currentTimeMillis()).apply();Intent i=new Intent(this,BookReaderActivity.class);i.putExtra("path",file.getAbsolutePath());startActivity(i);}')

main_path.write_text(main)


reader_path = Path('app/src/main/java/com/whisper/wowreader/BookReaderActivity.java')
reader = reader_path.read_text()
reader = add_once(reader, '    private int paperTargetPageZero;\n', '    private boolean paperGestureChapterBoundary;\n', 'paper boundary field')

reader = replace_method(reader, '    private void onWebSelection(String text, int start, int end)', r'''    private void onWebSelection(String text, int start, int end) {
        if (paperGestureActive || suppressingSelectionForPaperGesture()) {
            currentSelection = null;
            hideSelectionBar();
            clearWebSelection();
            return;
        }
        if (text == null || text.trim().isEmpty() || end <= start) {
            currentSelection = null;
            hideSelectionBar();
            return;
        }
        if (paperGestureCandidate) {
            paperGestureCandidate = false;
            recyclePageVelocityTracker();
        }
        SelectionData data = new SelectionData();
        data.text = text.trim();
        data.start = Math.max(0, start);
        data.end = Math.max(data.start, end);
        currentSelection = data;
        showSelectionBar();
    }''')

reader = replace_method(reader, '    private void completePageReady()', r'''    private void completePageReady() {
        emptyChapterSkipCount = 0;
        jumpToPendingTocFragment(() -> {
            if (paperGestureChapterBoundary && paperGestureReleased && paperGestureCommit) {
                finishInteractiveChapterBoundary();
                return;
            }
            if (finishPendingChapterCurl()) return;
            pageTurnLocked = false;
            chapterLoading = false;
            finishChapterFade();
        });
    }''')

reader = replace_method(reader, '    private boolean handlePaperGesture(MotionEvent event)', r'''    private boolean handlePaperGesture(MotionEvent event) {
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
                int earlySlop = Math.max(dp(4), Math.max(1, pageTouchSlop / 2));
                if (Math.abs(dx) < earlySlop) return false;
                if (Math.abs(dx) < Math.abs(dy) * 1.22f) {
                    resetPaperGestureState();
                    return false;
                }

                int direction = dx < 0f ? 1 : -1;
                int targetPage = currentPageInChapter + direction;
                cancelNativeSelectionForPaperGesture(event);

                if (targetPage < 1 || targetPage > pageCountInChapter) {
                    int targetSpine = currentSpine + direction;
                    if (targetSpine < 0 || targetSpine >= spine.size() ||
                            !beginInteractiveChapterBoundary(direction)) {
                        resetPaperGestureState();
                        return true;
                    }
                    paperGestureChapterBoundary = true;
                } else if (!beginInteractivePaperTurn(direction, targetPage - 1)) {
                    resetPaperGestureState();
                    return true;
                }
                paperGestureActive = true;
            }

            float width = Math.max(1f, webView.getWidth());
            paperProgress = Math.max(0f, Math.min(1f, Math.abs(dx) / (width * 0.965f)));
            paperTouchY = webView.getHeight() <= 0 ? 0.5f :
                    Math.max(0.07f, Math.min(0.93f, event.getY() / (float) webView.getHeight()));
            if (paperGestureReady && pageCurlView != null)
                pageCurlView.updateInteractive(paperProgress, paperTouchY);
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
            float projected = paperProgress + towardTurn * 0.13f;
            boolean commit = action != MotionEvent.ACTION_CANCEL &&
                    (projected >= 0.37f || towardTurn > 0.52f);

            paperGestureCommit = commit;
            paperGestureReleased = true;
            recyclePageVelocityTracker();

            if (paperGestureChapterBoundary) {
                if (commit) commitInteractiveChapterBoundary();
                else cancelInteractiveChapterBoundary();
            } else if (paperGestureReady) {
                settlePaperGesture();
            }
            return true;
        }
        return paperGestureActive;
    }''')

reader = replace_method(reader, '    private void resetPaperGestureState()', r'''    private void resetPaperGestureState() {
        recyclePageVelocityTracker();
        paperGestureCandidate = false;
        paperGestureActive = false;
        paperGestureReady = false;
        paperGestureReleased = false;
        paperGestureCommit = false;
        paperGestureChapterBoundary = false;
        paperGestureDirection = 0;
        paperProgress = 0f;
        paperReleaseVelocityX = 0f;
        paperTouchY = 0.5f;
        if (webView != null) webView.setLongClickable(true);
    }''')

reader = replace_method(reader, '    private void turnPage(int delta)', r'''    private void turnPage(int delta) {
        if (webView == null || chapterLoading || !"page".equals(readingMode) || delta == 0) return;
        long now = System.currentTimeMillis();
        if (pageTurnLocked || now - lastPageTurnMs < 220L) return;

        lastPageTurnMs = now;
        int direction = delta < 0 ? -1 : 1;
        int targetPage = currentPageInChapter + direction;
        boolean insideChapter = targetPage >= 1 && targetPage <= pageCountInChapter;

        if (!insideChapter) {
            navigateChapter(direction, direction < 0);
            return;
        }
        if ("paper".equals(pageAnimation) && pageCurlView != null)
            startNativePageCurl(direction, targetPage - 1);
        else
            performJsPageTurn(direction);
    }''')

reader = replace_method(reader, '    private void hideControls()', r'''    private void hideControls() {
        controlsVisible = false;
        if (topBar != null && topBar.getVisibility() == View.VISIBLE) {
            topBar.animate().cancel();
            topBar.animate().alpha(0f).translationY(-dp(14)).setDuration(145L)
                    .withEndAction(() -> { topBar.setVisibility(View.GONE); topBar.setAlpha(1f); topBar.setTranslationY(0f); }).start();
        }
        if (bottomBar != null && bottomBar.getVisibility() == View.VISIBLE) {
            bottomBar.animate().cancel();
            bottomBar.animate().alpha(0f).translationY(dp(14)).setDuration(145L)
                    .withEndAction(() -> { bottomBar.setVisibility(View.GONE); bottomBar.setAlpha(1f); bottomBar.setTranslationY(0f); }).start();
        }
    }''')

reader = replace_method(reader, '    private void showControls()', r'''    private void showControls() {
        controlsVisible = true;
        if (topBar != null) {
            topBar.animate().cancel();
            topBar.setVisibility(View.VISIBLE);
            topBar.setAlpha(0f);
            topBar.setTranslationY(-dp(10));
            topBar.animate().alpha(1f).translationY(0f).setDuration(175L).start();
        }
        if (bottomBar != null) {
            bottomBar.animate().cancel();
            bottomBar.setVisibility(View.VISIBLE);
            bottomBar.setAlpha(0f);
            bottomBar.setTranslationY(dp(10));
            bottomBar.animate().alpha(1f).translationY(0f).setDuration(175L).start();
        }
        enterImmersive();
    }''')

reader = replace_method(reader, '    private void updateChromeTheme()', r'''    private void updateChromeTheme() {
        int solid;
        int fg;
        int glass;
        int stroke;
        if (isPdf) {
            solid = Color.WHITE;
            fg = Color.rgb(32, 33, 36);
            glass = Color.argb(238, 255, 255, 255);
            stroke = Color.argb(82, 210, 214, 220);
        } else if (readerTheme == 2) {
            solid = Color.rgb(18, 18, 18);
            fg = Color.rgb(240, 242, 246);
            glass = Color.argb(232, 28, 29, 33);
            stroke = Color.argb(56, 255, 255, 255);
        } else if (readerTheme == 1) {
            solid = Color.rgb(244, 236, 216);
            fg = Color.rgb(32, 33, 36);
            glass = Color.argb(238, 250, 244, 228);
            stroke = Color.argb(92, 168, 153, 126);
        } else {
            solid = Color.WHITE;
            fg = Color.rgb(32, 33, 36);
            glass = Color.argb(238, 255, 255, 255);
            stroke = Color.argb(74, 175, 181, 193);
        }
        if (topBar != null) {
            topBar.setBackground(glassPanel(glass, dp(19), stroke));
            tintChromeChildren(topBar, fg);
        }
        if (bottomBar != null) {
            bottomBar.setBackground(glassPanel(glass, dp(19), stroke));
            tintChromeChildren(bottomBar, fg);
        }
        if (titleView != null) titleView.setTextColor(fg);
        if (positionView != null) positionView.setTextColor(fg);
        if (root != null) root.setBackgroundColor(solid);
        if (webView != null) webView.setBackgroundColor(solid);
    }''')

helpers = r'''
    private boolean suppressingSelectionForPaperGesture() {
        return paperGestureActive || (paperGestureCandidate && pageTurnLocked && paperGestureDirection != 0);
    }

    private void cancelNativeSelectionForPaperGesture(MotionEvent source) {
        if (webView == null) return;
        currentSelection = null;
        hideSelectionBar();
        webView.cancelLongPress();
        webView.setLongClickable(false);
        clearWebSelection();
        try {
            MotionEvent cancel = MotionEvent.obtain(source);
            cancel.setAction(MotionEvent.ACTION_CANCEL);
            webView.onTouchEvent(cancel);
            cancel.recycle();
        } catch (Exception ignored) {}
    }

    private boolean beginInteractiveChapterBoundary(int direction) {
        if (pageCurlView == null || webView == null) return false;
        Bitmap current = captureWebViewBitmap();
        if (current == null) return false;
        Bitmap under;
        try {
            under = Bitmap.createBitmap(current.getWidth(), current.getHeight(), Bitmap.Config.ARGB_8888);
            under.eraseColor(readerTheme == 2 ? Color.rgb(18, 18, 18) :
                    (readerTheme == 1 ? Color.rgb(244, 236, 216) : Color.WHITE));
        } catch (Throwable e) {
            current.recycle();
            return false;
        }
        paperGestureDirection = direction < 0 ? -1 : 1;
        paperOriginalPageZero = Math.max(0, currentPageInChapter - 1);
        paperGestureReady = true;
        paperGestureReleased = false;
        paperGestureCommit = false;
        pageTurnLocked = true;
        lastPageTurnMs = System.currentTimeMillis();
        pageCurlView.hold(current);
        pageCurlView.beginInteractive(under, paperGestureDirection, paperProgress, paperTouchY);
        return true;
    }

    private void cancelInteractiveChapterBoundary() {
        if (pageCurlView == null) {
            pageTurnLocked = false;
            resetPaperGestureState();
            return;
        }
        pageCurlView.settleInteractive(false, paperReleaseVelocityX, () -> {
            pageCurlView.release();
            pageTurnLocked = false;
            resetPaperGestureState();
        });
    }

    private void commitInteractiveChapterBoundary() {
        int target = currentSpine + (paperGestureDirection < 0 ? -1 : 1);
        if (target < 0 || target >= spine.size()) {
            cancelInteractiveChapterBoundary();
            return;
        }
        pendingChapterCurlDirection = paperGestureDirection;
        chapterLoading = true;
        pageTurnLocked = true;
        currentSpine = target;
        currentProgressPermille = paperGestureDirection < 0 ? 1000 : 0;
        saveEpubStateOnly();
        loadCurrentEpubChapter();
    }

    private void finishInteractiveChapterBoundary() {
        if (pageCurlView == null) {
            pendingChapterCurlDirection = 0;
            chapterLoading = false;
            pageTurnLocked = false;
            resetPaperGestureState();
            return;
        }
        Bitmap target = captureWebViewBitmap();
        if (target == null) {
            pageCurlView.release();
            pendingChapterCurlDirection = 0;
            chapterLoading = false;
            pageTurnLocked = false;
            resetPaperGestureState();
            return;
        }
        pendingChapterCurlDirection = 0;
        pageCurlView.replaceTarget(target);
        pageCurlView.settleInteractive(true, paperReleaseVelocityX, () -> {
            chapterLoading = false;
            finishNativePageCurl();
        });
    }

    private void tintChromeChildren(ViewGroup group, int color) {
        if (group == null) return;
        for (int i = 0; i < group.getChildCount(); i++) {
            View child = group.getChildAt(i);
            if (child instanceof TextView) ((TextView) child).setTextColor(color);
            else if (child instanceof ViewGroup) tintChromeChildren((ViewGroup) child, color);
        }
    }

'''
if '    private boolean suppressingSelectionForPaperGesture()' not in reader:
    marker = '    private boolean beginInteractivePaperTurn(int direction, int targetZeroBased)'
    if marker not in reader: raise SystemExit('missing interactive marker')
    reader = reader.replace(marker, helpers + marker, 1)

old_top = '''        FrameLayout.LayoutParams topLp = new FrameLayout.LayoutParams(\n                ViewGroup.LayoutParams.MATCH_PARENT, dp(60), Gravity.TOP);\n        root.addView(topBar, topLp);'''
new_top = '''        FrameLayout.LayoutParams topLp = new FrameLayout.LayoutParams(\n                ViewGroup.LayoutParams.MATCH_PARENT, dp(58), Gravity.TOP);\n        topLp.leftMargin = dp(10);\n        topLp.rightMargin = dp(10);\n        topLp.topMargin = dp(8);\n        root.addView(topBar, topLp);'''
if old_top in reader: reader = reader.replace(old_top, new_top, 1)
else: raise SystemExit('missing top bar layout anchor')
old_bottom = '''        FrameLayout.LayoutParams bottomLp = new FrameLayout.LayoutParams(\n                ViewGroup.LayoutParams.MATCH_PARENT, dp(58), Gravity.BOTTOM);\n        root.addView(bottomBar, bottomLp);'''
new_bottom = '''        FrameLayout.LayoutParams bottomLp = new FrameLayout.LayoutParams(\n                ViewGroup.LayoutParams.MATCH_PARENT, dp(54), Gravity.BOTTOM);\n        bottomLp.leftMargin = dp(34);\n        bottomLp.rightMargin = dp(34);\n        bottomLp.bottomMargin = dp(12);\n        root.addView(bottomBar, bottomLp);'''
if old_bottom in reader: reader = reader.replace(old_bottom, new_bottom, 1)
else: raise SystemExit('missing bottom bar layout anchor')
reader = reader.replace('        return "Natural paper";', '        return "3D page curl";')
reader_path.write_text(reader)


curl_path = Path('app/src/main/java/com/whisper/wowreader/PageCurlView.java')
curl = curl_path.read_text()
if '    void replaceTarget(Bitmap target)' not in curl:
    anchor = '''    void updateInteractive(float progress, float touchY) {\n        if (fromBitmap == null || toBitmap == null || animator != null) return;\n        this.progress = clamp(progress, 0f, 1f);\n        this.touchY = clamp(touchY, 0.08f, 0.92f);\n        invalidate();\n    }\n'''
    replacement = '''    void updateInteractive(float progress, float touchY) {\n        if (fromBitmap == null || toBitmap == null || animator != null) return;\n        this.progress = clamp(progress, 0f, 1f);\n        this.touchY = clamp(touchY, 0.07f, 0.93f);\n        postInvalidateOnAnimation();\n    }\n\n    void replaceTarget(Bitmap target) {\n        if (target == null) return;\n        if (toBitmap != null && toBitmap != fromBitmap && !toBitmap.isRecycled()) toBitmap.recycle();\n        toBitmap = target;\n        postInvalidateOnAnimation();\n    }\n'''
    if anchor not in curl: raise SystemExit('missing curl update anchor')
    curl = curl.replace(anchor, replacement, 1)
curl = curl.replace('        this.touchY = clamp(touchY, 0.08f, 0.92f);', '        this.touchY = clamp(touchY, 0.07f, 0.93f);')
curl = curl.replace('            progress = (float) a.getAnimatedValue();\n            invalidate();', '            progress = (float) a.getAnimatedValue();\n            postInvalidateOnAnimation();')
curl_path.write_text(curl)


build_path = Path('app/build.gradle')
build = build_path.read_text()
build = build.replace('versionCode 17', 'versionCode 18').replace("versionName '2.5.0'", "versionName '2.6.0'")
if "androidx.recyclerview:recyclerview" not in build:
    build = build.replace('dependencies {\n}', "dependencies {\n    implementation 'androidx.recyclerview:recyclerview:1.3.2'\n}")
build_path.write_text(build)

print('Applied WoW Reader v2.6 professional UX refresh')
