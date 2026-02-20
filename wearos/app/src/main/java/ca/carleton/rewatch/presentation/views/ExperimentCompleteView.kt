package ca.carleton.rewatch.presentation.views

import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Button
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.navigation.NavController
import androidx.wear.compose.material.TimeText
import androidx.wear.compose.material.curvedText
import ca.carleton.rewatch.presentation.Screen

@Composable
/**
 * Creates final button to confirm finished experiment
 *
 * @param navController Controller for navigation of views
 */
fun ExperimentCompleteView(
    navController: NavController,
) {

    return Box(
        contentAlignment = Alignment.Center
    ) {
        TimeText(
            startCurvedContent = { curvedText("ReWatch") }
        )

        Column(
            horizontalAlignment = Alignment.CenterHorizontally,
            modifier = Modifier.padding(bottom = 20.dp)
        ) {
            Text(
                text = "Complete",
                textAlign = TextAlign.Center,
                style = MaterialTheme.typography.titleMedium,
                color = Color.White,
                modifier = Modifier.padding(vertical = 6.dp)
            )

            Button(
                onClick = { navController.navigate(Screen.JoinExperiment.route) }
            ) {
                Text(
                    text = "Return To\nFront Page",
                    textAlign = TextAlign.Center
                )
            }
        }
    }
}