package ca.carleton.rewatch.presentation

import android.hardware.Sensor
import android.hardware.SensorEvent
import android.os.Bundle
import android.widget.TextView
import android.widget.ToggleButton
import androidx.activity.ComponentActivity
import android.hardware.SensorManager
import android.hardware.SensorEventListener
import android.util.Log
import androidx.activity.compose.setContent
import ca.carleton.rewatch.dataclasses.SensorReading
import ca.carleton.rewatch.presentation.navigation.NavigationStack

/**
 * Main Activity that gathers accelerometer data.
 */
class MainActivity : ComponentActivity() {

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        setTheme(android.R.style.Theme_DeviceDefault)

        setContent {
            NavigationStack()
        }
    }
}