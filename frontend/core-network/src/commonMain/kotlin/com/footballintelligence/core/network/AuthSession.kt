package com.footballintelligence.core.network

import com.footballintelligence.core.model.TokenStore
import io.ktor.client.plugins.api.ClientPlugin
import io.ktor.client.plugins.api.createClientPlugin
import io.ktor.http.HttpHeaders
import io.ktor.http.HttpStatusCode
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow

/**
 * The signed-in session (ADR 022). [token] is null when signed out; the app
 * shows the sign-in screen whenever it becomes null.
 */
class AuthSession(private val store: TokenStore) {
    private val _token = MutableStateFlow(store.load())
    val token: StateFlow<String?> = _token.asStateFlow()

    /** Keeps [token] for every later request. */
    fun signIn(token: String) {
        store.save(token)
        _token.value = token
    }

    /** Forgets the token. */
    fun signOut() {
        store.clear()
        _token.value = null
    }
}

/**
 * Sends the session token with every request, and signs out when the server
 * rejects it (HTTP 401). A 401 for a token that was already replaced, or for
 * a request sent without one (a wrong password), leaves the session alone.
 */
fun bearerAuth(session: AuthSession): ClientPlugin<Unit> =
    createClientPlugin("BearerAuth") {
        onRequest { request, _ ->
            session.token.value?.let { request.headers[HttpHeaders.Authorization] = bearer(it) }
        }
        onResponse { response ->
            val sent = response.call.request.headers[HttpHeaders.Authorization]
            val current = session.token.value
            if (response.status == HttpStatusCode.Unauthorized && current != null && sent == bearer(current)) {
                session.signOut()
            }
        }
    }

private fun bearer(token: String) = "Bearer $token"
