package com.footballintelligence.feature.assistant.di

import com.footballintelligence.feature.assistant.AssistantViewModel
import com.footballintelligence.feature.assistant.repository.AssistantRepository
import com.footballintelligence.feature.assistant.repository.DefaultAssistantRepository
import org.koin.androidx.viewmodel.dsl.viewModel
import org.koin.dsl.module

/** Koin DI module for the AI assistant chat feature. */
val assistantModule = module {
    single<AssistantRepository> { DefaultAssistantRepository(api = get()) }
    viewModel { AssistantViewModel(repository = get()) }
}
