package com.footballintelligence.core.network

import io.github.aakira.napier.Napier
import io.ktor.client.HttpClient
import io.ktor.client.plugins.HttpTimeout
import io.ktor.client.plugins.contentnegotiation.ContentNegotiation
import io.ktor.client.plugins.logging.LogLevel
import io.ktor.client.plugins.logging.Logger
import io.ktor.client.plugins.logging.Logging
import io.ktor.serialization.kotlinx.json.json
import kotlinx.serialization.json.Json

/** Creates a configured Ktor [HttpClient] for the Football Intelligence API. */
object HttpClientFactory {
    fun create(config: NetworkConfig): HttpClient =
        HttpClient {
            install(ContentNegotiation) {
                json(
                    Json {
                        ignoreUnknownKeys = true
                        isLenient = true
                        coerceInputValues = true
                    },
                )
            }
            install(Logging) {
                logger = object : Logger {
                    override fun log(message: String) {
                        Napier.d(message, tag = "Ktor")
                    }
                }
                level = LogLevel.BODY
            }
            install(HttpTimeout) {
                requestTimeoutMillis = config.timeoutMs
                connectTimeoutMillis = config.timeoutMs
                socketTimeoutMillis = config.timeoutMs
            }
        }
}
