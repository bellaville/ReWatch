package ca.carleton.rewatch.presentation

import android.content.Context
import android.hardware.Sensor
import android.hardware.SensorEvent
import android.hardware.SensorEventListener
import android.hardware.SensorManager
import android.util.Log
import ca.carleton.rewatch.dataclasses.SensorReading

class AccelerometerManager(context: Context): SensorEventListener {
    private val MAX_READINGS = 1500;
    private val sensorManager = context.getSystemService(Context.SENSOR_SERVICE) as SensorManager
    private val accelerometer = sensorManager.getDefaultSensor(Sensor.TYPE_LINEAR_ACCELERATION)
    private val _recordedData = ArrayDeque<SensorReading>(MAX_READINGS)
    val recordedData: List<SensorReading> get() = _recordedData

    private var isRecording = false

    fun setup() {
        accelerometer?.let {
            sensorManager.registerListener(this, it, SensorManager.SENSOR_DELAY_GAME)
        }
    }

    fun teardown() {
        if (isRecording) {
            stop()
        }
        sensorManager.unregisterListener(this)
    }

    fun start() {
        if (isRecording) return
        _recordedData.clear()
        isRecording = true
        Log.d("AccelerometerManager", "Started recording")
    }

    fun stop() {
        if (!isRecording) return
        isRecording = false
        Log.d("AccelerometerManager", "Stopped recording. Points: ${_recordedData.size}")
    }

    override fun onSensorChanged(event: SensorEvent?) {
        if (isRecording && event?.sensor?.type == Sensor.TYPE_LINEAR_ACCELERATION) {
            if (_recordedData.size == MAX_READINGS) {
                _recordedData.removeFirstOrNull()
            }
            _recordedData.addLast(
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