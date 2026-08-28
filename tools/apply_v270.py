from pathlib import Path

MAIN = Path('app/src/main/java/com/whisper/wowreader/MainActivity.java')
GRADLE = Path('app/build.gradle')


def must_replace(text, old, new, label):
    if old not in text:
        raise SystemExit(f'missing anchor: {label}')
    return text.replace(old, new, 1)


def replace_between(text, start, end, new_block, label):
    a = text.find(start)
    if a < 0:
        raise SystemExit(f'missing start: {label}')
    b = text.find(end, a)
    if b < 0:
        raise SystemExit(f'missing end: {label}')
    return text[:a] + new_block + text[b:]


s = MAIN.read_text(encoding='utf-8')

s = must_replace(
    s,
    'import java.util.Locale;\n',
    'import java.text.Collator;\nimport java.util.Locale;\n',
    'collator import')

s = must_replace(
    s,
    '    private String searchQuery = "";\n',
    '''    private String searchQuery = "";\n    private Typeface pyidaungsuTypeface;\n    private TextView sortButton;\n    private String sortMode = "added";\n    private volatile boolean metadataWarmupRunning = false;\n    private final Collator myanmarCollator = Collator.getInstance(new Locale("my", "MM"));\n    private final Collator englishCollator = Collator.getInstance(Locale.ENGLISH);\n''',
    'library sort fields')

s = must_replace(
    s,
    '        prefs = getSharedPreferences("wow_reader", MODE_PRIVATE);\n        gridMode = prefs.getBoolean("library_grid", true);\n',
    '''        prefs = getSharedPreferences("wow_reader", MODE_PRIVATE);\n        gridMode = prefs.getBoolean("library_grid", true);\n        sortMode = prefs.getString("library_sort", "added");\n        if (!"added".equals(sortMode) && !"opened".equals(sortMode) &&\n                !"title_asc".equals(sortMode) && !"title_desc".equals(sortMode))\n            sortMode = "added";\n        myanmarCollator.setStrength(Collator.PRIMARY);\n        englishCollator.setStrength(Collator.PRIMARY);\n        try {\n            pyidaungsuTypeface = Typeface.createFromAsset(getAssets(), "fonts/pyidaungsu_native.ttf");\n        } catch (Exception ignored) {\n            pyidaungsuTypeface = null;\n        }\n''',
    'load library preferences and native font')

s = must_replace(
    s,
    '        libraryRecycler.setItemAnimator(null);\n        libraryRecycler.setPadding(0, 0, 0, dp(96));\n',
    '''        androidx.recyclerview.widget.DefaultItemAnimator itemAnimator = new androidx.recyclerview.widget.DefaultItemAnimator();\n        itemAnimator.setSupportsChangeAnimations(false);\n        itemAnimator.setAddDuration(135L);\n        itemAnimator.setRemoveDuration(110L);\n        itemAnimator.setMoveDuration(170L);\n        libraryRecycler.setItemAnimator(itemAnimator);\n        libraryRecycler.setItemViewCacheSize(12);\n        libraryRecycler.setPadding(0, 0, 0, dp(96));\n''',
    'smooth recycler setup')

