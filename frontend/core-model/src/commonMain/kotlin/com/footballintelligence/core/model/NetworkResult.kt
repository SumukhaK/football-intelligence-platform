package com.footballintelligence.core.model

/** Wraps an async operation result: success, error, or loading. */
sealed class NetworkResult<out T> {
    /**
     * A result. [cachedAt] is set (ISO 8601, UTC) when the server could not be
     * reached and this is the last saved response instead.
     */
    data class Success<T>(val data: T, val cachedAt: String? = null) : NetworkResult<T>()
    data class Error(
        val message: String,
        val code: Int? = null,
        val kind: ErrorKind = ErrorKind.UNKNOWN,
    ) : NetworkResult<Nothing>()
    data object Loading : NetworkResult<Nothing>()
}
