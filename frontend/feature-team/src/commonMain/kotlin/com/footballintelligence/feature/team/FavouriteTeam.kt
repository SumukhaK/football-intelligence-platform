package com.footballintelligence.feature.team

/** The fan's chosen league and team, saved on the device. */
data class FavouriteTeam(val league: String, val team: String)

/** Saves the favourite team on the device. */
interface FavouriteTeamStore {
    /** The saved team, or null on first launch before the fan has picked one. */
    fun load(): FavouriteTeam?

    /** Replaces the saved team. */
    fun save(favourite: FavouriteTeam)
}