refresh_block = '''    private void refreshLibrary() {\n        File[] all = libraryDir.listFiles(file -> file.isFile() && isBook(file.getName()));\n        if (all == null) all = new File[0];\n        sortLibraryFiles(all);\n\n        visibleBooks.clear();\n        for (File f : all) {\n            String cachedTitle = cachedLibraryTitle(f).toLowerCase(Locale.ROOT);\n            String fileTitle = stripExtension(f.getName()).toLowerCase(Locale.ROOT);\n            if (searchQuery.isEmpty() || cachedTitle.contains(searchQuery) || fileTitle.contains(searchQuery))\n                visibleBooks.add(f);\n        }\n        if (libraryAdapter != null) libraryAdapter.submit(visibleBooks);\n        if (countView != null) countView.setText(visibleBooks.size() + (visibleBooks.size() == 1 ? " book" : " books"));\n        if (sortButton != null) sortButton.setText(sortButtonLabel());\n\n        if (isAlphabeticalSort()) warmSortMetadataIfNeeded(all);\n    }\n\n    private void sortLibraryFiles(File[] files) {\n        if (files == null || files.length < 2) return;\n        Arrays.sort(files, (a, b) -> {\n            if ("title_asc".equals(sortMode)) return compareBookTitles(a, b);\n            if ("title_desc".equals(sortMode)) return -compareBookTitles(a, b);\n            if ("opened".equals(sortMode)) {\n                int c = Long.compare(openedTime(b), openedTime(a));\n                return c != 0 ? c : compareBookTitles(a, b);\n            }\n            int c = Long.compare(addedTime(b), addedTime(a));\n            return c != 0 ? c : compareBookTitles(a, b);\n        });\n    }\n\n    private long addedTime(File file) {\n        return prefs.getLong("added_at_" + file.getName(), file.lastModified());\n    }\n\n    private long openedTime(File file) {\n        return prefs.getLong("last_opened_" + file.getName(), 0L);\n    }\n\n    private boolean isAlphabeticalSort() {\n        return "title_asc".equals(sortMode) || "title_desc".equals(sortMode);\n    }\n\n    private String cachedLibraryTitle(File file) {\n        String fallback = stripExtension(file.getName());\n        String value = prefs.getString("library_title_" + file.getName(), fallback);\n        return value == null || value.trim().isEmpty() ? fallback : value.trim();\n    }\n\n    private int compareBookTitles(File a, File b) {\n        String ta = normalizeSortTitle(cachedLibraryTitle(a));\n        String tb = normalizeSortTitle(cachedLibraryTitle(b));\n        int ga = titleScriptGroup(ta);\n        int gb = titleScriptGroup(tb);\n        if (ga != gb) return Integer.compare(ga, gb);\n        int c;\n        if (ga == 0) c = myanmarCollator.compare(ta, tb);\n        else c = englishCollator.compare(ta, tb);\n        if (c != 0) return c;\n        return ta.compareToIgnoreCase(tb);\n    }\n\n    private String normalizeSortTitle(String value) {\n        if (value == null) return "";\n        String s = value.trim();\n        int offset = 0;\n        while (offset < s.length()) {\n            int cp = s.codePointAt(offset);\n            if (Character.isLetterOrDigit(cp) || isMyanmarCodePoint(cp)) break;\n            offset += Character.charCount(cp);\n        }\n        return offset >= s.length() ? s : s.substring(offset);\n    }\n\n    private int titleScriptGroup(String value) {\n        if (value == null || value.isEmpty()) return 3;\n        for (int i = 0; i < value.length();) {\n            int cp = value.codePointAt(i);\n            if (isMyanmarCodePoint(cp)) return 0;\n            if ((cp >= 'A' && cp <= 'Z') || (cp >= 'a' && cp <= 'z')) return 1;\n            if (Character.isDigit(cp)) return 2;\n            if (Character.isLetter(cp)) return 2;\n            i += Character.charCount(cp);\n        }\n        return 3;\n    }\n\n    private boolean isMyanmarCodePoint(int cp) {\n        return (cp >= 0x1000 && cp <= 0x109F) ||\n                (cp >= 0xA9E0 && cp <= 0xA9FF) ||\n                (cp >= 0xAA60 && cp <= 0xAA7F);\n    }\n\n    private void warmSortMetadataIfNeeded(File[] files) {\n        if (metadataWarmupRunning || files == null || files.length == 0) return;\n        boolean missing = false;\n        for (File f : files) {\n            if (f.getName().toLowerCase(Locale.ROOT).endsWith(".epub") &&\n                    !prefs.contains("library_title_" + f.getName())) {\n                missing = true;\n                break;\n            }\n        }\n        if (!missing) return;\n        metadataWarmupRunning = true;\n        final File[] snapshot = files.clone();\n        new Thread(() -> {\n            SharedPreferences.Editor edit = prefs.edit();\n            boolean changed = false;\n            for (File f : snapshot) {\n                if (!f.getName().toLowerCase(Locale.ROOT).endsWith(".epub") ||\n                        prefs.contains("library_title_" + f.getName())) continue;\n                String title = stripExtension(f.getName());\n                try {\n                    EpubUtil.Summary summary = EpubUtil.extractSummary(f, coverCacheDir);\n                    if (summary.title != null && !summary.title.trim().isEmpty()) title = summary.title.trim();\n                } catch (Exception ignored) {}\n                edit.putString("library_title_" + f.getName(), title);\n                changed = true;\n            }\n            edit.apply();\n            final boolean shouldRefresh = changed;\n            runOnUiThread(() -> {\n                metadataWarmupRunning = false;\n                if (shouldRefresh && isAlphabeticalSort()) refreshLibrary();\n            });\n        }, "wow-library-metadata").start();\n    }\n\n'''
s = replace_between(s, '    private void refreshLibrary() {', '    private void addGrid(List<File> files) {', refresh_block, 'refresh and sorting')

