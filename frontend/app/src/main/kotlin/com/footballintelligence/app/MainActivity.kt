package com.footballintelligence.app

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.navigation.compose.rememberNavController
import com.footballintelligence.core.designsystem.FootballTheme

/** Entry point activity. Hosts the root NavHost inside [FootballTheme]. */
class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        setContent {
            FootballTheme {
                val navController = rememberNavController()
                AppNavigation(navController = navController)
            }
        }
    }
}
