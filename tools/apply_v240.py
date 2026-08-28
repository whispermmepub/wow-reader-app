from pathlib import Path

p = Path('app/src/main/java/com/whisper/wowreader/BookReaderActivity.java')
s = p.read_text()

old = '    private static final int SEL_COPY = 9304;\n'
if 'REQ_IMPORT_FONT' not in s:
    assert old in s
    s = s.replace(old, old + '    private static final int REQ_IMPORT_FONT = 9401;\n', 1)

old = '''        String familyCss = "";
        if ("pyidaungsu".equals(fontChoice))
            familyCss = "body,body *{font-family:'WoWPyidaungsu',sans-serif !important;}";
        else if ("yoeshin".equals(fontChoice))
            familyCss = "body,body *{font-family:'WoWYoeShin',sans-serif !important;}";
        else if ("burma2".equals(fontChoice))
            familyCss = "body,body *{font-family:'WoWBurma2',sans-serif !important;}";
'''
new = '''        String familyCss = "";
        if ("pyidaungsu".equals(fontChoice))
            familyCss = "body,body *{font-family:'WoWPyidaungsu',sans-serif !important;}";
        else if ("yoeshin".equals(fontChoice))
            familyCss = "body,body *{font-family:'WoWYoeShin',sans-serif !important;}";
        else if ("burma2".equals(fontChoice))
            familyCss = "body,body *{font-family:'WoWBurma2',sans-serif !important;}";
        else if ("burma001".equals(fontChoice))
            familyCss = "body,body *{font-family:'WoWBurma001',sans-serif !important;}";
        else if ("pupu".equals(fontChoice))
            familyCss = "body,body *{font-family:'WoWPuPu',sans-serif !important;}";
        else if ("ayar".equals(fontChoice))
            familyCss = "body,body *{font-family:'WoWMyanmarAyar',sans-serif !important;}";
        else if ("phantee".equals(fontChoice))
            familyCss = "body,body *{font-family:'WoWPhantee',sans-serif !important;}";
        else if (fontChoice != null && fontChoice.startsWith("custom:")) {
            File customFont = ReaderFontStore.fileForChoice(this, fontChoice);
            if (customFont != null) {
                String customUrl = Uri.fromFile(customFont).toString().replace("'", "%27");
                familyCss = "@font-face{font-family:'WoWCustom';src:url('" + customUrl + "') format('" +
                        ReaderFontStore.cssFormat(customFont) + "');font-display:block;}" +
                        "body,body *{font-family:'WoWCustom',sans-serif !important;}";
            } else {
                fontChoice = "publisher";
            }
        }
'''
if 'WoWBurma001' not in s:
    assert old in s
    s = s.replace(old, new, 1)

old = '''                "@font-face{font-family:'WoWPyidaungsu';src:url('file:///android_asset/fonts/pyidaungsu.woff2') format('woff2');}" +
                "@font-face{font-family:'WoWYoeShin';src:url('file:///android_asset/fonts/yoeshin.woff2') format('woff2');}" +
                "@font-face{font-family:'WoWBurma2';src:url('file:///android_asset/fonts/burma2.woff2') format('woff2');}" +
'''
new = '''                "@font-face{font-family:'WoWPyidaungsu';src:url('file:///android_asset/fonts/pyidaungsu.woff2') format('woff2');font-display:block;}" +
                "@font-face{font-family:'WoWYoeShin';src:url('file:///android_asset/fonts/yoeshin.woff2') format('woff2');font-display:block;}" +
                "@font-face{font-family:'WoWBurma2';src:url('file:///android_asset/fonts/burma2.woff2') format('woff2');font-display:block;}" +
                "@font-face{font-family:'WoWBurma001';src:url('file:///android_asset/fonts/burma001.ttf') format('truetype');font-display:block;}" +
                "@font-face{font-family:'WoWPuPu';src:url('file:///android_asset/fonts/m01_pupu_bold.ttf') format('truetype');font-display:block;}" +
                "@font-face{font-family:'WoWMyanmarAyar';src:url('file:///android_asset/fonts/myanmar_ayar_typewriter.ttf') format('truetype');font-display:block;}" +
                "@font-face{font-family:'WoWPhantee';src:url('file:///android_asset/fonts/phantee_hand_written.ttf') format('truetype');font-display:block;}" +
'''
if "myanmar_ayar_typewriter.ttf" not in s:
    assert old in s
    s = s.replace(old, new, 1)

