package com.footballintelligence.feature.team

import android.content.SharedPreferences
import com.footballintelligence.core.model.AccountPreferences
import com.footballintelligence.core.model.FavouriteTeam
import com.footballintelligence.core.model.TokenStore
import com.footballintelligence.core.network.AuthSession
import io.mockk.every
import io.mockk.mockk
import org.junit.jupiter.api.Assertions.assertEquals
import org.junit.jupiter.api.Assertions.assertNull
import org.junit.jupiter.api.Test

class PreferencesFavouriteTeamStoreTest {
    private val values = mutableMapOf<String, String>()
    private val editor = mockk<SharedPreferences.Editor>(relaxed = true)
    private val prefs = mockk<SharedPreferences>()
    private val session = AuthSession(object : TokenStore {
        override fun load() = "A"
        override fun save(token: String) = Unit
        override fun clear() = Unit
    })
    private val arsenal = FavouriteTeam("Premier League", "Arsenal")

    init {
        every { prefs.edit() } returns editor
        every { prefs.getString(any(), null) } answers { values[firstArg()] }
        every { editor.putString(any(), any()) } answers {
            values[firstArg()] = secondArg()
            editor
        }
        every { editor.remove(any()) } answers {
            values.remove(firstArg<String>())
            editor
        }
    }

    @Test
    fun `legacy unscoped cache is never assigned to a login`() {
        values["league"] = "Serie A"
        values["team"] = "Inter"
        val store = PreferencesFavouriteTeamStore(prefs, session)
        assertNull(store.load())
        assertNull(values["team"])
    }

    @Test
    fun `confirmed cache becomes inaccessible immediately on sign out or switch`() {
        val store = PreferencesFavouriteTeamStore(prefs, session)
        store.confirm("A", AccountPreferences("a@example.com", arsenal))
        assertEquals(arsenal, store.load())
        session.signOut()
        assertNull(store.load())
        session.signIn("B")
        assertNull(store.load())
        store.confirm("B", AccountPreferences("b@example.com", null))
        assertNull(store.load())
        assertEquals("Arsenal", values["team:a@example.com"])
    }

    @Test
    fun `late account A response cannot change B cache`() {
        val store = PreferencesFavouriteTeamStore(prefs, session)
        session.signIn("B")
        store.confirm("B", AccountPreferences("b@example.com", FavouriteTeam("Serie A", "Inter")))
        store.confirm("A", AccountPreferences("a@example.com", arsenal))
        assertEquals(FavouriteTeam("Serie A", "Inter"), store.load())
        assertNull(values["team:a@example.com"])
    }

    @Test
    fun `new installs and upgrades both wait for server confirmation`() {
        val store = PreferencesFavouriteTeamStore(prefs, session)
        store.confirm("A", AccountPreferences("a@example.com", arsenal))
        val upgraded = PreferencesFavouriteTeamStore(prefs, session)
        assertNull(upgraded.load())
        upgraded.confirm("A", AccountPreferences("a@example.com", arsenal))
        assertEquals(arsenal, upgraded.load())
        values.clear()
        val reinstalled = PreferencesFavouriteTeamStore(prefs, session)
        assertNull(reinstalled.load())
        reinstalled.confirm("A", AccountPreferences("a@example.com", arsenal))
        assertEquals(arsenal, reinstalled.load())
    }
}
