package com.footballintelligence.core.model

/** What went wrong, in terms the app can explain to a fan. */
enum class ErrorKind {
    /** The server could not be reached at all. */
    OFFLINE,

    /** The server answered but a model or dataset is not ready (HTTP 502–504). */
    SERVER_BUSY,

    /** The server refused the request and said why (HTTP 4xx); the message is its reason. */
    REJECTED,

    /** Anything else. */
    UNKNOWN,
}
