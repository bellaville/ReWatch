package ca.carleton.rewatch.presentation

import android.content.Context
import android.hardware.Sensor
import android.hardware.SensorEvent
import android.hardware.SensorEventListener
import android.hardware.SensorManager
import android.util.Log
import ca.carleton.rewatch.dataclasses.SensorReading

class AccelerometerManager(context: Context): SensorEventListener {
    private val sensorManager = context.getSystemService(Context.SENSOR_SERVICE) as SensorManager
    private val accelerometer = sensorManager.getDefaultSensor(Sensor.TYPE_LINEAR_ACCELERATION)

    private val _recordedData = mutableListOf<SensorReading>()
    val recordedData: List<SensorReading> get() = _recordedData

    private var isRecording = false

    fun start() {
        if (isRecording) return
        isRecording = true
        _recordedData.clear()
        accelerometer?.let {
            sensorManager.registerListener(this, it, SensorManager.SENSOR_DELAY_GAME)
        }
        Log.d("AccelerometerManager", "Started recording")
    }

    fun stop() {
        if (!isRecording) return
        isRecording = false
        sensorManager.unregisterListener(this)
        Log.d("AccelerometerManager", "Stopped recording. Points: ${_recordedData.size}")
    }

    override fun onSensorChanged(event: SensorEvent?) {
        if (isRecording && event?.sensor?.type == Sensor.TYPE_LINEAR_ACCELERATION) {
            _recordedData.add(
                SensorReading(
                    timestamp = System.currentTimeMillis(),
                    x = event.values[0],
                    y = event.values[1],
                    z = event.values[2]
                )
            )
        }
    }

    override fun onAccuracyChanged(sensor: Sensor?, accuracy: Int) {}

    fun isRunning(): Boolean {
        return isRecording;
    }
}