package com.footballintelligence.core.network

import org.junit.jupiter.api.Assertions.assertEquals
import org.junit.jupiter.api.Assertions.assertTrue
import org.junit.jupiter.api.Test

class NetworkConfigTest {
    @Test
    fun `an unreachable server is given up on within seconds`() {
        assertEquals(5_000L, NetworkConfig().connectTimeoutMs)
    }

    @Test
    fun `a reachable but slow server still gets the full request timeout`() {
        val config = NetworkConfig()
        assertTrue(config.connectTimeoutMs < config.timeoutMs)
    }

    @Test
    fun `a crest URL escapes the team name for the path`() {
        val config = NetworkConfig(baseUrl = "http://test", apiVersion = "v2")
        assertEquals("http://test/v2/teams/Nott'm%20Forest/crest", config.crestUrl("Nott'm Forest"))
    }
}
