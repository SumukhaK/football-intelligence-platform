package com.footballintelligence.core.model

import kotlinx.serialization.Serializable

/** The account's canonical favourite league and team. */
@Serializable
data class FavouriteTeam(val league: String, val team: String)

/** Server-confirmed account cache used by feature consumers. */
interface FavouriteTeamStore {
    /** The confirmed team's cached value, or null when empty or unavailable to this session. */
    fun load(): FavouriteTeam?

    /** Replaces the current account's cache after a confirmed server save. */
    fun save(favourite: FavouriteTeam)
}