start = s.index('    private void showFontDialog() {')
end = s.index('    private void showLineSpacingDialog() {', start)
font_methods = r'''    private void showFontDialog() {
        List<ReaderFontStore.FontEntry> custom = ReaderFontStore.list(this);
        List<String> labels = new ArrayList<>();
        List<String> ids = new ArrayList<>();

        labels.add("Publisher font (EPUB original)"); ids.add("publisher");
        labels.add("Pyidaungsu"); ids.add("pyidaungsu");
        labels.add("A10 YoeShin"); ids.add("yoeshin");
        labels.add("Burma2"); ids.add("burma2");
        labels.add("Burma001"); ids.add("burma001");
        labels.add("M01 PuPu Bold"); ids.add("pupu");
        labels.add("Myanmar Ayar Typewriter"); ids.add("ayar");
        labels.add("Phantee Hand Written"); ids.add("phantee");

        for (ReaderFontStore.FontEntry f : custom) {
            labels.add("My font · " + f.label);
            ids.add(f.id);
        }
        labels.add("＋ Import custom font…"); ids.add("__import__");
        if (!custom.isEmpty()) {
            labels.add("Manage custom fonts…"); ids.add("__manage__");
        }

        int selected = -1;
        for (int i = 0; i < ids.size(); i++) if (ids.get(i).equals(fontChoice)) selected = i;

        new AlertDialog.Builder(this)
                .setTitle("Font")
                .setSingleChoiceItems(labels.toArray(new String[0]), selected, (dialog, which) -> {
                    String id = ids.get(which);
                    dialog.dismiss();
                    if ("__import__".equals(id)) pickCustomFont();
                    else if ("__manage__".equals(id)) showManageCustomFonts();
                    else {
                        fontChoice = id;
                        saveReaderPreferences();
                        applyReaderStyle(true);
                    }
                })
                .setNegativeButton("Cancel", null)
                .show();
    }

    private void pickCustomFont() {
        Intent pick = new Intent(Intent.ACTION_OPEN_DOCUMENT);
        pick.addCategory(Intent.CATEGORY_OPENABLE);
        pick.setType("*/*");
        pick.putExtra(Intent.EXTRA_MIME_TYPES, new String[]{
                "font/ttf", "font/otf", "font/woff", "font/woff2",
                "application/x-font-ttf", "application/x-font-opentype",
                "application/font-woff", "application/octet-stream"
        });
        try {
            startActivityForResult(pick, REQ_IMPORT_FONT);
        } catch (Exception e) {
            Toast.makeText(this, "No file picker available", Toast.LENGTH_SHORT).show();
        }
    }

    private void showManageCustomFonts() {
        List<ReaderFontStore.FontEntry> fonts = ReaderFontStore.list(this);
        if (fonts.isEmpty()) {
            Toast.makeText(this, "No custom fonts imported", Toast.LENGTH_SHORT).show();
            return;
        }
        String[] labels = new String[fonts.size()];
        for (int i = 0; i < fonts.size(); i++) labels[i] = fonts.get(i).label;
        new AlertDialog.Builder(this)
                .setTitle("Custom fonts · tap to remove")
                .setItems(labels, (dialog, which) -> {
                    ReaderFontStore.FontEntry target = fonts.get(which);
                    new AlertDialog.Builder(this)
                            .setTitle("Remove font?")
                            .setMessage(target.label)
                            .setNegativeButton("Cancel", null)
                            .setPositiveButton("Remove", (d, w) -> {
                                boolean wasSelected = target.id.equals(fontChoice);
                                if (ReaderFontStore.delete(this, target.id)) {
                                    if (wasSelected) {
                                        fontChoice = "publisher";
                                        saveReaderPreferences();
                                        applyReaderStyle(true);
                                    }
                                    Toast.makeText(this, "Font removed", Toast.LENGTH_SHORT).show();
                                }
                            }).show();
                })
                .setNegativeButton("Close", null)
                .show();
    }

    @Override
    protected void onActivityResult(int requestCode, int resultCode, Intent data) {
        super.onActivityResult(requestCode, resultCode, data);
        if (requestCode != REQ_IMPORT_FONT || resultCode != RESULT_OK || data == null) return;
        Uri uri = data.getData();
        if (uri == null) return;
        try {
            ReaderFontStore.FontEntry imported = ReaderFontStore.importFont(this, uri);
            fontChoice = imported.id;
            saveReaderPreferences();
            applyReaderStyle(true);
            Toast.makeText(this, "Font added · " + imported.label, Toast.LENGTH_LONG).show();
        } catch (Exception e) {
            Toast.makeText(this, "Font import failed · " + e.getMessage(), Toast.LENGTH_LONG).show();
        }
    }

'''
if 'pickCustomFont()' not in s:
    s = s[:start] + font_methods + s[end:]

start = s.index('    private String fontDisplayName() {')
end = s.index('    private String lineSpacingDisplay() {', start)
replacement = r'''    private String fontDisplayName() {
        if ("pyidaungsu".equals(fontChoice)) return "Pyidaungsu";
        if ("yoeshin".equals(fontChoice)) return "A10 YoeShin";
        if ("burma2".equals(fontChoice)) return "Burma2";
        if ("burma001".equals(fontChoice)) return "Burma001";
        if ("pupu".equals(fontChoice)) return "M01 PuPu Bold";
        if ("ayar".equals(fontChoice)) return "Myanmar Ayar Typewriter";
        if ("phantee".equals(fontChoice)) return "Phantee Hand Written";
        if (fontChoice != null && fontChoice.startsWith("custom:")) {
            String name = ReaderFontStore.displayNameForChoice(this, fontChoice);
            if (name != null) return name;
        }
        return "Publisher";
    }

'''
s = s[:start] + replacement + s[end:]

s = s.replace('String[] labels = {"Paper · default", "Smooth slide", "None"};',
              'String[] labels = {"Natural paper · default", "Smooth slide", "None"};')
s = s.replace('        return "Paper";\n    }\n\n    private String alignmentDisplayName()',
              '        return "Natural paper";\n    }\n\n    private String alignmentDisplayName()')

p.write_text(s)

build = Path('app/build.gradle')
b = build.read_text().replace('versionCode 15', 'versionCode 16').replace("versionName '2.3.0'", "versionName '2.4.0'")
build.write_text(b)

readme = Path('README.md')
if readme.exists():
    r = readme.read_text().replace('Version: **2.3.0**', 'Version: **2.4.0**')
    r = r.replace('- Publisher font plus Pyidaungsu, A10 YoeShin and Burma2',
                  '- Publisher font plus Pyidaungsu, A10 YoeShin, Burma2, Burma001, M01 PuPu, Myanmar Ayar and Phantee\n- Import your own TTF, OTF, WOFF or WOFF2 reader fonts')
    readme.write_text(r)

print('WoW Reader v2.4 source patch applied')
