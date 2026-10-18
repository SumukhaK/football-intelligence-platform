package com.footballintelligence.core.model

import kotlinx.serialization.Serializable

/** An authenticated server response; explicit null confirms no favourite exists. */
@Serializable
data class AccountPreferences(val email: String, val favourite: FavouriteTeam?)

/** Replaces only the authenticated account's favourite. */
@Serializable
data class SaveFavouriteRequest(val favourite: FavouriteTeam)
