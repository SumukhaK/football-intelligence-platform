package com.footballintelligence.core.ui

import androidx.compose.material3.Surface
import androidx.compose.runtime.Composable
import com.footballintelligence.core.designsystem.FootballTheme
import org.jetbrains.compose.resources.ExperimentalResourceApi
import org.jetbrains.compose.resources.PreviewContextConfigurationEffect

/**
 * Wraps a @Preview in the app theme.
 *
 * Compose resources need the Android context to load strings, which Android
 * Studio's preview does not provide on its own; the effect supplies it.
 */
@OptIn(ExperimentalResourceApi::class)
@Composable
fun PreviewSurface(content: @Composable () -> Unit) {
    PreviewContextConfigurationEffect()
    FootballTheme {
        Surface(content = content)
    }
}
