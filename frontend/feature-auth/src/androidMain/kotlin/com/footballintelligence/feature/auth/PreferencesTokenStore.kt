package com.footballintelligence.feature.auth

import android.content.SharedPreferences
import com.footballintelligence.core.model.TokenStore

/**
 * [TokenStore] in the app's private SharedPreferences. Only this app can read
 * them, and the manifest turns off backup so the token never leaves the device.
 */
class PreferencesTokenStore(private val prefs: SharedPreferences) : TokenStore {
    override fun load(): String? = prefs.getString(KEY_TOKEN, null)

    override fun save(token: String) = prefs.edit().putString(KEY_TOKEN, token).apply()

    override fun clear() = prefs.edit().remove(KEY_TOKEN).apply()

    private companion object {
        const val KEY_TOKEN = "token"
    }
}
