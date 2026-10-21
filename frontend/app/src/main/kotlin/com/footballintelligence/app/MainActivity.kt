package com.footballintelligence.app

import android.graphics.Color
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.SystemBarStyle
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.runtime.CompositionLocalProvider
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.key
import androidx.compose.runtime.remember
import androidx.core.splashscreen.SplashScreen.Companion.installSplashScreen
import androidx.lifecycle.lifecycleScope
import androidx.navigation.compose.rememberNavController
import com.footballintelligence.core.designsystem.FootballTheme
import com.footballintelligence.core.network.AuthApiService
import com.footballintelligence.core.network.AuthSession
import com.footballintelligence.core.network.NetworkConfig
import com.footballintelligence.core.ui.LocalCrestUrl
import com.footballintelligence.core.ui.LocalEmblemUrl
import kotlinx.coroutines.launch
import org.koin.android.ext.android.inject
import java.util.UUID

/** Entry point activity. Hosts the root NavHost inside [FootballTheme]. */
class MainActivity : ComponentActivity() {
    private val networkConfig: NetworkConfig by inject()
    private val session: AuthSession by inject()
    private val authApi: AuthApiService by inject()

    override fun onCreate(savedInstanceState: Bundle?) {
        // Must run before super.onCreate so the Kick-off launch screen hands over cleanly.
        installSplashScreen()
        super.onCreate(savedInstanceState)
        // Every screen has a green bar under the status bar, so its icons stay light.
        enableEdgeToEdge(statusBarStyle = SystemBarStyle.dark(Color.TRANSPARENT))
        setContent {
            FootballTheme {
                CompositionLocalProvider(
                    LocalCrestUrl provides networkConfig::crestUrl,
                    LocalEmblemUrl provides networkConfig::emblemUrl,
                ) {
                    val token by session.token.collectAsState()
                    // Restoring a feature before account confirmation could construct it with an empty cache.
                    val navigationLifetime = remember { UUID.randomUUID().toString() }
                    key(token, navigationLifetime) {
                        val navController = rememberNavController()
                        AppNavigation(navController = navController, signedIn = token != null)
                    }
                }
            }
        }
    }

    /**
     * Starts the server booting while the user looks at the first screen. On
     * every return to the app too, since the server scales to zero when idle.
     */
    override fun onStart() {
        super.onStart()
        lifecycleScope.launch { authApi.wake() }
    }
}
