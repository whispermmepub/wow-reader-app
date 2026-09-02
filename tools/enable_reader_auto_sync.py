from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAIN = ROOT / "app/src/main/java/com/whisper/wowreader/MainActivity.java"
READER = ROOT / "app/src/main/java/com/whisper/wowreader/BookReaderActivity.java"
DRIVE = ROOT / "app/src/main/java/com/whisper/wowreader/GoogleDriveSync.java"
AUTO = ROOT / "app/src/main/java/com/whisper/wowreader/GoogleAutoSync.java"


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected exactly one match, found {count}")
    return text.replace(old, new, 1)


auto = r'''package com.whisper.wowreader;

import android.app.Activity;
import android.content.SharedPreferences;
import android.os.Handler;
import android.os.Looper;

import java.io.File;
import java.lang.ref.WeakReference;

/**
 * App-wide, local-first Google Drive auto sync coordinator.
 *
 * Reading data is always saved locally first. Cloud backup is delayed/coalesced so
 * page turns do not continuously rebuild and upload the whole library snapshot.
 */
final class GoogleAutoSync {
    private static final long SOON_DELAY_MS = 8_000L;
    private static final long NORMAL_DELAY_MS = 90_000L;
    private static final long RETRY_DELAY_MS = 120_000L;
    private static final long MIN_ATTEMPT_INTERVAL_MS = 30_000L;

    private static final Handler MAIN = new Handler(Looper.getMainLooper());
    private static WeakReference<Activity> activityRef = new WeakReference<>(null);
    private static Runnable pendingRunnable;
    private static long pendingAtMs = 0L;
    private static boolean busy = false;
    private static long lastAttemptMs = 0L;

    private GoogleAutoSync() {}

    static void schedule(Activity activity) {
        scheduleWithDelay(activity, NORMAL_DELAY_MS);
    }

    static void scheduleSoon(Activity activity) {
        scheduleWithDelay(activity, SOON_DELAY_MS);
    }

    static void flush(Activity activity) {
        if (!needsSync(activity)) return;
        cancelPending();
        long remaining;
        synchronized (GoogleAutoSync.class) {
            if (busy) return;
            remaining = MIN_ATTEMPT_INTERVAL_MS - (System.currentTimeMillis() - lastAttemptMs);
        }
        if (remaining > 0L) scheduleWithDelay(activity, remaining);
        else runSync(activity);
    }

    static synchronized boolean isBusy() {
        return busy;
    }

    static void cancelPending() {
        synchronized (GoogleAutoSync.class) {
            if (pendingRunnable != null) MAIN.removeCallbacks(pendingRunnable);
            pendingRunnable = null;
            pendingAtMs = 0L;
        }
    }

    private static void scheduleWithDelay(Activity activity, long delayMs) {
        if (!needsSync(activity)) return;
        long now = System.currentTimeMillis();
        long due = now + Math.max(1_500L, delayMs);
        synchronized (GoogleAutoSync.class) {
            activityRef = new WeakReference<>(activity);
            if (pendingRunnable != null && pendingAtMs > 0L && pendingAtMs <= due) return;
            if (pendingRunnable != null) MAIN.removeCallbacks(pendingRunnable);
            pendingAtMs = due;
            pendingRunnable = () -> {
                Activity target;
                synchronized (GoogleAutoSync.class) {
                    pendingRunnable = null;
                    pendingAtMs = 0L;
                    target = activityRef.get();
                }
                if (target != null) runSync(target);
            };
            MAIN.postDelayed(pendingRunnable, Math.max(1_500L, delayMs));
        }
    }

    private static boolean needsSync(Activity activity) {
        if (activity == null) return false;
        SharedPreferences prefs = activity.getSharedPreferences("wow_reader", Activity.MODE_PRIVATE);
        if (!prefs.getBoolean("google_sync_connected", false) ||
                !prefs.getBoolean("google_sync_enabled", true)) return false;
        long changed = prefs.getLong("sync_updated_ms", 0L);
        long synced = prefs.getLong("google_last_synced_change_ms",
                prefs.getLong("google_last_backup_ms", 0L));
        return changed > synced;
    }

    private static void runSync(Activity activity) {
        if (!needsSync(activity)) return;
        SharedPreferences prefs = activity.getSharedPreferences("wow_reader", Activity.MODE_PRIVATE);
        long now = System.currentTimeMillis();
        synchronized (GoogleAutoSync.class) {
            if (busy) {
                scheduleWithDelay(activity, SOON_DELAY_MS);
                return;
            }
            long remaining = MIN_ATTEMPT_INTERVAL_MS - (now - lastAttemptMs);
            if (remaining > 0L) {
                scheduleWithDelay(activity, remaining);
                return;
            }
            busy = true;
            lastAttemptMs = now;
        }

        final long requestedChangeMs = prefs.getLong("sync_updated_ms", 0L);
        final GoogleDriveSync drive = new GoogleDriveSync(activity);
        drive.authorizeSilently(new GoogleDriveSync.AuthCallback() {
            @Override public void onReady(GoogleDriveSync.Profile profile) {
                File library = new File(activity.getFilesDir(), "library");
                File fonts = new File(activity.getFilesDir(), "reader_fonts");
                if (!library.exists()) library.mkdirs();
                if (!fonts.exists()) fonts.mkdirs();
                GoogleDriveSync.backup(activity, profile.accessToken, library, fonts, prefs,
                        new GoogleDriveSync.SyncCallback() {
                            @Override public void onSuccess(String message) {
                                prefs.edit().putLong("google_last_synced_change_ms", requestedChangeMs).apply();
                                finish(activity, prefs, requestedChangeMs, true);
                            }

                            @Override public void onError(String message) {
                                finish(activity, prefs, requestedChangeMs, false);
                            }
                        });
            }

            @Override public void onError(String message) {
                finish(activity, prefs, requestedChangeMs, false);
            }
        });
    }

    private static void finish(Activity activity, SharedPreferences prefs,
                               long requestedChangeMs, boolean success) {
        synchronized (GoogleAutoSync.class) {
            busy = false;
        }
        long latest = prefs.getLong("sync_updated_ms", 0L);
        if (success) {
            if (latest > requestedChangeMs) scheduleSoon(activity);
        } else {
            scheduleWithDelay(activity, RETRY_DELAY_MS);
        }
    }
}
'''
AUTO.write_text(auto, encoding="utf-8")

