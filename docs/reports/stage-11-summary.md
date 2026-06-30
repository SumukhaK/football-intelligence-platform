# Stage 11 — Compose Multiplatform Android Application

## Summary

Stage 11 delivers the Android client for the Football Intelligence Platform. The application is built with Compose Multiplatform (KMP) and connects to the FastAPI backend via Ktor HTTP client. It covers all five API endpoints and eight distinct screens.

---

## Deliverables

### Screens Implemented

| Screen | Route | Description |
|---|---|---|
| Home | `home` | Health status dashboard with backend availability indicators |
| Match Prediction | `prediction` | Team selection with Premier League dropdown menus |
| Prediction Result | `prediction_result` | Outcome probabilities with progress bars |
| Explain Prediction | `explain_prediction` | SHAP feature contributions (positive and negative) |
| AI Assistant Chat | `assistant` | RAG-backed conversational interface |
| Model Information | `model_info` | Training metadata and evaluation metrics |
| Settings | `settings` | Navigation hub to model info and about |
| About | `about` | App version, technology stack, and dataset info |

### API Integrations

| Endpoint | Used by |
|---|---|
| `GET /health` | Home screen |
| `GET /model` | Model Information screen |
| `POST /predict` | Match Prediction → Prediction Result |
| `POST /explain` | Explain Prediction screen |
| `POST /assistant/chat` | AI Assistant Chat |

---

## Architecture

### Layer Structure

```
app/                   — NavHost, DI assembly, Application class, MainActivity
feature-home/          — Health status UI + HealthRepository + HomeViewModel
feature-prediction/    — Prediction + Result + Explain screens + PredictionViewModel
feature-assistant/     — Chat screen + AssistantRepository + AssistantViewModel
feature-settings/      — Settings + ModelInfo + About screens + SettingsViewModel
core-network/          — KtorFootballApiService, HttpClientFactory, FootballApiService
core-model/            — Domain models: NetworkResult, HealthStatus, Prediction, etc.
core-design-system/    — FootballTheme, colour palette (Material 3)
core-navigation/       — Screen sealed class with all 8 routes
core-ui/               — Shared: LoadingView, ErrorView, StatusChip
core-common/           — DispatcherProvider interface
```

### MVVM Pattern

- Composables in `commonMain` — receive `UiState` and lambda callbacks only, no logic
- ViewModels in `androidMain` — hold `StateFlow<UiState>`, scoped to `viewModelScope`
- Repositories in `commonMain` — suspend functions, return `NetworkResult<T>`
- Sealed UI state per screen: `Loading`, `Success(data)`, `Error(message)`

### ViewModel Sharing

`PredictionViewModel` is shared across Prediction → Result → Explain via `navController.getBackStackEntry(Screen.Prediction.route)` as the `ViewModelStoreOwner`.

---

## Known Limitation: Feature Vector

The prediction and explain endpoints require 42 engineered pre-match features (Elo ratings, rolling form, head-to-head, etc.). The app cannot compute these at runtime because the raw match data is not available on device.

`buildNeutralFeatures()` in `core-model` provides 44 neutral/average values so the prediction flow is fully exercisable for demonstration. This is documented in `core-model/src/commonMain/kotlin/com/footballintelligence/core/model/Team.kt`.

---

## Testing

| Module | Tests | Coverage |
|---|---|---|
| feature-home | `HealthRepositoryTest` — 2 tests | Repository contract |
| feature-prediction | `PredictionRepositoryTest` — 3 tests | Success + error paths |
| feature-assistant | `AssistantRepositoryTest` — 2 tests | Chat happy + error path |
| feature-settings | `ModelInfoRepositoryTest` — 2 tests | Success + error paths |

All tests use MockK for mocking `FootballApiService` and run via JUnit 5.

```
./gradlew test — BUILD SUCCESSFUL
```

---

## Build

```
./gradlew assembleDebug — BUILD SUCCESSFUL
```

APK output: `app/build/outputs/apk/debug/app-debug.apk`

---

## Dependencies Added

| Dependency | Reason |
|---|---|
| `androidx.activity:activity-compose:1.9.2` | `setContent {}` in MainActivity |
| `androidx.navigation:navigation-compose:2.8.3` | NavHost + composable destinations |
| `io.insert-koin:koin-android:3.5.6` | Koin AndroidContext + viewModel DSL |
| `io.insert-koin:koin-androidx-compose:3.5.6` | `koinViewModel()` in NavHost |
| `io.ktor:ktor-client-android:2.3.12` | Android Ktor engine in app module |

---

## Files Changed

- `frontend/gradle/libs.versions.toml` — added navigation, activity, fixed koin-compose version
- `frontend/app/build.gradle.kts` — feature + library dependencies
- `frontend/core-network/build.gradle.kts` — added `core-model` dependency
- `frontend/feature-home/build.gradle.kts` — added `materialIconsExtended`
- `frontend/feature-settings/build.gradle.kts` — added `materialIconsExtended`
- All `feature-*/` and `core-*/` source files — new implementation
