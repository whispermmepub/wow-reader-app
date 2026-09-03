from pathlib import Path
import re

reader = Path('app/src/main/java/com/whisper/wowreader/BookReaderActivity.java')
text = reader.read_text(encoding='utf-8')

if 'import java.util.Enumeration;' not in text:
    text = text.replace('import java.util.Calendar;\n', 'import java.util.Calendar;\nimport java.util.Enumeration;\n')
if 'import java.util.zip.ZipFile;' not in text:
    text = text.replace('import java.util.zip.ZipEntry;\n', 'import java.util.zip.ZipEntry;\nimport java.util.zip.ZipFile;\n')

pattern = re.compile(r'    private void unzipEpub\(File epub, File dest\) throws Exception \{.*?\n    \}\n\n    private void deleteRecursive', re.S)
replacement = '''    private void unzipEpub(File epub, File dest) throws Exception {
        // Prefer the ZIP central directory. Some EPUB producers write a wrong
        // uncompressed size into a local file header while the central directory
        // is correct. ZipInputStream trusts that broken local value and throws
        // "invalid entry size"; ZipFile reads the correct central-directory metadata.
        try {
            unzipEpubWithCentralDirectory(epub, dest);
            return;
        } catch (SecurityException unsafe) {
            throw unsafe;
        } catch (Exception centralDirectoryFailure) {
            // Keep support for unusual streaming ZIPs whose central directory is
            // incomplete but whose local entries are still readable.
            resetEpubExtractionDirectory(dest);
            try {
                unzipEpubStreaming(epub, dest);
            } catch (Exception streamingFailure) {
                streamingFailure.addSuppressed(centralDirectoryFailure);
                throw streamingFailure;
            }
        }
    }

    private void unzipEpubWithCentralDirectory(File epub, File dest) throws Exception {
        String destPath = dest.getCanonicalPath() + File.separator;
        byte[] buffer = new byte[64 * 1024];

        try (ZipFile zip = new ZipFile(epub)) {
            Enumeration<? extends ZipEntry> entries = zip.entries();
            while (entries.hasMoreElements()) {
                ZipEntry entry = entries.nextElement();
                File out = safeEpubOutput(dest, destPath, entry.getName());

                if (entry.isDirectory()) {
                    if (!out.mkdirs() && !out.isDirectory())
                        throw new Exception("Cannot create EPUB folder");
                    continue;
                }

                File parent = out.getParentFile();
                if (parent != null && !parent.mkdirs() && !parent.isDirectory())
                    throw new Exception("Cannot create EPUB folder");

                try (InputStream in = zip.getInputStream(entry);
                     FileOutputStream fos = new FileOutputStream(out)) {
                    int n;
                    while ((n = in.read(buffer)) != -1) {
                        if (n > 0) fos.write(buffer, 0, n);
                    }
                }
            }
        }
    }

    private void unzipEpubStreaming(File epub, File dest) throws Exception {
        String destPath = dest.getCanonicalPath() + File.separator;

        try (ZipInputStream zis = new ZipInputStream(new FileInputStream(epub))) {
            ZipEntry entry;
            byte[] buffer = new byte[64 * 1024];

            while ((entry = zis.getNextEntry()) != null) {
                File out = safeEpubOutput(dest, destPath, entry.getName());

                if (entry.isDirectory()) {
                    if (!out.mkdirs() && !out.isDirectory())
                        throw new Exception("Cannot create EPUB folder");
                } else {
                    File parent = out.getParentFile();
                    if (parent != null && !parent.mkdirs() && !parent.isDirectory())
                        throw new Exception("Cannot create EPUB folder");

                    try (FileOutputStream fos = new FileOutputStream(out)) {
                        int n;
                        while ((n = zis.read(buffer)) != -1) {
                            if (n > 0) fos.write(buffer, 0, n);
                        }
                    }
                }

                zis.closeEntry();
            }
        }
    }

    private File safeEpubOutput(File dest, String destPath, String entryName) throws Exception {
        String normalized = entryName == null ? "" : entryName.replace('\\\\', '/');
        File out = new File(dest, normalized);
        String outPath = out.getCanonicalPath();
        if (!outPath.startsWith(destPath))
            throw new SecurityException("Unsafe EPUB path");
        return out;
    }

    private void resetEpubExtractionDirectory(File dest) throws Exception {
        File[] children = dest.listFiles();
        if (children != null) {
            for (File child : children) deleteRecursive(child);
        }
        if (!dest.exists() && !dest.mkdirs())
            throw new Exception("Cannot prepare EPUB folder");
    }

    private void deleteRecursive'''

text2, count = pattern.subn(lambda _: replacement, text, count=1)
if count != 1:
    raise SystemExit('Could not locate the existing unzipEpub method exactly once')
reader.write_text(text2, encoding='utf-8')

workflow = Path('.github/workflows/build-apk.yml')
wf = workflow.read_text(encoding='utf-8')
guard = "          grep -q 'prewarmAdjacentChapters' \"$READER\"\n"
new_guard = guard + "          grep -q 'unzipEpubWithCentralDirectory' \"$READER\"\n          grep -q 'ZipFile zip = new ZipFile(epub)' \"$READER\"\n"
if "unzipEpubWithCentralDirectory" not in wf:
    if guard not in wf:
        raise SystemExit('Could not locate EPUB source-check insertion point')
    workflow.write_text(wf.replace(guard, new_guard, 1), encoding='utf-8')
