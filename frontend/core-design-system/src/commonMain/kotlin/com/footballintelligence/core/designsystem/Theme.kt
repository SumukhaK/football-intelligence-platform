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
    tertiary = GoldTertiary,
    error = ErrorRed,
    errorContainer = ErrorRedContainer,
    surface = NeutralSurface,
    onSurface = NeutralOnSurface,
    background = NeutralSurface,
    onBackground = NeutralOnSurface,
    surfaceVariant = NeutralSurfaceVariant,
    onSurfaceVariant = NeutralOnSurfaceVariant,
    outline = NeutralOutline,
    outlineVariant = NeutralOutlineVariant,
    surfaceContainerLowest = NeutralContainerLowest,
    surfaceContainerLow = NeutralContainerLow,
    surfaceContainer = NeutralContainer,
    surfaceContainerHigh = NeutralContainerHigh,
    surfaceContainerHighest = NeutralContainerHighest,
)

private val DarkColorScheme = darkColorScheme(
    primary = GreenPrimaryContainer,
    onPrimary = GreenOnPrimaryContainer,
    primaryContainer = GreenPrimary,
    onPrimaryContainer = GreenOnPrimary,
    secondary = GreenSecondaryContainer,
    secondaryContainer = GreenSecondary,
    tertiary = GoldTertiaryDark,
    error = ErrorRedDark,
    errorContainer = ErrorRed,
    surface = NeutralSurfaceDark,
    onSurface = NeutralOnSurfaceDark,
    background = NeutralSurfaceDark,
    onBackground = NeutralOnSurfaceDark,
    surfaceVariant = NeutralSurfaceVariantDark,
    onSurfaceVariant = NeutralOnSurfaceVariantDark,
    outline = NeutralOutlineDark,
    outlineVariant = NeutralSurfaceVariantDark,
    surfaceContainerLowest = NeutralContainerLowestDark,
    surfaceContainerLow = NeutralContainerLowDark,
    surfaceContainer = NeutralContainerDark,
    surfaceContainerHigh = NeutralContainerHighDark,
    surfaceContainerHighest = NeutralContainerHighestDark,
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
