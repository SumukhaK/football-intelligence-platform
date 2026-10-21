package com.footballintelligence.core.network

import com.footballintelligence.core.model.AccountPreferences
import com.footballintelligence.core.model.FavouriteTeam
import com.footballintelligence.core.model.NetworkResult
import com.footballintelligence.core.model.SaveFavouriteRequest
import io.ktor.client.HttpClient
import io.ktor.client.request.get
import io.ktor.client.request.header
import io.ktor.client.request.put
import io.ktor.client.request.setBody
import io.ktor.http.ContentType
import io.ktor.http.HttpHeaders
import io.ktor.http.contentType

/** Uncached account preferences, bound to the credentials that started each operation. */
class AccountPreferencesApiService(private val client: HttpClient, config: NetworkConfig) {
    private val url = "${config.baseUrl}/${config.apiVersion}/me/preferences"

    /** Reads the server's authoritative favourite, including an explicit empty result. */
    suspend fun load(token: String): NetworkResult<AccountPreferences> = guarded {
        client.get(url) { header(HttpHeaders.Authorization, "Bearer $token") }.decode()
    }

    /** Persists a selection before the app changes its cache or leaves the picker. */
    suspend fun save(token: String, favourite: FavouriteTeam): NetworkResult<AccountPreferences> = guarded {
        client.put(url) {
            header(HttpHeaders.Authorization, "Bearer $token")
            contentType(ContentType.Application.Json)
            setBody(SaveFavouriteRequest(favourite))
        }.decode()
    }
}
