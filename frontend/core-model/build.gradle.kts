plugins {
    id("football.kmp.library")
    alias(libs.plugins.kotlin.serialization)
}

android {
    namespace = "com.footballintelligence.core.model"
}

kotlin {
    sourceSets {
        commonMain.dependencies {
            implementation(libs.kotlinx.serialization.json)
            implementation(libs.kotlinx.coroutines.core)
        }
        commonTest.dependencies {
            implementation(libs.junit5.api)
            implementation(libs.junit5.params)
        }
    }
}
