package com.footballintelligence.core.ui

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.CloudOff
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.pulltorefresh.PullToRefreshBox
import androidx.compose.material3.pulltorefresh.rememberPullToRefreshState
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.graphicsLayer
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.unit.dp
import com.footballintelligence.core.ui.resources.Res
import com.footballintelligence.core.ui.resources.offline_banner
import org.jetbrains.compose.resources.stringResource

/**
 * Shown above content that came from the offline cache, with when it was saved.
 * Renders nothing when [savedAt] is null (the data is fresh).
 */
@Composable
fun OfflineBanner(savedAt: String?, modifier: Modifier = Modifier) {
    if (savedAt == null) return
    val text = stringResource(Res.string.offline_banner, savedAt)
    Row(
        modifier = modifier
            .fillMaxWidth()
            .background(MaterialTheme.colorScheme.tertiaryContainer)
            .padding(horizontal = 16.dp, vertical = 8.dp)
            .semantics { contentDescription = text },
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.spacedBy(8.dp),
    ) {
        Icon(
            Icons.Default.CloudOff,
            contentDescription = null,
            tint = MaterialTheme.colorScheme.onTertiaryContainer,
            modifier = Modifier.size(16.dp),
        )
        Text(
            text,
            style = MaterialTheme.typography.labelMedium,
            color = MaterialTheme.colorScheme.onTertiaryContainer,
        )
    }
}

/** Pull-to-refresh wrapper used by every data screen. */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun RefreshableContent(
    isRefreshing: Boolean,
    onRefresh: () -> Unit,
    modifier: Modifier = Modifier,
    content: @Composable () -> Unit,
) {
    val state = rememberPullToRefreshState()
    PullToRefreshBox(
        isRefreshing = isRefreshing,
        onRefresh = onRefresh,
        modifier = modifier.fillMaxSize(),
        state = state,
        indicator = {
            // The Kick-off ring replaces the default spinner, fading in as the user pulls.
            val pulled = state.distanceFraction.coerceIn(0f, 1f)
            if (isRefreshing || pulled > 0f) {
                Surface(
                    shape = CircleShape,
                    shadowElevation = 3.dp,
                    modifier = Modifier
                        .align(Alignment.TopCenter)
                        .padding(top = 12.dp)
                        .graphicsLayer { alpha = if (isRefreshing) 1f else pulled },
                ) {
                    KickoffLoader(size = 34.dp, modifier = Modifier.padding(6.dp))
                }
            }
        },
    ) {
        Box(Modifier.fillMaxSize()) { content() }
    }
}
