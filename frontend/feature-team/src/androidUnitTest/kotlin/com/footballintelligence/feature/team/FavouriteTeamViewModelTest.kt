package com.footballintelligence.feature.team

import com.footballintelligence.core.model.FavouriteTeam
import com.footballintelligence.core.model.FavouriteTeamStore
import io.mockk.every
import io.mockk.mockk
import org.junit.jupiter.api.Assertions.assertEquals
import org.junit.jupiter.api.Test

class FavouriteTeamViewModelTest {
    private val store = mockk<FavouriteTeamStore>()

    @Test
    fun `settings has no team when the confirmed account is empty`() {
        every { store.load() } returns null
        assertEquals(null, FavouriteTeamViewModel(store).favourite)
    }

    @Test
    fun `settings displays the server confirmed cached team`() {
        every { store.load() } returns FavouriteTeam("Bundesliga", "Dortmund")
        val vm = FavouriteTeamViewModel(store)
        assertEquals(FavouriteTeam("Bundesliga", "Dortmund"), vm.favourite)
    }
}