# Native Pyidaungsu for displayed book titles.
s = s.replace('        title.setTypeface(Typeface.DEFAULT, Typeface.BOLD);', '        applyBookTitleTypeface(title);')

section_block = '''    private View buildLibrarySectionHeader() {\n        LinearLayout row = new LinearLayout(this);\n        row.setOrientation(LinearLayout.HORIZONTAL);\n        row.setGravity(Gravity.CENTER_VERTICAL);\n        row.setPadding(dp(20), dp(7), dp(16), dp(9));\n\n        LinearLayout copy = new LinearLayout(this);\n        copy.setOrientation(LinearLayout.VERTICAL);\n        copy.setGravity(Gravity.CENTER_VERTICAL);\n        TextView label = new TextView(this);\n        label.setText("Library");\n        label.setTextSize(18);\n        label.setTextColor(Color.rgb(31, 34, 40));\n        label.setTypeface(Typeface.DEFAULT, Typeface.BOLD);\n        copy.addView(label);\n\n        countView = new TextView(this);\n        countView.setTextSize(10.5f);\n        countView.setTextColor(Color.rgb(112, 116, 128));\n        countView.setPadding(0, dp(1), 0, 0);\n        copy.addView(countView);\n        row.addView(copy, new LinearLayout.LayoutParams(0, dp(48), 1f));\n\n        sortButton = new TextView(this);\n        sortButton.setText(sortButtonLabel());\n        sortButton.setTextSize(11.5f);\n        sortButton.setTextColor(Color.rgb(67, 68, 190));\n        sortButton.setTypeface(Typeface.DEFAULT, Typeface.BOLD);\n        sortButton.setGravity(Gravity.CENTER);\n        sortButton.setPadding(dp(12), 0, dp(12), 0);\n        sortButton.setSingleLine(true);\n        sortButton.setBackground(roundRect(Color.argb(220, 255, 255, 255), dp(19), dp(1), Color.argb(72, 126, 126, 210)));\n        sortButton.setElevation(dp(1));\n        sortButton.setOnClickListener(v -> showSortDialog());\n        sortButton.setOnTouchListener((v, e) -> {\n            if (e.getActionMasked() == android.view.MotionEvent.ACTION_DOWN)\n                v.animate().scaleX(0.965f).scaleY(0.965f).setDuration(70L).start();\n            else if (e.getActionMasked() == android.view.MotionEvent.ACTION_UP || e.getActionMasked() == android.view.MotionEvent.ACTION_CANCEL)\n                v.animate().scaleX(1f).scaleY(1f).setDuration(110L).start();\n            return false;\n        });\n        row.addView(sortButton, new LinearLayout.LayoutParams(ViewGroup.LayoutParams.WRAP_CONTENT, dp(38)));\n        return row;\n    }\n\n    private String sortButtonLabel() {\n        if ("opened".equals(sortMode)) return "Recently opened  ▾";\n        if ("title_asc".equals(sortMode)) return "က–အ · A–Z  ▾";\n        if ("title_desc".equals(sortMode)) return "အ–က · Z–A  ▾";\n        return "Recently added  ▾";\n    }\n\n    private void showSortDialog() {\n        String[] labels = {\n                "Recently added",\n                "Recently opened",\n                "Title · က–အ / A–Z",\n                "Title · အ–က / Z–A"\n        };\n        String[] values = {"added", "opened", "title_asc", "title_desc"};\n        int selected = "opened".equals(sortMode) ? 1 :\n                ("title_asc".equals(sortMode) ? 2 : ("title_desc".equals(sortMode) ? 3 : 0));\n        new AlertDialog.Builder(this)\n                .setTitle("Sort library")\n                .setSingleChoiceItems(labels, selected, (dialog, which) -> {\n                    sortMode = values[which];\n                    prefs.edit().putString("library_sort", sortMode).apply();\n                    if (sortButton != null) sortButton.setText(sortButtonLabel());\n                    refreshLibrary();\n                    dialog.dismiss();\n                })\n                .setNegativeButton("Cancel", null)\n                .show();\n    }\n\n'''
s = replace_between(s, '    private View buildLibrarySectionHeader() {', '    private View buildEmptyState() {', section_block, 'section header and sort UI')

