package com.footballintelligence.core.ui

import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.runtime.Composable
import com.footballintelligence.core.ui.resources.Res
import com.footballintelligence.core.ui.resources.cd_back
import org.jetbrains.compose.resources.stringResource

/** Top-bar back arrow shared by every screen below Home. */
@Composable
fun BackButton(onClick: () -> Unit) {
    IconButton(onClick = onClick) {
        Icon(Icons.AutoMirrored.Filled.ArrowBack, contentDescription = stringResource(Res.string.cd_back))
    }
}
