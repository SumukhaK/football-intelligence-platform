package com.footballintelligence.core.ui

import androidx.compose.foundation.layout.size
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.outlined.Shield
import androidx.compose.runtime.Composable
import androidx.compose.runtime.staticCompositionLocalOf
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.vector.rememberVectorPainter
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.dp
import coil.compose.AsyncImage

/**
 * Turns a team name into its crest image URL (ADR 020). The app provides it
 * once from its network config; previews keep the default and show the
 * placeholder.
 */
val LocalCrestUrl = staticCompositionLocalOf<(String) -> String?> { { null } }

/** Turns a league name into its emblem image URL (ADR 020), like [LocalCrestUrl]. */
val LocalEmblemUrl = staticCompositionLocalOf<(String) -> String?> { { null } }

/**
 * A team's crest, with a plain shield while it loads or when the team has none.
 * Decorative: the team's name is always shown or announced beside it.
 */
@Composable
fun TeamCrest(team: String, modifier: Modifier = Modifier, size: Dp = 24.dp) {
    CrestImage(LocalCrestUrl.current(team), modifier.size(size))
}

/** A league's emblem, decorative like [TeamCrest]. */
@Composable
fun LeagueEmblem(league: String, modifier: Modifier = Modifier, size: Dp = 24.dp) {
    CrestImage(LocalEmblemUrl.current(league), modifier.size(size))
}

@Composable
private fun CrestImage(url: String?, modifier: Modifier) {
    val placeholder = rememberVectorPainter(Icons.Outlined.Shield)
    AsyncImage(
        model = url,
        contentDescription = null,
        placeholder = placeholder,
        error = placeholder,
        fallback = placeholder,
        modifier = modifier,
    )
}
