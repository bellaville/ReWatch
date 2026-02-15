package ca.carleton.rewatch.presentation

import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.LinearProgressIndicator
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.lifecycle.viewmodel.compose.viewModel
import androidx.navigation.NavController
import androidx.wear.compose.material.Text
import androidx.wear.compose.material.TimeText
import androidx.wear.compose.material.curvedText
import ca.carleton.rewatch.presentation.viewModels.AwaitingStartViewModel

@Composable
/**
 * Page for waiting for experiment to start
 *
 * @param navController Controller for navigation of views
 */
fun AwaitingStart(
    navController: NavController,
    viewModel: AwaitingStartViewModel = viewModel()
) {

    viewModel.pollExperiment(navController)

    return Box(
        contentAlignment = Alignment.Center
    ) {
        TimeText(
            startCurvedContent = { curvedText("ReWatch") }
        )

        // CREDIT: https://developer.android.com/develop/ui/compose/layouts/basics
        Column(
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            Text(
                "Awaiting Start\nof Experiment"
            )
            LinearProgressIndicator(
                modifier = Modifier.padding(
                    horizontal = 48.dp,
                    vertical = 8.dp
                )
            )
        }
    }
}