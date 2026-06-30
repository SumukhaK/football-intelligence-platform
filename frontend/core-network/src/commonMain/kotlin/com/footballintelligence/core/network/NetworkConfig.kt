package com.footballintelligence.core.network

/** Network configuration. Base URL is overridable for testing. */
data class NetworkConfig(
    val baseUrl: String = "http://10.0.2.2:8000",
    val timeoutMs: Long = 30_000L,
)
