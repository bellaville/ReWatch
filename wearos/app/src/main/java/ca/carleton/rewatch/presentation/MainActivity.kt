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

    private lateinit var status : TextView
    private lateinit var accelX : TextView
    private lateinit var accelY : TextView
    private lateinit var accelZ : TextView
    private lateinit var toggle : ToggleButton
    private var isRecording: Boolean = false
    private var recordedData = mutableListOf<SensorReading>()
    private lateinit var sensorManager : SensorManager

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        setTheme(android.R.style.Theme_DeviceDefault)

        setContent {
            NavigationStack()
        }
    }

    private val listener = object : SensorEventListener {
        override fun onAccuracyChanged(sensor: Sensor?, accuracy: Int) {
        }

        override fun onSensorChanged(event: SensorEvent?) {
            event?.let {
                if (isRecording && it.sensor.type == Sensor.TYPE_LINEAR_ACCELERATION) {

                    var x : Float = it.values[0]
                    var y : Float = it.values[1]
                    var z : Float = it.values[2]

                    val reading = SensorReading(
                        timestamp = System.currentTimeMillis(),
                        x = x,
                        y = y,
                        z = z
                    )

                    recordedData.add(reading)

                    accelX.text = "X: $x"
                    accelY.text = "Y: $y"
                    accelZ.text = "Z: $z"
                }
            }
        }
    }

    override fun onDestroy() {
        super.onDestroy()
        sensorManager.unregisterListener(listener)
    }

    fun toggleClick() {
        if(!isRecording) {
            isRecording = true
            status.text = "Status: Recording..."
        } else {
            isRecording = false
            status.text = "Status: idle..."
            accelX.text = "X: 0"
            accelY.text = "Y: 0"
            accelZ.text = "Z: 0"
            handleFinishedRecording()
        }
    }

    private fun handleFinishedRecording() {
        Log.d("ReWatch", "Recording finished. Captured ${recordedData.size} data points.")
        Log.v("ReWatch", "Recording finished. Captured Data:\n${recordedData}")
        recordedData.clear()
    }
}