package ca.carleton.rewatch.presentation

import android.os.Bundle
import androidx.activity.ComponentActivity
import android.view.WindowManager
import androidx.activity.compose.setContent
import ca.carleton.rewatch.BuildConfig.IMU_TESTING
import ca.carleton.rewatch.presentation.navigation.NavigationStack
import ca.carleton.rewatch.presentation.views.TestingIMUViewModel

/**
 * Main Activity that gathers accelerometer data.
 */
class MainActivity : ComponentActivity() {

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        window.addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON)
        setTheme(android.R.style.Theme_DeviceDefault)

        setContent {
            if (!IMU_TESTING) {
                NavigationStack()
            } else {
                TestingIMUViewModel()
            }
        }
    }
}