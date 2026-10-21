package com.footballintelligence.feature.team

import com.footballintelligence.core.model.AccountPreferences
import com.footballintelligence.core.model.FavouriteTeam
import com.footballintelligence.core.model.NetworkResult
import com.footballintelligence.core.network.AccountPreferencesApiService
import com.footballintelligence.core.network.AuthSession
import com.footballintelligence.feature.team.repository.AccountPreferencesRepository
import kotlinx.coroutines.ensureActive
import kotlin.coroutines.coroutineContext

/** Hydrates the account-bound cache only after a current session's server response. */
class DefaultAccountPreferencesRepository(
    private val api: AccountPreferencesApiService,
    private val session: AuthSession,
    private val cache: PreferencesFavouriteTeamStore,
) : AccountPreferencesRepository {
    override val sessionToken: String? get() = session.token.value

    override suspend fun load(token: String): NetworkResult<AccountPreferences> =
        forSession(token) { api.load(token) }

    override suspend fun save(token: String, favourite: FavouriteTeam): NetworkResult<AccountPreferences> =
        forSession(token) { api.save(token, favourite) }

    private suspend fun forSession(
        token: String,
        request: suspend () -> NetworkResult<AccountPreferences>,
    ): NetworkResult<AccountPreferences> {
        if (sessionToken != token) return NetworkResult.Error("Session changed", code = 401)
        val result = request()
        coroutineContext.ensureActive()
        return if (sessionToken != token) {
            NetworkResult.Error("Session changed", code = 401)
        } else {
            if (result is NetworkResult.Success) cache.confirm(token, result.data)
            result
        }
    }
}
