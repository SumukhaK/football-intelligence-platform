package com.footballintelligence.feature.home.di

import com.footballintelligence.feature.home.HomeViewModel
import com.footballintelligence.feature.home.repository.DefaultHealthRepository
import com.footballintelligence.feature.home.repository.HealthRepository
import org.koin.androidx.viewmodel.dsl.viewModel
import org.koin.dsl.module

/** Koin DI module for [HomeViewModel] and its dependencies. */
val homeModule = module {
    single<HealthRepository> { DefaultHealthRepository(api = get()) }
    viewModel { HomeViewModel(repository = get()) }
}
