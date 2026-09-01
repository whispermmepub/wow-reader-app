from pathlib import Path
p=Path('app/src/main/java/com/whisper/wowreader/BookReaderActivity.java')
s=p.read_text(encoding='utf-8')
old='import java.io.FileInputStream;\nimport java.io.FileOutputStream;'
new='import java.io.FileInputStream;\nimport java.io.FileOutputStream;\nimport java.io.InputStream;'
if old not in s: raise SystemExit('import anchor missing')
p.write_text(s.replace(old,new,1),encoding='utf-8')
