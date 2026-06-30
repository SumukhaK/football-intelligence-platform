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
            implementation(project(":core-common"))
            implementation(project(":core-model"))
            implementation(project(":core-network"))
            implementation(project(":core-ui"))
            implementation(project(":core-design-system"))
            implementation(project(":core-navigation"))
            implementation(compose.runtime)
            implementation(compose.foundation)
            implementation(compose.material3)
            implementation(compose.ui)
            implementation(libs.kotlinx.coroutines.core)
        }
        androidMain.dependencies {
            implementation(libs.koin.android)
            implementation(libs.bundles.lifecycle.compose)
        }
        commonTest.dependencies {
            implementation(libs.bundles.testing.unit)
            implementation(libs.kotlinx.coroutines.test)
        }
    }
}
