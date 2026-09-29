package com.footballintelligence.app

import androidx.annotation.StringRes
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.CalendarMonth
import androidx.compose.material.icons.filled.Psychology
import androidx.compose.material.icons.filled.Settings
import androidx.compose.material.icons.filled.SportsSoccer
import androidx.compose.material3.Icon
import androidx.compose.material3.NavigationBar
import androidx.compose.material3.NavigationBarItem
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.res.stringResource
import com.footballintelligence.core.navigation.Screen

/** A top-level destination shown in the bottom bar. */
enum class TopLevelDestination(
    val screen: Screen,
    val icon: ImageVector,
    @StringRes val label: Int,
) {
    FIXTURES(Screen.Home, Icons.Default.CalendarMonth, R.string.nav_fixtures),
    PREDICT(Screen.Prediction, Icons.Default.SportsSoccer, R.string.nav_predict),
    ASSISTANT(Screen.Assistant, Icons.Default.Psychology, R.string.nav_assistant),
    SETTINGS(Screen.Settings, Icons.Default.Settings, R.string.nav_settings),
    ;

    companion object {
        /** The destination whose screen has [route], or null for a detail screen. */
        fun forRoute(route: String?): TopLevelDestination? = entries.firstOrNull { it.screen.route == route }
    }
}

/** Bottom navigation between the app's top-level screens. */
@Composable
fun BottomNavBar(
    current: TopLevelDestination,
    onSelect: (TopLevelDestination) -> Unit,
) {
    NavigationBar {
        TopLevelDestination.entries.forEach { destination ->
            NavigationBarItem(
                selected = destination == current,
                onClick = { onSelect(destination) },
                icon = { Icon(destination.icon, contentDescription = null) },
                label = { Text(stringResource(destination.label)) },
            )
        }
    }
}
