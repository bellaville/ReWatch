package ca.carleton.rewatch.presentation

import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.material3.Surface
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.lifecycle.viewmodel.compose.viewModel
import androidx.navigation.NavController
import androidx.compose.material3.MaterialTheme
import androidx.wear.compose.material.Text
import androidx.wear.compose.material.TimeText
import androidx.wear.compose.material.curvedText
import ca.carleton.rewatch.presentation.components.PulsatingCircle
import ca.carleton.rewatch.presentation.viewModels.CalibrationViewModel

@Composable
/**
 * Page for waiting for experiment to start
 *
 * @param navController Controller for navigation of views
 */
fun CalibrationView(
    navController: NavController,
    viewModel: CalibrationViewModel = viewModel()
) {

    LaunchedEffect(Unit) {
        viewModel.pollExperiment(navController)
    }

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
                text = viewModel.collectionText,
                textAlign = TextAlign.Center
            )
            PulsatingCircle() {
                Surface(
                    color = MaterialTheme.colorScheme.primary,
                    shape = CircleShape,
                    modifier = Modifier.size(42.dp).padding(
                        vertical = 10.dp,
                        horizontal = 10.dp
                    ),
                    content = {}
                )
            }
        }
    }
}