# Cache the metadata title whenever a card is loaded.
s = must_replace(
    s,
    '            String ft=title,fa=author; Bitmap fb=bitmap; int progress=prefs.getInt("percent_"+file.getName(),0); runOnUiThread(()->{ if(fb!=null) cover.setImageBitmap(fb); titleView.setText(ft); String type=file.getName().toLowerCase(Locale.ROOT).endsWith(".pdf")?"PDF":"EPUB"; metaView.setText(fa.isEmpty()?type+" · "+progress+"%":fa+" · "+progress+"%"); }); }).start();\n',
    '            prefs.edit().putString("library_title_" + file.getName(), title).apply();\\n            String ft=title,fa=author; Bitmap fb=bitmap; int progress=prefs.getInt("percent_"+file.getName(),0); runOnUiThread(()->{ if(fb!=null) cover.setImageBitmap(fb); titleView.setText(ft); applyBookTitleTypeface(titleView); String type=file.getName().toLowerCase(Locale.ROOT).endsWith(".pdf")?"PDF":"EPUB"; metaView.setText(fa.isEmpty()?type+" · "+progress+"%":fa+" · "+progress+"%"); }); }).start();\n'.replace('\\n', '\n'),
    'cache loaded metadata title')

# Apply Pyidaungsu to placeholder Myanmar/English title initials too.
s = must_replace(
    s,
    'p.setTypeface(Typeface.create(Typeface.DEFAULT,Typeface.BOLD));',
    'p.setTypeface(Typeface.create(pyidaungsuTypeface != null ? pyidaungsuTypeface : Typeface.DEFAULT,Typeface.BOLD));',
    'placeholder typeface')

# Incoming books are always imported to Library and never auto-opened.
s = must_replace(
    s,
    '    private void handleIncomingIntent(Intent intent){ if(intent==null||!Intent.ACTION_VIEW.equals(intent.getAction()))return; Uri data=intent.getData(); if(data!=null) importBook(data,true); }\n',
    '''    private void handleIncomingIntent(Intent intent){\n        if(intent==null)return;\n        Uri data=null;\n        String action=intent.getAction();\n        if(Intent.ACTION_VIEW.equals(action)) data=intent.getData();\n        else if(Intent.ACTION_SEND.equals(action)){\n            try{Object stream=intent.getParcelableExtra(Intent.EXTRA_STREAM);if(stream instanceof Uri)data=(Uri)stream;}catch(Exception ignored){}\n        }\n        if(data!=null){\n            intent.setAction(null);\n            importBook(data,false);\n        }\n    }\n''',
    'incoming import behavior')

