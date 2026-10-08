package com.footballintelligence.core.model

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

/** Request body for POST /auth/login. */
@Serializable
data class LoginRequest(val email: String, val password: String)

/** Request body for POST /auth/redeem-invite. */
@Serializable
data class RedeemInviteRequest(val email: String, val code: String, val password: String)

/** A session token from sign-in; sent as `Authorization: Bearer <token>`. */
@Serializable
data class SessionResponse(
    val token: String,
    @SerialName("expires_at") val expiresAt: String,
)

/** Response from GET /me: the signed-in user and the notice they must accept. */
@Serializable
data class Me(
    val email: String,
    @SerialName("consent_required") val consentRequired: Boolean,
    @SerialName("consent_version") val consentVersion: Int,
    @SerialName("consent_text") val consentText: String,
    @SerialName("store_questions") val storeQuestions: Boolean,
)

/** Request body for POST /me/consent. */
@Serializable
data class ConsentRequest(
    val version: Int,
    @SerialName("store_questions") val storeQuestions: Boolean,
)

/** Keeps the session token on the device. */
interface TokenStore {
    /** The saved token, or null when signed out. */
    fun load(): String?

    /** Replaces the saved token. */
    fun save(token: String)

    /** Forgets the token. */
    fun clear()
}
