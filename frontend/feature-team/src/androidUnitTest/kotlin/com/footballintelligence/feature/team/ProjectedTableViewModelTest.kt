package com.footballintelligence.feature.team

import com.footballintelligence.core.model.ErrorKind
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.test.UnconfinedTestDispatcher
import kotlinx.coroutines.test.resetMain
import kotlinx.coroutines.test.setMain
import org.junit.jupiter.api.AfterEach
import org.junit.jupiter.api.Assertions.assertEquals
import org.junit.jupiter.api.BeforeEach
import org.junit.jupiter.api.Test

/** Sorting must change row order without changing the model's ranks or favourite. */
@OptIn(ExperimentalCoroutinesApi::class)
class ProjectedTableViewModelTest {
    private val rows = listOf(
        TableRow(1, "Liverpool", 13, 80, 23, 92, 1, isFavourite = false),
        TableRow(2, "Arsenal", 15, 75, 14, 66, 9, isFavourite = true),
        TableRow(3, "Chelsea", 12, 71, 51, 79, 2, isFavourite = false),
    )
    private val outlook = SeasonOutlook("Arsenal", 2, 15, 75, 14, 66, 9, 1.2, 0.7, emptyList(), rows)
    private val source = MutableStateFlow<SeasonOutlookUiState>(SeasonOutlookUiState.Success(outlook))

    @BeforeEach
    fun setUp() = Dispatchers.setMain(UnconfinedTestDispatcher())

    @AfterEach
    fun tearDown() = Dispatchers.resetMain()

    @Test
    fun `each column starts ascending then toggles descending and ascending`() {
        val ascending = mapOf(
            TableColumn.POSITION to listOf("Liverpool", "Arsenal", "Chelsea"),
            TableColumn.TEAM to listOf("Arsenal", "Chelsea", "Liverpool"),
            TableColumn.CURRENT_POINTS to listOf("Chelsea", "Liverpool", "Arsenal"),
            TableColumn.PROJECTED_POINTS to listOf("Chelsea", "Arsenal", "Liverpool"),
            TableColumn.TITLE to listOf("Arsenal", "Liverpool", "Chelsea"),
            TableColumn.TOP_FOUR to listOf("Arsenal", "Chelsea", "Liverpool"),
            TableColumn.RELEGATION to listOf("Liverpool", "Chelsea", "Arsenal"),
        )
        for ((column, expected) in ascending) {
            val vm = ProjectedTableViewModel(source)
            vm.sortBy(column)
            assertEquals(expected, table(vm).map { it.team }, "$column ascending")
            vm.sortBy(column)
            assertEquals(expected.reversed(), table(vm).map { it.team }, "$column descending")
            vm.sortBy(column)
            assertEquals(expected, table(vm).map { it.team }, "$column ascending again")
        }
    }

    @Test
    fun `changing columns starts ascending and preserves original ranks and favourite`() {
        val vm = ProjectedTableViewModel(source)
        vm.sortBy(TableColumn.CURRENT_POINTS)
        vm.sortBy(TableColumn.CURRENT_POINTS)
        vm.sortBy(TableColumn.TEAM)
        assertEquals(listOf("Arsenal", "Chelsea", "Liverpool"), table(vm).map { it.team })
        assertEquals(listOf(2, 3, 1), table(vm).map { it.position })
        assertEquals(listOf("Arsenal"), table(vm).filter { it.isFavourite }.map { it.team })
        assertEquals(rows, (source.value as SeasonOutlookUiState.Success).outlook.table)
    }

    @Test
    fun `new source data retains the chosen sort and cached timestamp`() {
        val vm = ProjectedTableViewModel(source)
        vm.sortBy(TableColumn.CURRENT_POINTS)
        val updated = rows.map { if (it.team == "Chelsea") it.copy(currentPoints = 19) else it }
        source.value = SeasonOutlookUiState.Success(outlook.copy(table = updated), "8 Oct, 09:00")
        assertEquals(listOf("Liverpool", "Arsenal", "Chelsea"), table(vm).map { it.team })
        assertEquals("8 Oct, 09:00", (vm.state.value.content as SeasonOutlookUiState.Success).savedAt)
    }

    @Test
    fun `ties retain projected rank order and empty tables are safe`() {
        val tied = rows.reversed().map { it.copy(currentPoints = 10) }
        source.value = SeasonOutlookUiState.Success(outlook.copy(table = tied))
        val vm = ProjectedTableViewModel(source)
        vm.sortBy(TableColumn.CURRENT_POINTS)
        assertEquals(listOf("Liverpool", "Arsenal", "Chelsea"), table(vm).map { it.team })
        vm.sortBy(TableColumn.CURRENT_POINTS)
        assertEquals(listOf("Liverpool", "Arsenal", "Chelsea"), table(vm).map { it.team })
        source.value = SeasonOutlookUiState.Success(outlook.copy(table = emptyList()))
        assertEquals(emptyList<TableRow>(), table(vm))
    }

    @Test
    fun `loading and errors remain visible after sorting`() {
        val vm = ProjectedTableViewModel(source)
        vm.sortBy(TableColumn.TEAM)
        source.value = SeasonOutlookUiState.Loading
        assertEquals(SeasonOutlookUiState.Loading, vm.state.value.content)
        val error = SeasonOutlookUiState.Error("Unavailable", ErrorKind.SERVER_BUSY)
        source.value = error
        assertEquals(error, vm.state.value.content)
    }

    private fun table(vm: ProjectedTableViewModel) =
        (vm.state.value.content as SeasonOutlookUiState.Success).outlook.table
}
