package com.footballintelligence.feature.prediction.di

import com.footballintelligence.feature.prediction.PredictionViewModel
import com.footballintelligence.feature.prediction.repository.DefaultPredictionRepository
import com.footballintelligence.feature.prediction.repository.PredictionRepository
import org.koin.androidx.viewmodel.dsl.viewModel
import org.koin.dsl.module

/** Koin DI module for the prediction and explanation flow. */
val predictionModule = module {
    single<PredictionRepository> { DefaultPredictionRepository(api = get()) }
    viewModel { PredictionViewModel(repository = get()) }
}
