from pathlib import Path

path = Path('app/src/main/java/com/whisper/wowreader/MainActivity.java')
text = path.read_text(encoding='utf-8')
old = '''    private void openExternal(String url) {
        try {
            startActivity(new Intent(Intent.ACTION_VIEW, Uri.parse(url)));
        } catch (Exception e) {
            Toast.makeText(this, "Unable to open link", Toast.LENGTH_SHORT).show();
        }
    }
'''
new = '''    private void openExternal(String url) {
        if (url == null || url.trim().isEmpty()) return;

        Uri parsed = Uri.parse(url.trim());
        String host = parsed.getHost();
        if (host != null && (host.equalsIgnoreCase("t.me") || host.equalsIgnoreCase("telegram.me"))) {
            if (openTelegramDeepLink(parsed)) return;
            String alternate = telegramWebFallback(parsed);
            if (alternate != null && openViewIntent(alternate)) return;
        }

        if (!openViewIntent(url))
            Toast.makeText(this, "Unable to open link", Toast.LENGTH_SHORT).show();
    }

    private boolean openTelegramDeepLink(Uri webUri) {
        try {
            String path = webUri.getPath();
            if (path == null) return false;
            String clean = path.startsWith("/") ? path.substring(1) : path;
            if (clean.isEmpty()) return false;

            Uri deepLink;
            if (clean.startsWith("+")) {
                String invite = clean.substring(1);
                if (invite.isEmpty()) return false;
                deepLink = Uri.parse("tg://join?invite=" + Uri.encode(invite));
            } else if (clean.startsWith("joinchat/")) {
                String invite = clean.substring("joinchat/".length());
                if (invite.isEmpty()) return false;
                deepLink = Uri.parse("tg://join?invite=" + Uri.encode(invite));
            } else {
                int slash = clean.indexOf('/');
                String username = slash >= 0 ? clean.substring(0, slash) : clean;
                if (username.isEmpty()) return false;
                deepLink = Uri.parse("tg://resolve?domain=" + Uri.encode(username));
            }

            startActivity(new Intent(Intent.ACTION_VIEW, deepLink));
            return true;
        } catch (Exception ignored) {
            return false;
        }
    }

    private String telegramWebFallback(Uri original) {
        String path = original.getPath();
        if (path == null || path.isEmpty()) return null;
        String clean = path.startsWith("/") ? path.substring(1) : path;
        if (clean.startsWith("+"))
            return "https://telegram.me/joinchat/" + clean.substring(1);
        return "https://telegram.me/" + clean;
    }

    private boolean openViewIntent(String url) {
        try {
            startActivity(new Intent(Intent.ACTION_VIEW, Uri.parse(url)));
            return true;
        } catch (Exception ignored) {
            return false;
        }
    }
'''
if old not in text:
    raise SystemExit('openExternal method did not match expected source')
path.write_text(text.replace(old, new, 1), encoding='utf-8')
