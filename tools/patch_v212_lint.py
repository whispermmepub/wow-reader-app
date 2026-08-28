from pathlib import Path
p = Path('app/src/main/java/com/whisper/wowreader/MainActivity.java')
s = p.read_text(encoding='utf-8')
old = '            counts.put(author, counts.getOrDefault(author, 0) + 1);\n'
new = '            Integer oldCount = counts.get(author);\n            counts.put(author, (oldCount == null ? 0 : oldCount) + 1);\n'
if old not in s:
    raise SystemExit('author count anchor missing')
p.write_text(s.replace(old, new, 1), encoding='utf-8')
print('Patched author counts for API 23')
