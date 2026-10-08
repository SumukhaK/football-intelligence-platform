package com.footballintelligence.feature.team

import android.content.SharedPreferences
import com.footballintelligence.core.model.FavouriteTeam
import com.footballintelligence.core.model.FavouriteTeamStore

/** [FavouriteTeamStore] in the app's private SharedPreferences. */
class PreferencesFavouriteTeamStore(private val prefs: SharedPreferences) : FavouriteTeamStore {
    override fun load(): FavouriteTeam? {
        val league = prefs.getString(KEY_LEAGUE, null)
        val team = prefs.getString(KEY_TEAM, null)
        return if (league != null && team != null) FavouriteTeam(league, team) else null
    }

    override fun save(favourite: FavouriteTeam) {
        prefs.edit()
            .putString(KEY_LEAGUE, favourite.league)
            .putString(KEY_TEAM, favourite.team)
            .apply()
    }

    private companion object {
        const val KEY_LEAGUE = "league"
        const val KEY_TEAM = "team"
    }
}
