# Android 2.6.2

18 October 2026. Frontend patch: version 2.6.2, code 12; staging is
`2.6.2-stg` with application ID `com.footballintelligence.app.stg`.
The hosted API stays on 2.6.0. No tag or GitHub Release is created.

Projected Table now uses the shared green toolbar and title capitalization.
The league-table layout has a sticky header, alternating rows, larger crests,
emphasized projected points and an explicit favourite-team highlight. Rank
and team stay visible while the numeric columns scroll together. Long team
names wrap; the heading and guide scroll away on short screens.
The supplied [Premier League Table design reference](https://dribbble.com/shots/6594148-Premier-League-Table)
informs the league-table layout while the app retains its existing theme.

Every heading sorts: projected rank, team name, current points, projected
points, first-place chance, top-four chance and bottom-three chance. First
tap on a newly selected column is ascending; repeat taps alternate descending
and ascending. Equal values retain projected-rank order. Sorting never
renumbers the model's ranks or changes the favourite team. The selected
heading shows an arrow, and accessibility labels announce its full name,
direction and next action.

The initial order remains the API's projected table. Now and Proj sort the
displayed whole points, and chances sort displayed whole percentages.
The outlook API has no official current rank or goal-difference tie-breakers,
so Now is a points ordering, not a reconstruction of official standings.
Top four and bottom three retain the definitions in ADR 023; they do not
claim exact qualification or relegation rules for every league.

A dedicated table ViewModel observes My Team's existing outlook. Sorting
requires no network request and preserves loading, errors and the offline
timestamp. No API, model, retrieval or account-storage changes are required.

Build with `frontend/gradlew.bat :app:assembleStagingDebug` after configuring
`staging.baseUrl` in ignored `frontend/local.properties`, or pass the
nonsecret address with `-PstagingBaseUrl=https://...`. Develop CI uploads the
`staging-debug-apk` artifact. CI has no Firebase config and sends no crash
reports; the ignored local Firebase config is preserved. Debug certificates
can differ between local and CI builds; switching certificates can require
uninstalling, which removes local sessions and preferences.

Validation: all 221 Android unit tests, Spotless and Detekt pass. The five
new table ViewModel cases cover every column, repeated taps, switching
columns, equal values, empty data, updated/cached data, loading and errors.
Temporarily breaking the direction toggle fails the regression test.
Android 12 emulator checks use a temporary fixture with the real ViewModel
and screen: all seven headings pass ascending, descending and ascending
again. Screenshots cover normal/dark themes and doubled system text with
animations disabled. The fixture is removed before the delivery build;
these checks do not exercise signed-in staging data.
