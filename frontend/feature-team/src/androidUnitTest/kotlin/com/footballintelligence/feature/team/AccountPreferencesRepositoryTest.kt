package com.footballintelligence.feature.team

import com.footballintelligence.core.model.AccountPreferences
import com.footballintelligence.core.model.FavouriteTeam
import com.footballintelligence.core.model.NetworkResult
import com.footballintelligence.core.model.TokenStore
import com.footballintelligence.core.network.AccountPreferencesApiService
import com.footballintelligence.core.network.AuthSession
import io.mockk.coEvery
import io.mockk.coVerify
import io.mockk.mockk
import io.mockk.verify
import kotlinx.coroutines.CompletableDeferred
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.async
import kotlinx.coroutines.test.runCurrent
import kotlinx.coroutines.test.runTest
import org.junit.jupiter.api.Assertions.assertInstanceOf
import org.junit.jupiter.api.Test

@OptIn(ExperimentalCoroutinesApi::class)
class AccountPreferencesRepositoryTest {
    private val api = mockk<AccountPreferencesApiService>()
    private val cache = mockk<PreferencesFavouriteTeamStore>(relaxed = true)
    private val session = AuthSession(object : TokenStore {
        override fun load() = "A"
        override fun save(token: String) = Unit
        override fun clear() = Unit
    })
    private val repository = DefaultAccountPreferencesRepository(api, session, cache)
    private val arsenal = FavouriteTeam("Premier League", "Arsenal")
    private val server = AccountPreferences("a@example.com", arsenal)

    @Test
    fun `empty device cache is restored only from the server`() = runTest {
        coEvery { api.load("A") } returns NetworkResult.Success(server)
        assertInstanceOf(NetworkResult.Success::class.java, repository.load("A"))
        verify { cache.confirm("A", server) }
        coVerify(exactly = 0) { api.save(any(), any()) }
    }

    @Test
    fun `failed save never updates the cache`() = runTest {
        coEvery { api.save("A", arsenal) } returns NetworkResult.Error("Unavailable")
        assertInstanceOf(NetworkResult.Error::class.java, repository.save("A", arsenal))
        verify(exactly = 0) { cache.confirm(any(), any()) }
    }

    @Test
    fun `late load and save cannot populate a replacement session`() = runTest {
        val load = CompletableDeferred<NetworkResult<AccountPreferences>>()
        val save = CompletableDeferred<NetworkResult<AccountPreferences>>()
        coEvery { api.load("A") } coAnswers { load.await() }
        coEvery { api.save("A", arsenal) } coAnswers { save.await() }
        val read = async { repository.load("A") }
        val write = async { repository.save("A", arsenal) }
        runCurrent()
        session.signOut()
        session.signIn("B")
        load.complete(NetworkResult.Success(server))
        save.complete(NetworkResult.Success(server))
        assertInstanceOf(NetworkResult.Error::class.java, read.await())
        assertInstanceOf(NetworkResult.Error::class.java, write.await())
        verify(exactly = 0) { cache.confirm(any(), any()) }
        assertInstanceOf(NetworkResult.Error::class.java, repository.save("A", arsenal))
        coVerify(exactly = 1) { api.save("A", arsenal) }
    }
}
