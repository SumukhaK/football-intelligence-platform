# frontend — Compose Multiplatform Android Application

Android client for the Football Intelligence Platform. Built with Compose Multiplatform (KMP), targeting Android API 26+.

## Stack

| Tool | Version | Role |
|---|---|---|
| Kotlin Multiplatform | 2.0.20 | Shared source across Android targets |
| Compose Multiplatform | 1.7.0 | Shared UI in `commonMain` |
| Ktor | 2.3.12 | HTTP client for FastAPI backend |
| Koin | 3.5.6 | Dependency injection |
| AndroidX Navigation Compose | 2.8.3 | Route-based navigation |
| AndroidX ViewModel | 2.8.3 | Lifecycle-scoped state holders |
| Kotlinx Serialization | 1.7.1 | JSON serialisation for API DTOs |
| Napier | 2.7.1 | KMP-compatible logging |
| JUnit 5 + MockK + Turbine | — | Unit testing |

## Module Structure

```
app/                   — Application entry point, NavHost, bottom bar, Koin assembly
feature-home/          — Fixtures by league (the first screen; tap one to predict it) and the backend status card
feature-prediction/    — Prediction, Result, and Explain screens
feature-assistant/     — AI Assistant chat screen
feature-settings/      — Settings, Model Information, and About screens
feature-team/          — Favourite team picker (first launch and Settings) and the My Team tab
core-network/          — Ktor API service, offline response cache, HTTP client factory
core-model/            — Domain models and network result types
core-design-system/    — Material 3 theme and colour palette
core-navigation/       — Screen routes sealed class
core-ui/               — Shared UI components (loading, errors, offline banner, pull to refresh)
core-common/           — Dispatchers and date/time formatting
core-testing/, feature-match/ — empty, nothing depends on them
```

On first launch the app asks for a favourite league, then a team from it, on
one screen with two steps. The choice is saved in SharedPreferences and the
picker is not shown again. A bottom bar switches between Fixtures, Predict,
My Team and Assistant; a settings icon at the top right of each opens Settings.
My Team shows the favourite team's next match: kick-off, the win/draw/loss pick
with its top three reasons, the three likeliest scores and the clean-sheet
chance. A match leaves the card two hours after kick-off. Settings shows the
saved league and team; changing either reopens the picker and, once saved,
restarts the app so every screen loads the new team. Every
API response is saved in the app's cache directory; when the server can't be
reached, screens show the saved data under an offline banner, and pulling down
on a screen fetches fresh data.

## Running Locally

1. Start the FastAPI backend (see [`backend/README.md`](../backend/README.md)). It must be reachable on `localhost:8000`.

2. Launch an Android emulator (API 26+). The app calls API v2 at `http://10.0.2.2:8000/v2` (emulator localhost alias).

3. Build and install:
   ```bash
   cd frontend
   ./gradlew assembleDebug
   adb install app/build/outputs/apk/debug/app-debug.apk
   ```

## Running Tests

```bash
./gradlew testDebugUnitTest
./gradlew spotlessCheck detekt
```

Repository and network tests live in `src/commonTest/`. ViewModel and
date-formatting tests live in `src/androidUnitTest/`, next to the `androidMain`
code they cover.

## Architecture

The app follows MVVM with strict layer separation:

- **Composables** (`commonMain`) — receive `UiState` and callbacks, contain no logic
- **ViewModels** (`androidMain`) — own `StateFlow<UiState>`, use `viewModelScope`
- **Repositories** (`commonMain`) — suspend functions returning `NetworkResult<T>`
- **API Service** (`commonMain`) — `FootballApiService` interface, `KtorFootballApiService` impl

UI state is a sealed class per screen with `Loading`, `Success`, and `Error` variants.

Screen text lives in each module's `src/commonMain/composeResources/values/strings.xml`
and is read with `stringResource(Res.string.key)`. Every screen has previews in its
module's `androidMain` source set, wrapped in `PreviewSurface` (ADR 010).

## Backend Base URL

The base URL is configured in `core-network/src/commonMain/.../NetworkConfig.kt`:

```kotlin
data class NetworkConfig(
    val baseUrl: String = "http://10.0.2.2:8000",
    val apiVersion: String = "v2",
    val timeoutMs: Long = 30_000L,
    val connectTimeoutMs: Long = 5_000L,
)
```

The short connect timeout makes an unreachable server fall back to saved data
quickly; `timeoutMs` bounds a request once connected.

Change this for physical device testing (use your machine's LAN IP).
