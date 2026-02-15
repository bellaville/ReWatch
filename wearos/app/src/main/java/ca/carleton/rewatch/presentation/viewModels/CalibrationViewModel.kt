package ca.carleton.rewatch.presentation.viewModels

import android.util.Log
import androidx.lifecycle.SavedStateHandle
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import androidx.navigation.NavController
import ca.carleton.rewatch.dataclasses.AssessmentStage
import ca.carleton.rewatch.dataclasses.JoinedExperiment
import ca.carleton.rewatch.presentation.Screen
import ca.carleton.rewatch.service.Requestor
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch

class CalibrationViewModel(private val savedStateHandle: SavedStateHandle) : ViewModel() {

    /**
     * Builds and sends poll request to ReWatch web server
     *
     * @return Optional JoinedExperiment, or null if request failed
     */
    suspend fun sendRequest(experimentID: String): JoinedExperiment? {
        return try {
            Requestor.getInstance().pollStatus(experimentID)
        } catch (e: Exception) {
            e.printStackTrace()
            null
        }
    }

    /**
     * Polls the experiment in a coroutine to the webserver,
     * and takes appropriate action based on request result
     */
    fun pollExperiment(navController: NavController) {
        val experimentID: String = savedStateHandle["experimentID"] ?: ""

        if (experimentID == "") {
            navController.navigate(Screen.JoinExperiment.route)
            return
        }

        viewModelScope.launch {
            var isAwaiting = true

            // Loop to check status every second
            while (isAwaiting) {
                var joinedExperiment: JoinedExperiment? = sendRequest(experimentID)

                // If null, return to join experiment and stop
                if (joinedExperiment == null) navController.navigate(Screen.JoinExperiment.route)

                // Check if current stage, if not navigate to next stage
                if (joinedExperiment?.stage == AssessmentStage.CALIBRATION.stage) {
                    Log.d("EXPPOLL", "Awaiting Change to Status")
                } else {
                    isAwaiting = false
                    Log.d("EXPPOLL", "Status Changed to " + joinedExperiment?.stage)
                    navController.navigate(Screen.JoinExperiment.route)
                }
                delay(1000)
            }
        }
    }
}