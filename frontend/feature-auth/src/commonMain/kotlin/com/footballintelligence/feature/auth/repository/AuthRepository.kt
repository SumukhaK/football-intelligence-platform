package com.footballintelligence.feature.auth.repository

import com.footballintelligence.core.model.ConsentRequest
import com.footballintelligence.core.model.LoginRequest
import com.footballintelligence.core.model.Me
import com.footballintelligence.core.model.NetworkResult
import com.footballintelligence.core.model.RedeemInviteRequest
import com.footballintelligence.core.model.SessionResponse
import com.footballintelligence.core.network.AuthApiService
import com.footballintelligence.core.network.AuthSession

/** Signs in and out, and reads and accepts the notice (ADR 022). */
interface AuthRepository {
    /** Signs in; on success the session holds the new token. */
    suspend fun signIn(email: String, password: String): NetworkResult<Unit>

    /** Sets a password with an invite code and signs in. */
    suspend fun redeemInvite(email: String, code: String, password: String): NetworkResult<Unit>

    /** Ends the session on the server, then forgets the token even if that failed. */
    suspend fun signOut()

    /** The signed-in user and the notice. */
    suspend fun me(): NetworkResult<Me>

    /** Accepts notice [version], allowing question text to be stored if [storeQuestions]. */
    suspend fun acceptConsent(version: Int, storeQuestions: Boolean): NetworkResult<Me>
}

/** Production implementation backed by [AuthApiService] and [AuthSession]. */
class DefaultAuthRepository(
    private val api: AuthApiService,
    private val session: AuthSession,
) : AuthRepository {
    override suspend fun signIn(email: String, password: String): NetworkResult<Unit> =
        api.login(LoginRequest(email.trim(), password)).startSession()

    override suspend fun redeemInvite(email: String, code: String, password: String): NetworkResult<Unit> =
        api.redeemInvite(RedeemInviteRequest(email.trim(), code.trim(), password)).startSession()

    override suspend fun signOut() {
        api.logout()
        session.signOut()
    }

    override suspend fun me(): NetworkResult<Me> = api.me()

    override suspend fun acceptConsent(version: Int, storeQuestions: Boolean): NetworkResult<Me> =
        api.acceptConsent(ConsentRequest(version, storeQuestions))

    private fun NetworkResult<SessionResponse>.startSession(): NetworkResult<Unit> = when (this) {
        is NetworkResult.Success -> {
            session.signIn(data.token)
            NetworkResult.Success(Unit)
        }
        is NetworkResult.Error -> this
        is NetworkResult.Loading -> this
    }
}