# GoogleDriveSync: add a no-UI authorization path for background auto sync.
drive = DRIVE.read_text(encoding="utf-8")
needle = '''    void authorize(boolean chooseAccount, AuthCallback callback) {\n        AuthorizationRequest.Builder builder = AuthorizationRequest.builder()\n                .setRequestedScopes(SCOPES);\n        if (chooseAccount) builder.setPrompt(AuthorizationRequest.Prompt.SELECT_ACCOUNT);\n        AuthorizationRequest request = builder.build();\n        authorizationClient.authorize(request)\n                .addOnSuccessListener(result -> handleAuthorizationResult(result, callback))\n                .addOnFailureListener(e -> callback.onError(friendly(e)));\n    }\n'''
replacement = needle + '''\n    void authorizeSilently(AuthCallback callback) {\n        AuthorizationRequest request = AuthorizationRequest.builder()\n                .setRequestedScopes(SCOPES)\n                .build();\n        authorizationClient.authorize(request)\n                .addOnSuccessListener(result -> {\n                    if (result != null && result.hasResolution()) {\n                        callback.onError("Google account needs reconnect");\n                        return;\n                    }\n                    handleAuthorizationResult(result, callback);\n                })\n                .addOnFailureListener(e -> callback.onError(friendly(e)));\n    }\n'''
drive = replace_once(drive, needle, replacement, "silent authorization")
DRIVE.write_text(drive, encoding="utf-8")

# MainActivity: all automatic paths use the shared coordinator; manual Sync now remains available.
main = MAIN.read_text(encoding="utf-8")
old_auto = '''    private void maybeAutoGoogleSync(){\n        if(prefs==null||googleDrive==null)return;\n        if(!prefs.getBoolean("google_sync_connected",false)||!prefs.getBoolean("google_sync_enabled",true))return;\n        long changed=prefs.getLong("sync_updated_ms",0L);\n        long synced=prefs.getLong("google_last_synced_change_ms",prefs.getLong("google_last_backup_ms",0L));\n        if(changed<=synced)return;\n        if(googleSyncBusy){scheduleGoogleSyncRetry(12000L);return;}\n        long now=System.currentTimeMillis();\n        long remaining=12000L-(now-lastAutoSyncAttemptMs);\n        if(remaining>0L){scheduleGoogleSyncRetry(remaining);return;}\n        lastAutoSyncAttemptMs=now;\n        performGoogleBackup(false);\n    }\n'''
new_auto = '''    private void maybeAutoGoogleSync(){\n        GoogleAutoSync.scheduleSoon(this);\n    }\n'''
main = replace_once(main, old_auto, new_auto, "main auto sync delegation")

