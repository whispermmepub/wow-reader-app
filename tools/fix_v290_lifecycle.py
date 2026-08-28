from pathlib import Path

P = Path('app/src/main/java/com/whisper/wowreader/BookReaderActivity.java')
s = P.read_text(encoding='utf-8')

duplicate = '''    @Override\n    protected void onResume() {\n        super.onResume();\n        View decor = getWindow().getDecorView();\n        decor.postDelayed(this::enterImmersive, 80L);\n    }\n\n    @Override\n    public void onWindowFocusChanged(boolean hasFocus) {\n        super.onWindowFocusChanged(hasFocus);\n        if (hasFocus) getWindow().getDecorView().postDelayed(this::enterImmersive, 55L);\n    }\n\n'''
if s.count(duplicate) != 1:
    raise SystemExit('duplicate v2.9 lifecycle block not found exactly once')
s = s.replace(duplicate, '', 1)

old = '''    @Override\n    public void onWindowFocusChanged(boolean hasFocus) {\n        super.onWindowFocusChanged(hasFocus);\n        if (hasFocus) enterImmersive();\n    }\n\n    @Override\n    protected void onResume() {\n        super.onResume();\n        enterImmersive();\n        applyWindowPreferences();\n    }'''
new = '''    @Override\n    public void onWindowFocusChanged(boolean hasFocus) {\n        super.onWindowFocusChanged(hasFocus);\n        if (hasFocus) getWindow().getDecorView().postDelayed(this::enterImmersive, 55L);\n    }\n\n    @Override\n    protected void onResume() {\n        super.onResume();\n        applyWindowPreferences();\n        getWindow().getDecorView().postDelayed(this::enterImmersive, 80L);\n    }'''
if old not in s:
    raise SystemExit('existing lifecycle anchor not found')
s = s.replace(old, new, 1)
P.write_text(s, encoding='utf-8')
print('v2.9 lifecycle fixed')
