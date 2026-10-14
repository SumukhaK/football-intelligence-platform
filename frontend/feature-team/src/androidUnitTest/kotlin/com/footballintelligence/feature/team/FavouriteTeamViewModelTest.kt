package com.footballintelligence.feature.team

import com.footballintelligence.core.model.FavouriteTeam
import com.footballintelligence.core.model.FavouriteTeamStore
import io.mockk.every
import io.mockk.mockk
import org.junit.jupiter.api.Assertions.assertEquals
import org.junit.jupiter.api.Assertions.assertFalse
import org.junit.jupiter.api.Assertions.assertTrue
import org.junit.jupiter.api.Test

class FavouriteTeamViewModelTest {
    private val store = mockk<FavouriteTeamStore>()

    @Test
    fun `onboarding is needed on first launch`() {
        every { store.load() } returns null
        assertTrue(FavouriteTeamViewModel(store).needsOnboarding)
    }

    @Test
    fun `onboarding is shown only once, until a team is saved`() {
        every { store.load() } returns FavouriteTeam("Bundesliga", "Dortmund")
        val vm = FavouriteTeamViewModel(store)
        assertFalse(vm.needsOnboarding)
        assertEquals(FavouriteTeam("Bundesliga", "Dortmund"), vm.favourite)
    }
}
