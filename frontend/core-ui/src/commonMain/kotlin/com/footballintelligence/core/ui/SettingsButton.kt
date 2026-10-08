package com.footballintelligence.core.ui

import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Settings
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.runtime.Composable
import com.footballintelligence.core.ui.resources.Res
import com.footballintelligence.core.ui.resources.cd_settings
import org.jetbrains.compose.resources.stringResource

/** Top-bar settings icon shown at the top right of every top-level screen. */
@Composable
fun SettingsButton(onClick: () -> Unit) {
    IconButton(onClick = onClick) {
        Icon(Icons.Default.Settings, contentDescription = stringResource(Res.string.cd_settings))
    }
}
