package com.footballintelligence.app.di

import com.footballintelligence.core.network.HttpClientFactory
import com.footballintelligence.core.network.KtorFootballApiService
import com.footballintelligence.core.network.NetworkConfig
import com.footballintelligence.core.network.FootballApiService
import org.koin.dsl.module

/** Root Koin module: network client and API service singletons. */
val networkModule = module {
    single { NetworkConfig() }
    single { HttpClientFactory.create(config = get()) }
    single<FootballApiService> { KtorFootballApiService(client = get(), config = get()) }
}
