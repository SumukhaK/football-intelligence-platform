package com.footballintelligence.app

import android.app.Application
import com.footballintelligence.app.di.networkModule
import com.footballintelligence.feature.assistant.di.assistantModule
import com.footballintelligence.feature.home.di.homeModule
import com.footballintelligence.feature.prediction.di.predictionModule
import com.footballintelligence.feature.settings.di.settingsModule
import io.github.aakira.napier.DebugAntilog
import io.github.aakira.napier.Napier
import org.koin.android.ext.koin.androidContext
import org.koin.android.ext.koin.androidLogger
import org.koin.core.context.startKoin

/** Application entry point. Starts Koin DI and Napier logging. */
class FootballApplication : Application() {
    override fun onCreate() {
        super.onCreate()
        if (BuildConfig.DEBUG) {
            Napier.base(DebugAntilog())
        }
        startKoin {
            androidLogger()
            androidContext(this@FootballApplication)
            modules(
                networkModule,
                homeModule,
                predictionModule,
                assistantModule,
                settingsModule,
            )
        }
    }
}
