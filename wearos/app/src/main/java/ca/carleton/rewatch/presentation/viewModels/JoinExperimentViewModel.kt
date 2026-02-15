package ca.carleton.rewatch.presentation.viewModels

import android.util.Log
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import androidx.navigation.NavController
import ca.carleton.rewatch.dataclasses.JoinedExperiment
import ca.carleton.rewatch.presentation.Screen
import ca.carleton.rewatch.service.RequestJoinExperiment
import ca.carleton.rewatch.service.Requestor
import kotlinx.coroutines.launch
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory

/**
 * The view model for joining an experiment.
 * Text entered on the join page updated experimentID,
 * which is sent off by the submitExperiment to the
 * relevant URL. ViewModel is automatically destroyed
 * once the displayed page isn't JoinExperiment
 *
 * Credit:
 */
class JoinExperimentViewModel : ViewModel() {

    var experimentID by mutableStateOf("")
        private set

    /**
     * Updates the internal experimentID
     *
     * @param experimentID New experiment ID
     */
    fun onExperimentChanged(experimentID: String) {
        this.experimentID = experimentID
    }

    /**
     * Builds and sends request to ReWatch web server
     *
     * @return Optional JoinedExperiment, or null if request failed
     */
    suspend fun sendRequest(): JoinedExperiment? {
        return try {
            Requestor.getInstance().join(experimentID)
        } catch (e: Exception) {
            e.printStackTrace()
            null
        }
    }

    /**
     * Submits the experiment in a coroutine to the webserver,
     * and takes appropriate action based on request result
     */
    fun submitExperiment(navController: NavController) {
        viewModelScope.launch {
            navController.navigate(Screen.Loading.route)
            var joinedExperiment: JoinedExperiment? = sendRequest()
            if (joinedExperiment != null) {
                Log.d("EXPJOIN", joinedExperiment.experimentID)
                Log.d("EXPJOIN", joinedExperiment.stage)
                navController.navigate(Screen.JoinExperiment.route)
            } else {
                navController.navigate(Screen.JoinExperiment.route)
            }
        }
    }
}
