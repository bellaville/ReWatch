package ca.carleton.rewatch.presentation.navigation

import androidx.compose.runtime.Composable
import androidx.wear.compose.navigation.SwipeDismissableNavHost
import androidx.wear.compose.navigation.composable
import androidx.wear.compose.navigation.rememberSwipeDismissableNavController
import ca.carleton.rewatch.presentation.AwaitingStart
import ca.carleton.rewatch.presentation.CalibrationView
import ca.carleton.rewatch.presentation.JoinExperimentView
import ca.carleton.rewatch.presentation.LoadingSpinner
import ca.carleton.rewatch.presentation.Screen

@Composable
/**
 * The main navigation stack for the app, allowing
 * for navigation within the main thread for ReWatch
 *
 * CREDIT: https://developer.android.com/training/wearables/compose/navigation
 *
 * @return Webpage that should be displayed by MainActivity
 */
fun NavigationStack() {

    val navController = rememberSwipeDismissableNavController()

    SwipeDismissableNavHost(
        navController = navController,
        startDestination = Screen.JoinExperiment.route
    ) {
        composable(Screen.JoinExperiment.route) {
            JoinExperimentView(navController)
        }
        composable(Screen.Loading.route) {
            LoadingSpinner()
        }
        composable(Screen.AwaitingStart.route) {
            AwaitingStart(navController)
        }
        composable(Screen.Calibration.route) {
            CalibrationView(navController)
        }
    }
}