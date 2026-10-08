package com.footballintelligence.feature.team

import androidx.lifecycle.ViewModel
import com.footballintelligence.core.model.FavouriteTeam
import com.footballintelligence.core.model.FavouriteTeamStore

/**
 * The saved favourite team, for the app's start screen and the Settings
 * section. Read once: saving a new team relaunches the app.
 */
class FavouriteTeamViewModel(store: FavouriteTeamStore) : ViewModel() {
    /** Null until the fan has picked a team. */
    val favourite: FavouriteTeam? = store.load()

    /** True on first launch only; onboarding is shown until a team is saved. */
    val needsOnboarding: Boolean get() = favourite == null
}
