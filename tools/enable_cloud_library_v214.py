from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAIN = ROOT / "app/src/main/java/com/whisper/wowreader/MainActivity.java"
BUILD = ROOT / "app/build.gradle"
CI = ROOT / ".github/workflows/build-apk.yml"
README = ROOT / "README.md"


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected exactly one match, found {count}")
    return text.replace(old, new, 1)


main = MAIN.read_text(encoding="utf-8")

main = replace_once(
    main,
    "    private long lastAutoSyncAttemptMs = 0L;\n",
    "    private long lastAutoSyncAttemptMs = 0L;\n    private Runnable googleSyncRetryRunnable;\n",
    "google sync retry field",
)

main = replace_once(
    main,
    "        // Google account / Drive sync is intentionally deferred for a later release.\n",
    "        googleDrive = new GoogleDriveSync(this);\n        restoreStoredGoogleProfile();\n",
    "google drive initialization",
)

main = replace_once(
    main,
    "    @Override protected void onResume() {\n        super.onResume();\n        if (libraryRecycler != null) refreshLibrary();\n    }\n",
    "    @Override protected void onResume() {\n        super.onResume();\n        if (libraryRecycler != null) refreshLibrary();\n        maybeAutoGoogleSync();\n    }\n",
    "resume auto sync",
)

main = replace_once(
    main,
    "        brandRow.addView(brandCopy, new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f));\n\n        themeButton = iconButton(\"navy\".equals(appTheme) ? \"✦\" : \"◐\");\n",
    "        brandRow.addView(brandCopy, new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f));\n\n        accountButton = iconButton(\"G\");\n        accountButton.setTextSize(15);\n        accountButton.setTypeface(Typeface.DEFAULT, Typeface.BOLD);\n        accountButton.setContentDescription(\"Google account & cloud library\");\n        accountButton.setOnClickListener(v -> showAccountMenu());\n        brandRow.addView(accountButton, new LinearLayout.LayoutParams(dp(44), dp(44)));\n        updateAccountButton();\n\n        themeButton = iconButton(\"navy\".equals(appTheme) ? \"✦\" : \"◐\");\n",
    "account button",
)

main = replace_once(
    main,
    "    private void performGoogleBackup(boolean showToast){\n        if(googleSyncBusy)return;\n        googleSyncBusy=true;\n",
    "    private void performGoogleBackup(boolean showToast){\n        if(googleSyncBusy){scheduleGoogleSyncRetry(12000L);return;}\n        googleSyncBusy=true;\n        final long requestedChangeMs=prefs.getLong(\"sync_updated_ms\",0L);\n",
    "backup generation capture",
)

main = replace_once(
    main,
    "                    @Override public void onSuccess(String message){googleSyncBusy=false;if(showToast)Toast.makeText(MainActivity.this,message,Toast.LENGTH_LONG).show();}\n",
    "                    @Override public void onSuccess(String message){prefs.edit().putLong(\"google_last_synced_change_ms\",requestedChangeMs).apply();googleSyncBusy=false;if(showToast)Toast.makeText(MainActivity.this,message,Toast.LENGTH_LONG).show();maybeAutoGoogleSync();}\n",
    "backup completion tracking",
)

old_auto = '''    private void maybeAutoGoogleSync(){\n        if(prefs==null||googleDrive==null||googleSyncBusy)return;\n        if(!prefs.getBoolean("google_sync_connected",false)||!prefs.getBoolean("google_sync_enabled",true))return;\n        long changed=prefs.getLong("sync_updated_ms",0L),backed=prefs.getLong("google_last_backup_ms",0L),now=System.currentTimeMillis();\n        if(changed<=backed||now-lastAutoSyncAttemptMs<45000L)return;\n        lastAutoSyncAttemptMs=now;\n        performGoogleBackup(false);\n    }\n'''
new_auto = '''    private void maybeAutoGoogleSync(){\n        if(prefs==null||googleDrive==null)return;\n        if(!prefs.getBoolean("google_sync_connected",false)||!prefs.getBoolean("google_sync_enabled",true))return;\n        long changed=prefs.getLong("sync_updated_ms",0L);\n        long synced=prefs.getLong("google_last_synced_change_ms",prefs.getLong("google_last_backup_ms",0L));\n        if(changed<=synced)return;\n        if(googleSyncBusy){scheduleGoogleSyncRetry(12000L);return;}\n        long now=System.currentTimeMillis();\n        long remaining=12000L-(now-lastAutoSyncAttemptMs);\n        if(remaining>0L){scheduleGoogleSyncRetry(remaining);return;}\n        lastAutoSyncAttemptMs=now;\n        performGoogleBackup(false);\n    }\n\n    private void scheduleGoogleSyncRetry(long delayMs){\n        if(libraryRecycler==null)return;\n        if(googleSyncRetryRunnable!=null)libraryRecycler.removeCallbacks(googleSyncRetryRunnable);\n        googleSyncRetryRunnable=()->{googleSyncRetryRunnable=null;maybeAutoGoogleSync();};\n        libraryRecycler.postDelayed(googleSyncRetryRunnable,Math.max(1500L,delayMs));\n    }\n'''
main = replace_once(main, old_auto, new_auto, "reliable auto sync")

main = replace_once(
    main,
    '.remove("google_account_email").remove("google_account_picture").apply();',
    '.remove("google_account_email").remove("google_account_picture").remove("google_last_synced_change_ms").apply();',
    "disconnect sync generation cleanup",
)

MAIN.write_text(main, encoding="utf-8")

build = BUILD.read_text(encoding="utf-8")
build = replace_once(build, "versionCode 25", "versionCode 26", "version code")
build = replace_once(build, "versionName '2.13.0'", "versionName '2.14.0'", "version name")
BUILD.write_text(build, encoding="utf-8")

ci = CI.read_text(encoding="utf-8")
ci = ci.replace("Build WoW Reader v2.13 APK", "Build WoW Reader v2.14 APK")
ci = ci.replace('grep -q "versionCode 25" app/build.gradle', 'grep -q "versionCode 26" app/build.gradle')
ci = ci.replace('grep -q "versionName \'2.13.0\'" app/build.gradle', 'grep -q "versionName \'2.14.0\'" app/build.gradle')
ci = ci.replace('! grep -q \'accountButton = iconButton("G")\' "$MAIN"', 'grep -q \'accountButton = iconButton("G")\' "$MAIN"\n          grep -q \'googleDrive = new GoogleDriveSync(this)\' "$MAIN"\n          grep -q \'google_last_synced_change_ms\' "$MAIN"')
ci = ci.replace("versionCode='25'", "versionCode='26'")
ci = ci.replace("versionName='2.13.0'", "versionName='2.14.0'")
ci = ci.replace("WoW-Reader-v2.13.0-unsigned.apk", "WoW-Reader-v2.14.0-unsigned.apk")
ci = ci.replace("name: WoW-Reader-v2.13.0", "name: WoW-Reader-v2.14.0")
CI.write_text(ci, encoding="utf-8")

readme = README.read_text(encoding="utf-8")
readme = readme.replace("Version: **2.4.0**", "Version: **2.14.0**")
readme = readme.replace(
    "Google Account / automatic Google Drive sync is currently disabled.",
    "Google Account cloud library is available: connect a Google account to privately back up books, notes, highlights, custom fonts and reading progress to the app's Google Drive app-data space, then restore them on another device.",
)
if "Google Account cloud library is available" not in readme:
    raise SystemExit("README cloud library update failed")
README.write_text(readme, encoding="utf-8")

print("WoW Reader v2.14 cloud library migration applied")
