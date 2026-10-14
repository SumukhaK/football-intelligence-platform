# ADR 028 — Crash Reports in the Staging App

**Status:** Accepted

**Supersedes:** —
**Superseded by:** —

## Context

The staging app (`com.footballintelligence.app.stg`, tracker step 6a) is
shared directly with invited friends. The backend logs every request (ADR
024), but when the app crashes on a friend's phone no request reaches it, so
the owner would never hear about it. The owner asked for crash reports in the
staging app and created a Firebase project for it. Google Analytics was
considered and turned down: the server already records the usage the beta
needs.

## Decision

1. **Firebase Crashlytics, staging build only.** The `staging` flavor depends
   on `firebase-crashlytics` through the Firebase BoM; the `local` flavor has
   no Firebase code at all. Firebase's own `FirebaseInitProvider` starts it,
   so the app needs no setup code.
2. **Config kept out of Git.** The owner keeps `google-services.json` at
   `frontend/app/src/staging/`, already ignored by `.gitignore`, because it
   names the Google project. A build without it (CI, other machines) still
   succeeds and sends nothing: the Google Services plugin ignores the missing
   file, `enableCrashReports` finds no Firebase app, and the `local` flavor
   doesn't upload R8 mappings.
3. **Nothing is sent before consent.** The staging manifest turns collection
   off; the app turns it on once the user has accepted the notice. The notice
   (version 2) now says crash reports go to Google and that answers come from
   a model hosted by Cloudflare, so every user is asked again.
4. **No Play Store review applies**, because the APK is not published there.
   If the app is ever published, it needs a privacy policy page.

### Dependencies this allows

- `com.google.firebase:firebase-bom` and `firebase-crashlytics` (staging only).
- The `com.google.gms.google-services` and `com.google.firebase.crashlytics`
  Gradle plugins, which read the config and add the build ID Crashlytics needs.

## Consequences

- **Easier:** the owner sees crashes from friends' phones, with stack traces
  deobfuscated from the uploaded R8 mapping of staging release builds.
- **Privacy:** reports include the device model, Android version, a per-install
  ID and the stack trace; no account email or question text is attached.
- **Build:** a staging release build uploads its mapping file to Firebase, so it
  needs the network.
