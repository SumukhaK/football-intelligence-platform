package com.footballintelligence.app.di

import com.footballintelligence.core.network.CachingFootballApiService
import com.footballintelligence.core.network.FileResponseCache
import com.footballintelligence.core.network.FootballApiService
import com.footballintelligence.core.network.HttpClientFactory
import com.footballintelligence.core.network.KtorFootballApiService
import com.footballintelligence.core.network.NetworkConfig
import com.footballintelligence.core.network.ResponseCache
import org.koin.android.ext.koin.androidContext
import org.koin.dsl.module
import java.io.File
import java.time.Instant

/**
 * Root Koin module: network client and API service singletons.
 *
 * Every response is saved to the app's cache directory and replayed when the
 * server can't be reached, so screens show the last data with an offline banner.
 */
val networkModule = module {
    single { NetworkConfig() }
    single { HttpClientFactory.create(config = get()) }
    single<ResponseCache> { FileResponseCache(File(androidContext().cacheDir, "api")) }
    single<FootballApiService> {
        CachingFootballApiService(
            delegate = KtorFootballApiService(client = get(), config = get()),
            cache = get(),
            clock = { Instant.now().toString() },
        )
    }
}
