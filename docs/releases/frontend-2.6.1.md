# Android 2.6.1

18 October 2026. Frontend patch: version 2.6.1, code 11; staging is
`2.6.1-stg` with application ID `com.footballintelligence.app.stg`.
The hosted API stays on 2.6.0. No tag or GitHub Release is created.

New chat is hidden during a reply, and the ViewModel ignores reset attempts
until success or failure. Completed conversations still reset normally;
the four-exchange signed history, duplicate-send guard and 30-minute idle
reset stay in place (ADR 030).

The refused "How does the app pick a winner?" starter is removed. The other
starter, "Who is favourite in my team's next match?", is withheld as well:
its prior comment established only local-model validation. Neither starter
has been evaluated against the staging model/index in this patch, including
with favourite-team context, so none is offered. No grounding threshold,
retrieval, index, model or backend behavior changes. The existing conversation
evaluation includes harmful safety cases and is not run against the owner's
hosted account. No provider credentials are accessed.

Account-backed favourite-team restoration is explicitly deferred in
[the application backlog](../plans/hosting-execution-tracker.md#deferred-application-backlog).
Uninstall currently removes the device-only choice; an existing account does
not bypass onboarding.

Frontend CI builds the staging debug variant with the verified nonsecret
staging API URL and uploads `staging-debug-apk`, failing if the APK is absent.
CI has no staging Firebase configuration, so its APK sends no crash reports
(ADR 028). The owner's ignored local Firebase configuration is preserved.
CI and local debug builds can use different debug signing certificates;
installing across them may require uninstalling first, which removes local
preferences and sessions.

Validation: the three new deferred-response cases failed at the reset assertion
before the guard, then all 12 ViewModel cases passed. The full Android command
`testDebugUnitTest spotlessCheck detekt :app:assembleStagingDebug` passed.
It reports existing Gradle deprecation/JVM test-agent notices, with no lint
failures. Delivery and UI evidence are recorded in the patch PR and build run.
