pluginManagement {
    includeBuild("build-logic")
    repositories {
        google {
            content {
                includeGroupByRegex("com\\.android.*")
                includeGroupByRegex("com\\.google.*")
                includeGroupByRegex("androidx.*")
            }
        }
        mavenCentral()
        gradlePluginPortal()
    }
}

dependencyResolutionManagement {
    repositoriesMode.set(RepositoriesMode.FAIL_ON_PROJECT_REPOS)
    repositories {
        google {
            content {
                includeGroupByRegex("com\\.android.*")
                includeGroupByRegex("com\\.google.*")
                includeGroupByRegex("androidx.*")
            }
        }
        mavenCentral()
    }
}

rootProject.name = "football-intelligence"

include(":app")
include(":core-common")
include(":core-ui")
include(":core-design-system")
include(":core-navigation")
include(":core-network")
include(":core-model")
include(":core-testing")
include(":feature-home")
include(":feature-prediction")
include(":feature-match")
include(":feature-team")
include(":feature-assistant")
include(":feature-settings")
