plugins {
    id("football.kmp.library")
}

android {
    namespace = "com.footballintelligence.core.testing"
}

kotlin {
    sourceSets {
        commonMain.dependencies {
            implementation(libs.kotlinx.coroutines.test)
            implementation(libs.turbine)
            implementation(libs.mockk)
            implementation(libs.junit5.api)
            implementation(libs.junit5.params)
        }
    }
}
