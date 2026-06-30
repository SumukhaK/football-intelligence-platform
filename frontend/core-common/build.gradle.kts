plugins {
    id("football.kmp.library")
}

android {
    namespace = "com.footballintelligence.core.common"
}

kotlin {
    sourceSets {
        commonMain.dependencies {
            implementation(libs.napier)
            implementation(libs.kotlinx.coroutines.core)
        }
        commonTest.dependencies {
            implementation(libs.kotlinx.coroutines.test)
            implementation(libs.junit5.api)
            implementation(libs.junit5.params)
        }
    }
}
