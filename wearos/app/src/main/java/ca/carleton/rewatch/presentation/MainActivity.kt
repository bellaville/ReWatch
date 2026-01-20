package ca.carleton.rewatch.presentation

import android.hardware.Sensor
import android.hardware.SensorEvent
import android.os.Bundle
import android.widget.TextView
import android.widget.ToggleButton
import androidx.activity.ComponentActivity
import ca.carleton.rewatch.R
import android.hardware.SensorManager
import android.hardware.SensorEventListener
import android.util.Log
import ca.carleton.rewatch.BuildConfig
import ca.carleton.rewatch.dataclasses.SensorReading
import retrofit2.Retrofit

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

    val webAppUrl = Retrofit.Builder().baseUrl(BuildConfig.BASE_URL).build()
    val test = BuildConfig.BASE_URL

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        status = findViewById(R.id.statusText)
        accelX = findViewById(R.id.accel_x)
        accelY = findViewById(R.id.accel_y)
        accelZ = findViewById(R.id.accel_z)
        toggle = findViewById(R.id.toggle_button)
        toggle.isEnabled = true
        toggle.setOnClickListener {
            toggleClick()
        }

        sensorManager = getSystemService(SENSOR_SERVICE) as SensorManager
        val sensor : Sensor? = sensorManager.getDefaultSensor(Sensor.TYPE_LINEAR_ACCELERATION)
        sensorManager.registerListener(listener, sensor, SensorManager.SENSOR_DELAY_NORMAL)
        status.text = "Status: Sensor loaded"
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

    private fun transferData(data: List<SensorReading>) {
        Log.d("ReWatch", "${data}")
    }
}