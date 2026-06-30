package com.footballintelligence.core.designsystem

import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable

private val LightColorScheme = lightColorScheme(
    primary = GreenPrimary,
    onPrimary = GreenOnPrimary,
    primaryContainer = GreenPrimaryContainer,
    onPrimaryContainer = GreenOnPrimaryContainer,
    secondary = GreenSecondary,
    secondaryContainer = GreenSecondaryContainer,
    error = ErrorRed,
    errorContainer = ErrorRedContainer,
    surface = NeutralSurface,
)

private val DarkColorScheme = darkColorScheme(
    primary = GreenPrimaryContainer,
    onPrimary = GreenOnPrimaryContainer,
    primaryContainer = GreenPrimary,
    onPrimaryContainer = GreenOnPrimary,
    secondary = GreenSecondaryContainer,
    secondaryContainer = GreenSecondary,
    error = ErrorRedContainer,
    errorContainer = ErrorRed,
    surface = NeutralSurfaceDark,
)

/** Material 3 theme for Football Intelligence. */
@Composable
fun FootballTheme(
    darkTheme: Boolean = isSystemInDarkTheme(),
    content: @Composable () -> Unit,
) {
    val colorScheme = if (darkTheme) DarkColorScheme else LightColorScheme
    MaterialTheme(
        colorScheme = colorScheme,
        content = content,
    )
}
