package ca.carleton.rewatch.presentation

/**
 * Class for different screens shown within ReWatch
 *
 * CREDIT: https://medium.com/@jpmtech/navigation-in-jetpack-compose-c9e1fcfd2cdd
 */
sealed class Screen(val route: String) {
    object JoinExperiment : Screen("joinExp")
    object Loading : Screen("loading")
    object AwaitingStart: Screen("awaiting/{experimentID}")
    object Calibration: Screen("calibrating/{experimentID}")
}