# Android, CI and Platform Troubleshooting

[Python, data and API troubleshooting](troubleshooting.md). Commands are run from the repository root unless a section states otherwise.

## Android / Gradle Issues

### `SDK location not found`

**Cause:** Gradle cannot find the Android SDK because `local.properties` is missing.

**Fix:** Create `frontend/local.properties` with your SDK path:
```
# macOS
sdk.dir=/Users/<username>/Library/Android/sdk

# Windows
sdk.dir=C\:\\Users\\<username>\\AppData\\Local\\Android\\Sdk

# Linux
sdk.dir=/home/<username>/Android/Sdk
```

---

### `Unsupported class file major version N`

**Cause:** Gradle is running on a JDK that is too old. This project requires JDK 17+.

**Fix:**
1. Install JDK 17 or higher.
2. Set `JAVA_HOME` to point to the new JDK.
3. Verify: `java -version` should show `17.x` or higher.

---

### `Deprecated Gradle features were used in this build`

**Cause:** Some Gradle plugins use deprecated APIs. This is a known issue with the current Gradle 8.8 + Kotlin plugin combination.

**Impact:** Build succeeds. The warning is informational.

**Fix:** No action needed. The deprecations will be resolved in a future plugin update.

---

### Build fails with `Could not resolve` dependency errors

**Cause:** Gradle cannot reach Maven Central or Google's Maven repository.

**Fix:** Check your internet connection. On corporate networks, you may need to configure a proxy in `gradle.properties`:
```properties
systemProp.http.proxyHost=proxy.example.com
systemProp.http.proxyPort=8080
```

---

### `./gradlew: Permission denied` (macOS/Linux)

**Cause:** The Gradle wrapper script is not executable.

**Fix:**
```sh
chmod +x frontend/gradlew
```

---

### Android app shows the offline banner

**Cause:** The app cannot reach the backend at `http://10.0.2.2:8000/v2` (the emulator's address for your computer), so it shows the data it saved last time.

**Fix:** Start the backend from `ai/` with `uv run uvicorn backend.app.main:app --reload`, then pull down to refresh.

---

## CI Issues

### Frontend checks did not run on a pull request

**Cause:** The frontend workflows run only on pull requests into `develop` or `main` (and pushes to them) that change `frontend/`. Pull requests into other branches, such as a feature branch, skip them.

**Fix:** Run the same checks locally from `frontend/`:
```sh
./gradlew detekt testDebugUnitTest assembleDebug spotlessCheck
```

---

### CI fails with `./gradlew: Permission denied`

**Cause:** `frontend/gradlew` lost its executable bit in git, often after a commit from Windows.

**Fix:**
```sh
git update-index --chmod=+x frontend/gradlew
```

Commit the change. `git ls-files -s frontend/gradlew` should show mode `100755`.

---

## Platform-Specific Issues

### Windows: `uv run` command hangs in Git Bash

**Cause:** Git Bash has known issues with interactive Python processes.

**Fix:** Use PowerShell instead of Git Bash for all uv commands on Windows.

---

### macOS: `SSL: CERTIFICATE_VERIFY_FAILED`

**Cause:** Python's SSL certificates are not installed.

**Fix:**
```sh
# Run the Install Certificates script included with Python
/Applications/Python\ 3.12/Install\ Certificates.command
```

---

### Linux: `libgomp` not found when loading XGBoost model

**Cause:** OpenMP runtime is missing on some minimal Linux installations.

**Fix:**
```sh
# Ubuntu/Debian
sudo apt-get install libgomp1

# CentOS/RHEL
sudo yum install libgomp
```
