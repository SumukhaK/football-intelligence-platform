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
}
