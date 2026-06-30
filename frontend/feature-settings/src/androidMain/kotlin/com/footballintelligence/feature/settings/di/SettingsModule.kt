package com.footballintelligence.feature.settings.di

import com.footballintelligence.feature.settings.SettingsViewModel
import com.footballintelligence.feature.settings.repository.DefaultModelInfoRepository
import com.footballintelligence.feature.settings.repository.ModelInfoRepository
import org.koin.androidx.viewmodel.dsl.viewModel
import org.koin.dsl.module

/** Koin DI module for settings, model info, and about screens. */
val settingsModule = module {
    single<ModelInfoRepository> { DefaultModelInfoRepository(api = get()) }
    viewModel { SettingsViewModel(repository = get()) }
}
