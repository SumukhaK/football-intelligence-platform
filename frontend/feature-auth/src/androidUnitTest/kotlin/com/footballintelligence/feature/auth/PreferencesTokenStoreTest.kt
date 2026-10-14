package com.footballintelligence.feature.auth

import android.content.SharedPreferences
import io.mockk.every
import io.mockk.mockk
import io.mockk.verify
import org.junit.jupiter.api.Assertions.assertEquals
import org.junit.jupiter.api.Assertions.assertNull
import org.junit.jupiter.api.Test

class PreferencesTokenStoreTest {
    private val editor = mockk<SharedPreferences.Editor>(relaxed = true)
    private val prefs = mockk<SharedPreferences> {
        every { edit() } returns editor
        every { getString("token", null) } returns null
    }
    private val store = PreferencesTokenStore(prefs)

    @Test
    fun `signed out on first launch`() {
        assertNull(store.load())
    }

    @Test
    fun `a saved token is read back`() {
        every { prefs.getString("token", null) } returns "tok-1"
        assertEquals("tok-1", store.load())
    }

    @Test
    fun `saving and clearing write the token`() {
        every { editor.putString(any(), any()) } returns editor
        every { editor.remove(any()) } returns editor
        store.save("tok-1")
        store.clear()
        verify {
            editor.putString("token", "tok-1")
            editor.remove("token")
        }
    }
}
