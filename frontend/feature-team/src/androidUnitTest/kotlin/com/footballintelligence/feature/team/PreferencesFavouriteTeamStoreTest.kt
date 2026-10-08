package com.footballintelligence.feature.team

import android.content.SharedPreferences
import com.footballintelligence.core.model.FavouriteTeam
import io.mockk.every
import io.mockk.mockk
import io.mockk.verify
import org.junit.jupiter.api.Assertions.assertEquals
import org.junit.jupiter.api.Assertions.assertNull
import org.junit.jupiter.api.Test

class PreferencesFavouriteTeamStoreTest {
    private val editor = mockk<SharedPreferences.Editor>(relaxed = true)
    private val prefs = mockk<SharedPreferences> {
        every { edit() } returns editor
        every { getString(any(), null) } returns null
    }
    private val store = PreferencesFavouriteTeamStore(prefs)

    @Test
    fun `nothing is saved on first launch`() {
        assertNull(store.load())
    }

    @Test
    fun `a saved team is read back`() {
        every { prefs.getString("league", null) } returns "La Liga"
        every { prefs.getString("team", null) } returns "Barcelona"
        assertEquals(FavouriteTeam("La Liga", "Barcelona"), store.load())
    }

    @Test
    fun `saving writes the league and team together`() {
        every { editor.putString(any(), any()) } returns editor
        store.save(FavouriteTeam("Ligue 1", "Lens"))
        verify {
            editor.putString("league", "Ligue 1")
            editor.putString("team", "Lens")
            editor.apply()
        }
    }
}
