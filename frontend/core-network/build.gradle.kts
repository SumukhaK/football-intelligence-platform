plugins {
    id("football.kmp.library")
    alias(libs.plugins.kotlin.serialization)
}

android {
    namespace = "com.footballintelligence.core.network"
}

kotlin {
    sourceSets {
        commonMain.dependencies {
            implementation(project(":core-model"))
            implementation(libs.bundles.ktor.client)
            implementation(libs.kotlinx.serialization.json)
            implementation(libs.napier)
        }
        commonTest.dependencies {
            implementation(libs.ktor.client.mock)
            implementation(libs.kotlinx.coroutines.test)
            implementation(libs.junit5.api)
            implementation(libs.junit5.params)
        }
    }
}
