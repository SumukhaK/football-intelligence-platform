package com.footballintelligence.feature.team

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowForwardIos
import androidx.compose.material.icons.filled.EmojiEvents
import androidx.compose.material.icons.filled.Shield
import androidx.compose.material3.Card
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.Icon
import androidx.compose.material3.ListItem
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.unit.dp
import com.footballintelligence.feature.team.resources.Res
import com.footballintelligence.feature.team.resources.cd_change_league
import com.footballintelligence.feature.team.resources.cd_change_team
import com.footballintelligence.feature.team.resources.settings_league
import com.footballintelligence.feature.team.resources.settings_my_team_section
import com.footballintelligence.feature.team.resources.settings_team
import org.jetbrains.compose.resources.stringResource

/** Settings section with the saved league and team, each opening the picker to change it. */
@Composable
fun MyTeamSettingsSection(
    favourite: FavouriteTeam,
    onChangeLeague: () -> Unit,
    onChangeTeam: () -> Unit,
    modifier: Modifier = Modifier,
) {
    Column(modifier = modifier, verticalArrangement = Arrangement.spacedBy(8.dp)) {
        Text(stringResource(Res.string.settings_my_team_section), style = MaterialTheme.typography.labelMedium)
        Card(modifier = Modifier.fillMaxWidth()) {
            Column {
                ChangeItem(
                    title = stringResource(Res.string.settings_league),
                    value = favourite.league,
                    icon = Icons.Default.EmojiEvents,
                    description = stringResource(Res.string.cd_change_league, favourite.league),
                    onClick = onChangeLeague,
                )
                HorizontalDivider()
                ChangeItem(
                    title = stringResource(Res.string.settings_team),
                    value = favourite.team,
                    icon = Icons.Default.Shield,
                    description = stringResource(Res.string.cd_change_team, favourite.team),
                    onClick = onChangeTeam,
                )
            }
        }
    }
}

@Composable
private fun ChangeItem(title: String, value: String, icon: ImageVector, description: String, onClick: () -> Unit) {
    ListItem(
        headlineContent = { Text(title) },
        supportingContent = { Text(value) },
        leadingContent = { Icon(icon, contentDescription = null) },
        trailingContent = { Icon(Icons.AutoMirrored.Filled.ArrowForwardIos, contentDescription = null) },
        modifier = Modifier
            .clickable(onClick = onClick)
            .semantics { contentDescription = description },
    )
}
