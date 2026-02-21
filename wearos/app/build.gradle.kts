plugins {
    alias(libs.plugins.android.application)
    alias(libs.plugins.kotlin.android)
    alias(libs.plugins.kotlin.compose)
}

android {
    namespace = "ca.carleton.rewatch"
    compileSdk {
        version = release(36)
    }

    buildFeatures {
        compose = true
        dataBinding = true
        buildConfig = true
    }

    defaultConfig {
        applicationId = "ca.carleton.rewatch"
        minSdk = 36
        targetSdk = 36
        versionCode = 1
        versionName = "1.0"

    }

    buildTypes {
        debug {
            buildConfigField("String", "API_ENDPOINT", "\"http://192.168.2.32:5000/\"") // Change this when debugging
        }

        release {
            isMinifyEnabled = false
            proguardFiles(
                getDefaultProguardFile("proguard-android-optimize.txt"),
                "proguard-rules.pro"
            )
            buildConfigField("String", "API_ENDPOINT", "path/to/azure") //@TODO
        }
    }
    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_11
        targetCompatibility = JavaVersion.VERSION_11
    }
    kotlinOptions {
        jvmTarget = "11"
    }
    useLibrary("wear-sdk")

}

dependencies {
    implementation(libs.play.services.wearable)
    implementation(platform(libs.compose.bom))
    implementation(libs.ui)
    implementation(libs.ui.graphics)
    implementation(libs.ui.tooling.preview)
    implementation(libs.compose.material)
    implementation(libs.compose.foundation)
    implementation(libs.wear.tooling.preview)
    implementation(libs.activity.compose)
    implementation(libs.core.splashscreen)
    implementation(libs.material3)
    implementation(libs.retrofit)
    implementation("com.squareup.retrofit2:converter-gson:2.3.0")
    implementation("androidx.wear.compose:compose-navigation:1.5.6")
    implementation("androidx.lifecycle:lifecycle-livedata-ktx:2.6.1")
    implementation("androidx.lifecycle:lifecycle-viewmodel-ktx:2.6.1")
    implementation("androidx.fragment:fragment-ktx:1.6.0")
    androidTestImplementation(platform(libs.compose.bom))
    androidTestImplementation(libs.ui.test.junit4)
    debugImplementation(libs.ui.tooling)
    debugImplementation(libs.ui.test.manifest)

    implementation(libs.gson)

    // This is for the Samsung Health Sensor SDK
    implementation(fileTree(mapOf("dir" to "libs", "include" to listOf("*.aar"))))
}