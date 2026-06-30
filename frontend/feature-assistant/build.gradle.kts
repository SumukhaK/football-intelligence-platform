plugins {
    id("football.kmp.library")
    id("football.android.compose")
}

android {
    namespace = "com.footballintelligence.feature.assistant"
}

kotlin {
    sourceSets {
        commonMain.dependencies {
            implementation(compose.runtime)
            implementation(compose.foundation)
            implementation(compose.material3)
            implementation(libs.kotlinx.coroutines.core)
            implementation(libs.koin.android)
        }
        commonTest.dependencies {
            implementation(libs.bundles.testing.unit)
        }
    }
}
