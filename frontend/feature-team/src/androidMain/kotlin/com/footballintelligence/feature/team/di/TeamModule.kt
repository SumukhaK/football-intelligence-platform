package com.footballintelligence.feature.team.di

import android.content.Context
import com.footballintelligence.core.model.FavouriteTeamStore
import com.footballintelligence.feature.team.AccountPreferencesViewModel
import com.footballintelligence.feature.team.DefaultAccountPreferencesRepository
import com.footballintelligence.feature.team.FavouriteTeamViewModel
import com.footballintelligence.feature.team.MyTeamViewModel
import com.footballintelligence.feature.team.PreferencesFavouriteTeamStore
import com.footballintelligence.feature.team.ProjectedTableViewModel
import com.footballintelligence.feature.team.TeamPickerViewModel
import com.footballintelligence.feature.team.repository.AccountPreferencesRepository
import com.footballintelligence.feature.team.repository.DefaultTeamRepository
import com.footballintelligence.feature.team.repository.TeamRepository
import org.koin.android.ext.koin.androidContext
import org.koin.androidx.viewmodel.dsl.viewModel
import org.koin.dsl.module

/** Koin DI module for the favourite team: its store, the picker and My Team. */
val teamModule = module {
    single {
        PreferencesFavouriteTeamStore(
            androidContext().getSharedPreferences("favourite_team", Context.MODE_PRIVATE),
            get(),
        )
    }
    single<FavouriteTeamStore> { get<PreferencesFavouriteTeamStore>() }
    single<AccountPreferencesRepository> {
        DefaultAccountPreferencesRepository(api = get(), session = get(), cache = get())
    }
    viewModel { AccountPreferencesViewModel(repository = get()) }
    single<TeamRepository> { DefaultTeamRepository(api = get()) }
    viewModel { FavouriteTeamViewModel(store = get()) }
    viewModel { params ->
        TeamPickerViewModel(flow = params.get(), repository = get(), store = get(), preferences = get())
    }
    viewModel { MyTeamViewModel(repository = get(), store = get()) }
    viewModel { params -> ProjectedTableViewModel(outlook = params.get()) }
}
