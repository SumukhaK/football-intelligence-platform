package com.footballintelligence.feature.team

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.combine
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.flow.update

/** Owns table ordering while sharing My Team's outlook without another network request. */
class ProjectedTableViewModel(outlook: StateFlow<SeasonOutlookUiState>) : ViewModel() {
    private val sort = MutableStateFlow(TableSort())

    val state: StateFlow<ProjectedTableUiState> = combine(outlook, sort) { content, selected ->
        val sorted = when (content) {
            is SeasonOutlookUiState.Success -> content.copy(
                outlook = content.outlook.copy(table = sortedTable(content.outlook.table, selected)),
            )
            else -> content
        }
        ProjectedTableUiState(sorted, selected)
    }.stateIn(viewModelScope, SharingStarted.Eagerly, ProjectedTableUiState(outlook.value))

    /** A new column starts ascending; tapping the selected column reverses it. */
    fun sortBy(column: TableColumn) {
        sort.update { current ->
            TableSort(column, ascending = current.column != column || !current.ascending)
        }
    }
}
