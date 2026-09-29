package com.footballintelligence.core.network

/**
 * Network configuration. Base URL is overridable for testing.
 *
 * [apiVersion] is the backend API version the app speaks (ADR 014): v2 serves
 * all five leagues with the current model.
 *
 * [connectTimeoutMs] is short so an unreachable server falls back to saved
 * data quickly; [timeoutMs] bounds a request once connected, because some
 * answers take the server a while to compute.
 */
data class NetworkConfig(
    val baseUrl: String = "http://10.0.2.2:8000",
    val apiVersion: String = "v2",
    val timeoutMs: Long = 30_000L,
    val connectTimeoutMs: Long = 5_000L,
)
