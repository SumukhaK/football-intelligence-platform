package com.footballintelligence.feature.team.repository

import com.footballintelligence.core.model.AccountPreferences
import com.footballintelligence.core.model.FavouriteTeam
import com.footballintelligence.core.model.NetworkResult

/** Loads and saves server preferences without crossing authenticated sessions. */
interface AccountPreferencesRepository {
    /** Current session identity; null when signed out. */
    val sessionToken: String?

    /** Loads only for the session that opened the screen. */
    suspend fun load(token: String): NetworkResult<AccountPreferences>

    /** Saves only for the session that opened the picker. */
    suspend fun save(token: String, favourite: FavouriteTeam): NetworkResult<AccountPreferences>
}
