package com.footballintelligence.feature.team

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowForwardIos
import androidx.compose.material3.Card
import androidx.compose.material3.Icon
import androidx.compose.material3.ListItem
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.unit.dp
import com.footballintelligence.core.ui.TeamCrest
import com.footballintelligence.feature.team.resources.Res
import com.footballintelligence.feature.team.resources.cd_change_my_team
import com.footballintelligence.feature.team.resources.settings_my_team
import com.footballintelligence.feature.team.resources.settings_my_team_section
import com.footballintelligence.feature.team.resources.settings_my_team_value
import org.jetbrains.compose.resources.stringResource

/** Settings section with the saved team's crest and name; tapping it opens the picker. */
@Composable
fun MyTeamSettingsSection(favourite: FavouriteTeam, onChange: () -> Unit, modifier: Modifier = Modifier) {
    val description = stringResource(Res.string.cd_change_my_team, favourite.team, favourite.league)
    Column(modifier = modifier, verticalArrangement = Arrangement.spacedBy(8.dp)) {
        Text(stringResource(Res.string.settings_my_team_section), style = MaterialTheme.typography.labelMedium)
        Card(modifier = Modifier.fillMaxWidth()) {
            ListItem(
                headlineContent = { Text(stringResource(Res.string.settings_my_team)) },
                supportingContent = {
                    Text(stringResource(Res.string.settings_my_team_value, favourite.team, favourite.league))
                },
                leadingContent = { TeamCrest(favourite.team, size = 40.dp) },
                trailingContent = { Icon(Icons.AutoMirrored.Filled.ArrowForwardIos, contentDescription = null) },
                modifier = Modifier
                    .clickable(onClick = onChange)
                    .semantics { contentDescription = description },
            )
        }
    }
}
