package com.footballintelligence.feature.team

import androidx.lifecycle.ViewModel
import com.footballintelligence.core.model.FavouriteTeam
import com.footballintelligence.core.model.FavouriteTeamStore

/**
 * The server-confirmed favourite for Settings. Read after the account gate;
 * saving a new team relaunches the app.
 */
class FavouriteTeamViewModel(store: FavouriteTeamStore) : ViewModel() {
    /** Null when the server confirmed that this account has no favourite. */
    val favourite: FavouriteTeam? = store.load()
}
