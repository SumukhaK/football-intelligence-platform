package com.footballintelligence.core.network

import com.footballintelligence.core.model.ConsentRequest
import com.footballintelligence.core.model.LoginRequest
import com.footballintelligence.core.model.Me
import com.footballintelligence.core.model.NetworkResult
import com.footballintelligence.core.model.RedeemInviteRequest
import com.footballintelligence.core.model.SessionResponse
import io.ktor.client.HttpClient
import io.ktor.client.request.get
import io.ktor.client.request.post
import io.ktor.client.request.setBody
import io.ktor.http.ContentType
import io.ktor.http.contentType
import io.ktor.http.isSuccess

/**
 * Sign-in and consent endpoints (ADR 022). Never cached: a saved answer
 * would sign someone in, or skip the notice, without asking the server.
 */
class AuthApiService(
    private val client: HttpClient,
    private val config: NetworkConfig,
) {
    private val base get() = "${config.baseUrl}/${config.apiVersion}"

    /** Checks an email and password and returns a session token. */
    suspend fun login(request: LoginRequest): NetworkResult<SessionResponse> =
        guarded { postJson("$base/auth/login", request).decode() }

    /** Sets the password for an invited email with its one-time code, and signs in. */
    suspend fun redeemInvite(request: RedeemInviteRequest): NetworkResult<SessionResponse> =
        guarded { postJson("$base/auth/redeem-invite", request).decode() }

    /** Ends the session behind the current token. */
    suspend fun logout(): NetworkResult<Unit> =
        guarded {
            val response = client.post("$base/auth/logout")
            if (response.status.isSuccess()) NetworkResult.Success(Unit) else response.toError()
        }

    /** The signed-in user and the notice they must accept. */
    suspend fun me(): NetworkResult<Me> = guarded { client.get("$base/me").decode() }

    /** Records that the user accepted notice [ConsentRequest.version]. */
    suspend fun acceptConsent(request: ConsentRequest): NetworkResult<Me> =
        guarded { postJson("$base/me/consent", request).decode() }

    private suspend inline fun <reified T> postJson(url: String, body: T) =
        client.post(url) {
            contentType(ContentType.Application.Json)
            setBody(body)
        }
}
