# :feature-team

The favourite team: the picker (first launch and Settings) and the My Team tab.

## Ownership

Presentation layer. Depends on `core-common`, `core-model`, `core-network`, `core-ui`, `core-design-system`.

## Contents

- `TeamPickerScreen`, `TeamPickerViewModel` — league emblems, then the league's crests; saving finishes onboarding or relaunches the app.
- `MyTeamScreen`, `MyTeamViewModel` — the favourite team's next match card and the season outlook (ADR 023), with `ProjectedTableScreen` behind it.
- `MyTeamSettingsSection` — the My team row in Settings.
- `FavouriteTeamViewModel`, `PreferencesFavouriteTeamStore` — the saved team, read once at launch.
- `TeamRepository` — teams, fixtures, predictions, insights and the outlook.

## Constraints

- TDD: ViewModel tests written before implementation.
- No hardcoded strings.