# Replace import method to record added time + metadata and never launch reader automatically.
old_import_start = '    private void importBook(Uri uri,boolean openAfter){'
old_import_end = '    private String queryDisplayName(Uri uri)'
new_import = '''    private void importBook(Uri uri,boolean openAfter){\n        new Thread(()->{\n            try{\n                String name=queryDisplayName(uri);\n                if(name==null||name.trim().isEmpty())name="book_"+System.currentTimeMillis();\n                String lower=name.toLowerCase(Locale.ROOT),mime=getContentResolver().getType(uri);\n                if(!lower.endsWith(".epub")&&!lower.endsWith(".pdf")){\n                    if("application/pdf".equals(mime))name+=".pdf";\n                    else if("application/epub+zip".equals(mime))name+=".epub";\n                    else throw new Exception("Only EPUB and PDF files are supported");\n                }\n                File out=uniqueFile(name);\n                try(InputStream in=getContentResolver().openInputStream(uri);OutputStream os=new FileOutputStream(out)){\n                    if(in==null)throw new Exception("Unable to open file");\n                    copy(in,os);\n                }\n                String displayTitle=stripExtension(out.getName());\n                if(out.getName().toLowerCase(Locale.ROOT).endsWith(".epub")){\n                    try{\n                        EpubUtil.Summary summary=EpubUtil.extractSummary(out,coverCacheDir);\n                        if(summary.title!=null&&!summary.title.trim().isEmpty())displayTitle=summary.title.trim();\n                    }catch(Exception ignored){}\n                }\n                prefs.edit()\n                        .putLong("added_at_"+out.getName(),System.currentTimeMillis())\n                        .putString("library_title_"+out.getName(),displayTitle)\n                        .apply();\n                runOnUiThread(()->{\n                    Toast.makeText(this,"Added to Library",Toast.LENGTH_SHORT).show();\n                    refreshLibrary();\n                });\n            }catch(Exception e){\n                runOnUiThread(()->Toast.makeText(this,e.getMessage(),Toast.LENGTH_LONG).show());\n            }\n        },"wow-import-book").start();\n    }\n\n    private void applyBookTitleTypeface(TextView view){\n        if(view==null)return;\n        if(pyidaungsuTypeface!=null)view.setTypeface(pyidaungsuTypeface,Typeface.BOLD);\n        else view.setTypeface(Typeface.DEFAULT,Typeface.BOLD);\n    }\n\n'''
s = replace_between(s, old_import_start, old_import_end, new_import, 'import behavior')

# Store added time during restore, and clear related metadata on delete.
s = must_replace(
    s,
    'if(file.delete()){prefs.edit().remove("percent_"+file.getName()).apply();refreshLibrary();}',
    'if(file.delete()){prefs.edit().remove("percent_"+file.getName()).remove("library_title_"+file.getName()).remove("added_at_"+file.getName()).remove("last_opened_"+file.getName()).apply();refreshLibrary();}',
    'delete metadata cleanup')

s = must_replace(
    s,
    'try(InputStream in=getContentResolver().openInputStream(doc);OutputStream os=new FileOutputStream(out)){if(in!=null){copy(in,os);count++;}}',
    'try(InputStream in=getContentResolver().openInputStream(doc);OutputStream os=new FileOutputStream(out)){if(in!=null){copy(in,os);prefs.edit().putLong("added_at_"+out.getName(),System.currentTimeMillis()).apply();count++;}}',
    'restore added time')

# Softer navigation transition into the reader.
s = must_replace(
    s,
    'private void openBook(File file){prefs.edit().putLong("last_opened_"+file.getName(),System.currentTimeMillis()).apply();Intent i=new Intent(this,BookReaderActivity.class);i.putExtra("path",file.getAbsolutePath());startActivity(i);}',
    'private void openBook(File file){prefs.edit().putLong("last_opened_"+file.getName(),System.currentTimeMillis()).apply();Intent i=new Intent(this,BookReaderActivity.class);i.putExtra("path",file.getAbsolutePath());startActivity(i);overridePendingTransition(android.R.anim.fade_in,android.R.anim.fade_out);}',
    'reader transition')

MAIN.write_text(s, encoding='utf-8')

g = GRADLE.read_text(encoding='utf-8')
g = must_replace(g, 'versionCode 18', 'versionCode 19', 'version code')
g = must_replace(g, "versionName '2.6.0'", "versionName '2.7.0'", 'version name')
GRADLE.write_text(g, encoding='utf-8')

print('Applied WoW Reader v2.7 library typography, sorting, import UX and motion polish')
