# build-logic

Gradle convention plugins that centralise build configuration across all modules.

## Purpose

Without convention plugins, every `build.gradle.kts` repeats the same SDK versions, compile options, and plugin declarations. Any change (e.g. bumping `compileSdk`) requires editing every module file. Convention plugins eliminate that duplication — module build files become declarations of intent, not boilerplate.

## Available Plugins

| Plugin ID | Class | Apply to |
|---|---|---|
| `football.android.application` | `AndroidApplicationConventionPlugin` | `:app` only |
| `football.android.library` | `AndroidLibraryConventionPlugin` | Android-only library modules |
| `football.kmp.library` | `KmpLibraryConventionPlugin` | Kotlin Multiplatform library modules |
| `football.android.compose` | `ComposeConventionPlugin` | Any module using Compose |

## Usage

In any module `build.gradle.kts`:

```kotlin
plugins {
    id("football.kmp.library")
    id("football.android.compose")
}
```

## Adding a New Plugin

1. Create the plugin class in `convention/src/main/kotlin/`.
2. Register it in `convention/build.gradle.kts` under `gradlePlugin { plugins { ... } }`.
3. Apply it to the relevant modules.
