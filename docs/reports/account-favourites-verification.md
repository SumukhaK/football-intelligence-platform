# Account Favourites Verification

Date: 19 October 2026. Scope: ADR 035 and the account-favourites plan.

## Implementation scope

- Backend: existing account adapters, authenticated preference router/schema/service,
  account provider errors, dependency wiring, fake Firestore and regression tests.
- Mobile: preference DTO/API/repository, account-scoped cache, navigation gate,
  session lifetime, picker saving/retry, settings cache consumer and tests.
- Documentation: ADR 035/index, API contract, implementation plan, READMEs and this report.
- No new dependency, account database, authentication system, release or cloud change.

## Migration and compatibility

Legacy account records without `favourite` read as explicit null; malformed saved
values are 503 errors. The server alone owns the preference. JSON merges under
its existing lock and atomic replacement; Firestore patches only the favourite.
Authentication writes omit that field so stale account snapshots cannot erase it.
Unknown account fields remain intact.

The cache uses canonical server email in its keys and an in-memory binding to
the originating token. Sign-out/token replacement makes that cache inaccessible
immediately; new cache instances wait for the server. Old unscoped `league` and
`team` keys are discarded, never uploaded. Loading and errors never route to
onboarding. Only successful explicit null does. Saves complete only on success.

Delayed reads, saves, rejected credentials and logout replies cannot mutate
another login. Cancellation propagates. A non-saveable navigation lifetime
prevents restored My Team from being constructed with an unconfirmed cache.

## Commands and observed results

Python commands ran from `ai/` with `PYTHONPATH` set to that directory using:
`D:\Anthropic\TestProjects\football-intelligence-platform\ai\.venv\Scripts\python.exe`
(Python 3.12.13). No staging accounts or credentials were used.

| Command | Result |
|---|---|
| `python -m pytest tests/backend/test_account_preferences.py -x -vv -s --no-cov --tb=short` before implementation | Failed as expected: new route returned 404 |
| `python -m pytest --cov --cov-report=term-missing` | 1,388 passed, 36 skipped, 83.73% coverage; 451.64 seconds |
| `python -m pytest tests/backend/test_account_preferences.py tests/backend/test_account_service.py tests/backend/test_firestore_account_store.py tests/backend/test_auth_endpoints.py -o addopts=--tb=short --no-cov` | Final run: 107 passed; 22.65 seconds, including all 53 preference cases |
| `python -m pytest tests/integration -o addopts=--tb=short --no-cov -rs` | 36 passed; 12.16 seconds, using the real local model |
| `python -m black --check backend/app/services/account_store.py backend/app/services/account_preferences_service.py backend/app/routers/account_preferences.py backend/app/schemas/account_preferences.py backend/app/dependencies.py tests/backend/test_account_preferences.py tests/backend/fake_firestore.py` | Passed |
| `python -m ruff check backend tests/backend/test_account_preferences.py tests/backend/fake_firestore.py` | Passed |
| `python -m mypy backend/app/services/account_store.py backend/app/services/account_preferences_service.py backend/app/routers/account_preferences.py backend/app/schemas/account_preferences.py backend/app/dependencies.py` | Passed: no issues in 5 source files |

The full Python run preceded the final two new-login recovery cases and OpenAPI
error-schema typing changes; the final focused run covered those changes.
The first full run lacked ignored model artifacts. Existing local
`models/latest/{model.joblib,config.json,metrics.json,refit.json}` and
`models/registry.json` were copied from the original checkout into previously
absent ignored worktree paths, then the real-model integration suite ran.
The source artifacts were not changed and no model was trained or published.

Android commands ran from `frontend/` with:
`JAVA_HOME=C:\Program Files\Java\jdk-19`,
`ANDROID_HOME=C:\Users\sumuk\AppData\Local\Android\Sdk`,
`GRADLE_USER_HOME=C:\Users\sumuk\.gradle`.

- New gate tests first failed because the DTO/repository/ViewModel were missing.
- The delayed logout regression failed before guarding the originating token.
- The cancellation regression failed before propagating cancellation.
- `gradlew.bat spotlessApply --offline --console=plain` applied formatting.
- Final `gradlew.bat spotlessCheck detekt :app:assembleLocalDebug :app:testLocalDebugUnitTest testDebugUnitTest --offline --console=plain` passed.
- JUnit XML reports contain 239 tests across 43 suites, including 2 app routing
  tests, with zero failures. APK: `frontend/app/build/outputs/apk/local/debug/app-local-debug.apk`.

Backend tests cover fresh/legacy accounts, invalid requests and stored values,
canonical catalog relationships, unauthorized/blocked accounts, account isolation,
provider/catalog/write failures, unrelated/unknown field preservation and stale
authentication writes. Recovery uses a new sign-in and client against the same
persisted account for both JSON and fake Firestore.

Mobile tests cover loading, successful favourite, explicit null, retry, failed
saves, duplicate taps, delayed reads/saves/logout, missing response fields,
account changes, sign-out, legacy cache and empty-cache install/upgrade recovery.
Routing tests assert that loading/errors cannot enter onboarding or home.

## Review and limitations

Independent review covered authorization, storage/catalog validation, narrow
writes, session/cancellation handling and navigation. The restoration ordering
issue found on cross-check was fixed and scoped re-review passed. Diff whitespace
checks passed.

No live Firestore, IAM, hosting, deployment, production data, physical device,
uninstall/reinstall or device process-death test was performed. Rotation/process
recreation resets tabs through the account gate; this is the intentional cost
of confirming preferences before creating feature ViewModels. Process recreation
is source-reviewed; UI state/routing and cache recreation have offline tests.

The updated app requires a successful server account read at startup. An older
backend returns a retryable error until the new API is deployed. Deploying this
change is outside this task. A previously device-only favourite must be selected
once if the server has none; unowned legacy data is never silently assigned.

Existing third-party warnings remain: Starlette/httpx deprecation and three SHAP
colour-map deprecations; Gradle 9 deprecation and the JVM test class-sharing notice.
Mypy notes unused third-party config sections when checking only these 5 files.
The bundled Android Studio JBR was incomplete; the installed JDK 19 worked.
Sandbox restrictions required elevated execution for installed tool caches and
managed worktree test writes; tests remained local/offline.

The original checkout stays on `develop` with its original untracked files.
Unrelated worktrees, football-dashboard, D9 and PR #19 were not modified.
Publication state is reported with the final result.
