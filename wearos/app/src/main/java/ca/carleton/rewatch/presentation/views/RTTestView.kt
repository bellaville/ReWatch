package ca.carleton.rewatch.presentation.views

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
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.lifecycle.viewmodel.compose.viewModel
import androidx.navigation.NavController
import androidx.wear.compose.material.MaterialTheme
import androidx.wear.compose.material.Text
import androidx.wear.compose.material.TimeText
import androidx.wear.compose.material.curvedText
import ca.carleton.rewatch.presentation.components.PulsatingCircle
import ca.carleton.rewatch.presentation.viewModels.RTTestViewModel

@Composable
/**
 * Page for performing RT Test
 *
 * @param navController Controller for navigation of views
 */
fun RTTestView(
    navController: NavController,
    viewModel: RTTestViewModel = viewModel()
) {

    LaunchedEffect(Unit) {
        viewModel.startTimeSync()
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
                text = "Reaction Time",
                textAlign = TextAlign.Center,
                style = MaterialTheme.typography.title1
            )
            Text(
                text = viewModel.collectionText,
                textAlign = TextAlign.Center
            )
            PulsatingCircle() {
                Surface(
                    color = if (viewModel.circleColour == 0) Color.Red else Color.Green,
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