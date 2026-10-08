package com.footballintelligence.app

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.runtime.CompositionLocalProvider
import androidx.core.splashscreen.SplashScreen.Companion.installSplashScreen
import androidx.navigation.compose.rememberNavController
import com.footballintelligence.core.designsystem.FootballTheme
import com.footballintelligence.core.network.NetworkConfig
import com.footballintelligence.core.ui.LocalCrestUrl
import org.koin.android.ext.android.inject

/** Entry point activity. Hosts the root NavHost inside [FootballTheme]. */
class MainActivity : ComponentActivity() {
    private val networkConfig: NetworkConfig by inject()

    override fun onCreate(savedInstanceState: Bundle?) {
        // Must run before super.onCreate so the Kick-off launch screen hands over cleanly.
        installSplashScreen()
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        setContent {
            FootballTheme {
                CompositionLocalProvider(LocalCrestUrl provides networkConfig::crestUrl) {
                    val navController = rememberNavController()
                    AppNavigation(navController = navController)
                }
            }
        }
    }
}
