package com.footballintelligence.app

import android.content.Context
import com.google.firebase.FirebaseApp
import com.google.firebase.crashlytics.FirebaseCrashlytics

/**
 * Turns crash reports on once the user has accepted the notice (ADR 028).
 * A build without the Firebase config has no Firebase app, so it sends nothing.
 */
fun enableCrashReports(context: Context) {
    if (FirebaseApp.getApps(context).isNotEmpty()) {
        FirebaseCrashlytics.getInstance().setCrashlyticsCollectionEnabled(true)
    }
}
