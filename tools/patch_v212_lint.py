from pathlib import Path
p = Path('app/src/main/java/com/whisper/wowreader/MainActivity.java')
s = p.read_text(encoding='utf-8')
old = '''        authors.sort((a, b) -> {
            int ga = titleScriptGroup(a), gb = titleScriptGroup(b);
            if (ga != gb) return Integer.compare(ga, gb);
            return ga == 0 ? myanmarCollator.compare(a, b) : englishCollator.compare(a, b);
        });
'''
new = '''        java.util.Collections.sort(authors, (a, b) -> {
            int ga = titleScriptGroup(a), gb = titleScriptGroup(b);
            if (ga != gb) return Integer.compare(ga, gb);
            return ga == 0 ? myanmarCollator.compare(a, b) : englishCollator.compare(a, b);
        });
'''
if old not in s:
    raise SystemExit('author sort anchor missing')
p.write_text(s.replace(old, new, 1), encoding='utf-8')
print('Patched author sort for API 23')
