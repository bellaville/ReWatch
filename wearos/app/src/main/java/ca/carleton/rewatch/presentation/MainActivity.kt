package ca.carleton.rewatch.presentation

import android.Manifest
import android.content.Context
import android.content.pm.PackageManager
import android.hardware.Sensor
import android.hardware.SensorEvent
import android.health.connect.HealthConnectException
import android.os.Bundle
import android.widget.TextView
import android.widget.ToggleButton
import androidx.activity.ComponentActivity
import androidx.activity.result.contract.ActivityResultContracts
import androidx.core.app.ActivityCompat
import ca.carleton.rewatch.R


import com.samsung.android.service.health.tracking.*
import com.samsung.android.service.health.tracking.data.*

import android.hardware.SensorManager
import android.hardware.SensorEventListener
import kotlin.math.abs


class MainActivity : ComponentActivity() {
    private var healthTrackingService : HealthTrackingService? = null
    private var accelTracker : HealthTracker? = null

    private lateinit var status : TextView
    private lateinit var accelX : TextView
    private lateinit var accelY : TextView
    private lateinit var accelZ : TextView
    private lateinit var toggle : ToggleButton

    private lateinit var sensorManager : SensorManager

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        status = findViewById(R.id.statusText)
        accelX = findViewById(R.id.accel_x)
        accelY = findViewById(R.id.accel_y)
        accelZ = findViewById(R.id.accel_z)
        toggle = findViewById(R.id.toggle_button)
        toggle.isEnabled = true

        sensorManager = getSystemService(SENSOR_SERVICE) as SensorManager
        var sensor : Sensor? = sensorManager.getDefaultSensor(Sensor.TYPE_ACCELEROMETER)
        sensorManager.registerListener(listener, sensor, SensorManager.SENSOR_DELAY_NORMAL)

        status.text = "Sensor loaded"
    }

    private val listener = object : SensorEventListener {
        override fun onAccuracyChanged(sensor: Sensor?, accuracy: Int) {
        }

        override fun onSensorChanged(event: SensorEvent?) {
            var x : Float = event!!.values[0]
            var y : Float = event.values[1]
            var z : Float = event.values[2]

            accelX.text = "X: $x"
            accelY.text = "Y: $y"
            accelZ.text = "Z: $z"
        }
    }

    override fun onDestroy() {
        super.onDestroy()
        sensorManager.unregisterListener(listener)
    }


    /*
    private val requestPermissionLauncher = registerForActivityResult(ActivityResultContracts.RequestPermission()) {isGranted: Boolean ->
        if(isGranted) {
            println("sensor access granted")
        }
    }


    private val connectionListener = object : ConnectionListener {
        override fun onConnectionSuccess() {
            println("connected")
            var availableTrackers : List<HealthTrackerType> = healthTrackingService!!.trackingCapability.supportHealthTrackerTypes
            if(!availableTrackers.contains(HealthTrackerType.ACCELEROMETER_CONTINUOUS)) {
                // Accelerometer not available
                runOnUiThread {
                    status.text = "Status: Connected"
                    toggle.isEnabled = true
                }
            } else {
                accelTracker = healthTrackingService!!.getHealthTracker(HealthTrackerType.ACCELEROMETER_CONTINUOUS)
            }
        }

        override fun onConnectionEnded() {
            runOnUiThread {
                status.text = "Status: Disconnected"
                toggle.isEnabled = false
                toggle.text = "Start Tracking"
            }
        }

        override fun onConnectionFailed(p0: HealthTrackerException?) {
            println("connection failed")
            runOnUiThread {
                status.text = "Status: Connection Failed"
                toggle.isEnabled = false
            }
        }

    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        setContentView(R.layout.activity_main)

        status = findViewById(R.id.statusText)
        accelX = findViewById(R.id.accel_x)
        accelY = findViewById(R.id.accel_y)
        accelZ = findViewById(R.id.accel_z)
        toggle = findViewById(R.id.toggle_button)
        toggle.isEnabled = false

        if(ActivityCompat.checkSelfPermission(applicationContext, Manifest.permission.BODY_SENSORS) == PackageManager.PERMISSION_DENIED) {
            requestPermissionLauncher.launch(Manifest.permission.BODY_SENSORS)
        }

        try {
            healthTrackingService = HealthTrackingService(connectionListener, applicationContext)
            healthTrackingService!!.connectService()
        } catch (e: HealthConnectException) {
            TODO("Add error handling")
        }
    }
    */
}