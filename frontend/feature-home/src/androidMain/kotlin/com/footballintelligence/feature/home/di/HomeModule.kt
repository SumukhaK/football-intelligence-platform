package com.footballintelligence.feature.home.di

import com.footballintelligence.core.model.FavouriteTeamStore
import com.footballintelligence.feature.home.BackendStatusViewModel
import com.footballintelligence.feature.home.HomeViewModel
import com.footballintelligence.feature.home.repository.DefaultFixturesRepository
import com.footballintelligence.feature.home.repository.DefaultHealthRepository
import com.footballintelligence.feature.home.repository.FixturesRepository
import com.footballintelligence.feature.home.repository.HealthRepository
import org.koin.androidx.viewmodel.dsl.viewModel
import org.koin.dsl.module

/**
 * Koin DI module for [HomeViewModel], [BackendStatusViewModel] and their
 * repositories. The favourite team store comes from the team module.
 */
val homeModule = module {
    single<HealthRepository> { DefaultHealthRepository(api = get()) }
    single<FixturesRepository> { DefaultFixturesRepository(api = get()) }
    viewModel { HomeViewModel(repository = get(), favouriteLeague = get<FavouriteTeamStore>().load()?.league) }
    viewModel { BackendStatusViewModel(repository = get()) }
}
