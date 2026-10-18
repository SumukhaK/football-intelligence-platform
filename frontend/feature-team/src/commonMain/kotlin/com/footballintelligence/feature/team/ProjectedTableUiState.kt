package com.footballintelligence.feature.team

/** The displayed columns, each sortable by its displayed value. */
enum class TableColumn { POSITION, TEAM, CURRENT_POINTS, PROJECTED_POINTS, TITLE, TOP_FOUR, RELEGATION }

/** A null column means no header has been tapped; the API's projected order is shown. */
data class TableSort(val column: TableColumn? = null, val ascending: Boolean = true)

/** Source loading/error/cache state plus the selected table sort. */
data class ProjectedTableUiState(val content: SeasonOutlookUiState, val sort: TableSort = TableSort())

/** Sort a copy, retaining projected ranks as a stable tie-breaker in either direction. */
internal fun sortedTable(rows: List<TableRow>, sort: TableSort): List<TableRow> {
    val comparator = when (sort.column) {
        null -> return rows
        TableColumn.POSITION -> compareBy<TableRow> { it.position }
        TableColumn.TEAM -> compareBy { it.team.lowercase() }
        TableColumn.CURRENT_POINTS -> compareBy { it.currentPoints }
        TableColumn.PROJECTED_POINTS -> compareBy { it.expectedPoints }
        TableColumn.TITLE -> compareBy { it.titlePercent }
        TableColumn.TOP_FOUR -> compareBy { it.topFourPercent }
        TableColumn.RELEGATION -> compareBy { it.relegationPercent }
    }
    val directed = if (sort.ascending) comparator else comparator.reversed()
    return rows.sortedWith(directed.thenBy { it.position }.thenBy { it.team })
}
