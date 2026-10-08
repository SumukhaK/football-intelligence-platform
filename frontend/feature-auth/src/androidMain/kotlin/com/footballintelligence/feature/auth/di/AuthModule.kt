package com.footballintelligence.feature.auth.di

import android.content.Context
import com.footballintelligence.core.model.TokenStore
import com.footballintelligence.feature.auth.AuthViewModel
import com.footballintelligence.feature.auth.ConsentViewModel
import com.footballintelligence.feature.auth.PreferencesTokenStore
import com.footballintelligence.feature.auth.SignOutViewModel
import com.footballintelligence.feature.auth.repository.AuthRepository
import com.footballintelligence.feature.auth.repository.DefaultAuthRepository
import org.koin.android.ext.koin.androidContext
import org.koin.androidx.viewmodel.dsl.viewModel
import org.koin.dsl.module

/** Koin DI module for sign-in, the notice and sign-out (ADR 022). */
val authModule = module {
    single<TokenStore> {
        PreferencesTokenStore(androidContext().getSharedPreferences("session", Context.MODE_PRIVATE))
    }
    single<AuthRepository> { DefaultAuthRepository(api = get(), session = get()) }
    viewModel { AuthViewModel(repository = get()) }
    viewModel { ConsentViewModel(repository = get()) }
    viewModel { SignOutViewModel(repository = get()) }
}
