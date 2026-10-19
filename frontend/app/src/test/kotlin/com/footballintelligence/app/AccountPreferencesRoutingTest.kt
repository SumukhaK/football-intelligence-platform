package com.footballintelligence.app

import com.footballintelligence.core.model.ErrorKind
import com.footballintelligence.core.model.FavouriteTeam
import com.footballintelligence.core.navigation.Screen
import com.footballintelligence.feature.team.AccountPreferencesUiState
import org.junit.jupiter.api.Assertions.assertEquals
import org.junit.jupiter.api.Assertions.assertNull
import org.junit.jupiter.api.Test

class AccountPreferencesRoutingTest {
    @Test
    fun `loading and retryable failure cannot enter onboarding or home`() {
        assertNull(AccountPreferencesUiState.Loading.destination())
        assertNull(AccountPreferencesUiState.Error("Unavailable", ErrorKind.OFFLINE).destination())
    }

    @Test
    fun `only a server confirmed empty account enters onboarding`() {
        assertEquals(Screen.Onboarding, AccountPreferencesUiState.ConfirmedEmpty.destination())
        val saved = AccountPreferencesUiState.Success(FavouriteTeam("Serie A", "Inter"))
        assertEquals(Screen.Home, saved.destination())
    }
}