main = replace_once(
    main,
    '''    private void performGoogleBackup(boolean showToast){\n        if(googleSyncBusy){scheduleGoogleSyncRetry(12000L);return;}\n        googleSyncBusy=true;\n''',
    '''    private void performGoogleBackup(boolean showToast){\n        if(GoogleAutoSync.isBusy()){if(showToast)Toast.makeText(this,"Auto sync is already running",Toast.LENGTH_SHORT).show();return;}\n        GoogleAutoSync.cancelPending();\n        if(googleSyncBusy){scheduleGoogleSyncRetry(12000L);return;}\n        googleSyncBusy=true;\n''',
    "manual sync collision guard",
)

main = replace_once(
    main,
    '''                    else if(w==2){prefs.edit().putBoolean("google_sync_enabled",!auto).apply();Toast.makeText(this,"Auto sync "+(!auto?"on":"off"),Toast.LENGTH_SHORT).show();}\n''',
    '''                    else if(w==2){boolean enabled=!auto;prefs.edit().putBoolean("google_sync_enabled",enabled).apply();if(enabled)maybeAutoGoogleSync();else GoogleAutoSync.cancelPending();Toast.makeText(this,"Auto sync "+(enabled?"on":"off"),Toast.LENGTH_SHORT).show();}\n''',
    "auto sync toggle",
)

main = replace_once(
    main,
    '''                        new AlertDialog.Builder(MainActivity.this).setTitle("Google Drive connected")\n                                .setMessage("Auto sync is on. Back up this device now?")\n                                .setNegativeButton("Later",null).setPositiveButton("Back up now",(d,w)->performGoogleBackup(true)).show();\n''',
    '''                        new AlertDialog.Builder(MainActivity.this).setTitle("Google Drive connected")\n                                .setMessage("Auto sync is on. WoW Reader will back up changes automatically while keeping books available offline.")\n                                .setPositiveButton("OK",null).show();\n                        maybeAutoGoogleSync();\n''',
    "connected auto sync message",
)

main = replace_once(
    main,
    '''    private void disconnectGoogleAccount(){\n        GoogleDriveSync.Profile profile=googleProfile;\n''',
    '''    private void disconnectGoogleAccount(){\n        GoogleAutoSync.cancelPending();\n        GoogleDriveSync.Profile profile=googleProfile;\n''',
    "disconnect auto sync cleanup",
)
MAIN.write_text(main, encoding="utf-8")

# ReaderActivity: schedule meaningful changes, retry on resume, and flush latest progress when leaving reader.
reader = READER.read_text(encoding="utf-8")
reader = replace_once(
    reader,
    '''        ReaderAnnotationStore.add(prefs, bookFile.getName(), currentSpine,\n                data.start, data.end, data.text, color, note);\n        applySavedAnnotations();\n''',
    '''        ReaderAnnotationStore.add(prefs, bookFile.getName(), currentSpine,\n                data.start, data.end, data.text, color, note);\n        GoogleAutoSync.scheduleSoon(this);\n        applySavedAnnotations();\n''',
    "annotation add auto sync",
)
reader = replace_once(
    reader,
    '''                    ReaderAnnotationStore.remove(prefs, bookFile.getName(), a.id);\n                    applySavedAnnotations();\n''',
    '''                    ReaderAnnotationStore.remove(prefs, bookFile.getName(), a.id);\n                    GoogleAutoSync.scheduleSoon(this);\n                    applySavedAnnotations();\n''',
    "annotation remove auto sync",
)
reader = replace_once(
    reader,
    '''                .putString("epub_reading_mode", readingMode)\n                .putLong("sync_updated_ms", System.currentTimeMillis())\n                .apply();\n    }\n\n    private String readingModeDisplayName() {\n''',
    '''                .putString("epub_reading_mode", readingMode)\n                .putLong("sync_updated_ms", System.currentTimeMillis())\n                .apply();\n        GoogleAutoSync.scheduleSoon(this);\n    }\n\n    private String readingModeDisplayName() {\n''',
    "reader preferences auto sync",
)
reader = replace_once(
    reader,
    '''    protected void onResume() {\n        super.onResume();\n        applyWindowPreferences();\n        updateNightLightOverlay();\n        getWindow().getDecorView().postDelayed(this::enterImmersive, 80L);\n    }\n\n    @Override\n    protected void onPause() {\n        if (!isPdf) saveEpubState();\n        super.onPause();\n    }\n''',
    '''    protected void onResume() {\n        super.onResume();\n        applyWindowPreferences();\n        updateNightLightOverlay();\n        GoogleAutoSync.schedule(this);\n        getWindow().getDecorView().postDelayed(this::enterImmersive, 80L);\n    }\n\n    @Override\n    protected void onPause() {\n        if (!isPdf) saveEpubState();\n        GoogleAutoSync.flush(this);\n        super.onPause();\n    }\n''',
    "reader lifecycle auto sync",
)
READER.write_text(reader, encoding="utf-8")

print("WoW Reader automatic cloud sync migration applied")
