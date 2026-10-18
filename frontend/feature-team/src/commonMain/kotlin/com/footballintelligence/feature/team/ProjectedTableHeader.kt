package com.footballintelligence.feature.team

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.ArrowDownward
import androidx.compose.material.icons.filled.ArrowUpward
import androidx.compose.material.icons.filled.UnfoldMore
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.semantics.Role
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.semantics.stateDescription
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import com.footballintelligence.feature.team.resources.Res
import com.footballintelligence.feature.team.resources.sort_ascending
import com.footballintelligence.feature.team.resources.sort_descending
import com.footballintelligence.feature.team.resources.sort_not_selected
import com.footballintelligence.feature.team.resources.table_current_points
import com.footballintelligence.feature.team.resources.table_points_now
import com.footballintelligence.feature.team.resources.table_points_projected
import com.footballintelligence.feature.team.resources.table_position
import com.footballintelligence.feature.team.resources.table_projected_points
import com.footballintelligence.feature.team.resources.table_projected_rank
import com.footballintelligence.feature.team.resources.table_relegation
import com.footballintelligence.feature.team.resources.table_relegation_chance
import com.footballintelligence.feature.team.resources.table_sort_ascending
import com.footballintelligence.feature.team.resources.table_sort_descending
import com.footballintelligence.feature.team.resources.table_team
import com.footballintelligence.feature.team.resources.table_title_chance
import com.footballintelligence.feature.team.resources.table_title_probability
import com.footballintelligence.feature.team.resources.table_top_four
import com.footballintelligence.feature.team.resources.table_top_four_chance
import org.jetbrains.compose.resources.StringResource
import org.jetbrains.compose.resources.stringResource

internal val TABLE_IDENTITY_WIDTH = 200.dp
internal val TABLE_RANK_WIDTH = 48.dp
internal val TABLE_METRIC_WIDTH = 88.dp
internal val TABLE_METRIC_COLUMNS = listOf(
    TableColumn.CURRENT_POINTS,
    TableColumn.PROJECTED_POINTS,
    TableColumn.TITLE,
    TableColumn.TOP_FOUR,
    TableColumn.RELEGATION,
)

/** A header announces its full meaning, current direction and the next tap's action. */
@Composable
internal fun SortHeader(column: TableColumn, sort: TableSort, onSort: (TableColumn) -> Unit, modifier: Modifier) {
    val selected = sort.column == column
    val description = stringResource(column.description())
    val direction = stringResource(
        when {
            !selected -> Res.string.sort_not_selected
            sort.ascending -> Res.string.sort_ascending
            else -> Res.string.sort_descending
        },
    )
    val action = stringResource(
        if (selected && sort.ascending) Res.string.table_sort_descending else Res.string.table_sort_ascending,
        description,
    )
    val background = if (selected) MaterialTheme.colorScheme.primaryContainer else Color.Transparent
    val foreground = if (selected) {
        MaterialTheme.colorScheme.onPrimaryContainer
    } else {
        MaterialTheme.colorScheme.onSurfaceVariant
    }
    Row(
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.Center,
        modifier = modifier.heightIn(min = 56.dp).background(background)
            .semantics {
                contentDescription = description
                stateDescription = direction
            }
            .clickable(role = Role.Button, onClickLabel = action) { onSort(column) }.padding(horizontal = 4.dp),
    ) {
        Text(
            stringResource(column.label()),
            style = MaterialTheme.typography.labelLarge,
            color = foreground,
            fontWeight = FontWeight.Bold,
        )
        Icon(
            when {
                !selected -> Icons.Default.UnfoldMore
                sort.ascending -> Icons.Default.ArrowUpward
                else -> Icons.Default.ArrowDownward
            },
            contentDescription = null,
            tint = foreground,
            modifier = Modifier.size(16.dp),
        )
    }
}

private fun TableColumn.label(): StringResource = when (this) {
    TableColumn.POSITION -> Res.string.table_position
    TableColumn.TEAM -> Res.string.table_team
    TableColumn.CURRENT_POINTS -> Res.string.table_points_now
    TableColumn.PROJECTED_POINTS -> Res.string.table_points_projected
    TableColumn.TITLE -> Res.string.table_title_chance
    TableColumn.TOP_FOUR -> Res.string.table_top_four
    TableColumn.RELEGATION -> Res.string.table_relegation
}

private fun TableColumn.description(): StringResource = when (this) {
    TableColumn.POSITION -> Res.string.table_projected_rank
    TableColumn.TEAM -> Res.string.table_team
    TableColumn.CURRENT_POINTS -> Res.string.table_current_points
    TableColumn.PROJECTED_POINTS -> Res.string.table_projected_points
    TableColumn.TITLE -> Res.string.table_title_probability
    TableColumn.TOP_FOUR -> Res.string.table_top_four_chance
    TableColumn.RELEGATION -> Res.string.table_relegation_chance
}
