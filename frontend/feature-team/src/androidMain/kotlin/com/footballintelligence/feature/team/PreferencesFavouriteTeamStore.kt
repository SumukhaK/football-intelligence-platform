package com.footballintelligence.feature.team

import android.content.SharedPreferences
import com.footballintelligence.core.model.AccountPreferences
import com.footballintelligence.core.model.FavouriteTeam
import com.footballintelligence.core.model.FavouriteTeamStore
import com.footballintelligence.core.network.AuthSession

/** Server-confirmed cache, accessible only to the session that loaded the account. */
class PreferencesFavouriteTeamStore(
    private val prefs: SharedPreferences,
    private val session: AuthSession,
) : FavouriteTeamStore {
    private var confirmedToken: String? = null
    private var email: String? = null

    init {
        // Legacy entries have no trustworthy owner and must never be uploaded.
        prefs.edit().remove("league").remove("team").apply()
    }

    override fun load(): FavouriteTeam? {
        val account = email?.takeIf { confirmedToken == session.token.value } ?: return null
        val league = prefs.getString("league:$account", null)
        val team = prefs.getString("team:$account", null)
        return if (league != null && team != null) FavouriteTeam(league, team) else null
    }

    override fun save(favourite: FavouriteTeam) {
        val account = email?.takeIf { confirmedToken == session.token.value } ?: return
        prefs.edit()
            .putString("league:$account", favourite.league)
            .putString("team:$account", favourite.team)
            .apply()
    }

    /** Makes only a current session's successful response available to feature consumers. */
    fun confirm(token: String, preferences: AccountPreferences) {
        if (token != session.token.value) return
        confirmedToken = token
        email = preferences.email
        val favourite = preferences.favourite
        if (favourite == null) {
            prefs.edit().remove("league:${preferences.email}").remove("team:${preferences.email}").apply()
        } else {
            save(favourite)
        }
    }
}
