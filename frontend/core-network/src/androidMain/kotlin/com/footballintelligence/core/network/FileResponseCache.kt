package com.footballintelligence.core.network

import kotlinx.serialization.json.Json
import java.io.File
import java.security.MessageDigest

/** Saves each response as a small JSON file in the app's cache directory. */
class FileResponseCache(private val directory: File) : ResponseCache {
    private val json = Json { ignoreUnknownKeys = true }

    override fun read(key: String): CachedResponse? =
        runCatching { json.decodeFromString<CachedResponse>(fileFor(key).readText()) }.getOrNull()

    override fun write(key: String, response: CachedResponse) {
        runCatching {
            directory.mkdirs()
            fileFor(key).writeText(json.encodeToString(CachedResponse.serializer(), response))
        }
    }

    private fun fileFor(key: String): File {
        val digest = MessageDigest.getInstance("SHA-256").digest(key.toByteArray())
        return File(directory, digest.joinToString("") { "%02x".format(it) } + ".json")
    }
}
