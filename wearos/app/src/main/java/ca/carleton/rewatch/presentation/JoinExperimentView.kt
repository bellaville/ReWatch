package ca.carleton.rewatch.presentation

import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.text.KeyboardActions
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.focus.FocusManager
import androidx.compose.ui.platform.LocalFocusManager
import androidx.compose.ui.text.input.ImeAction
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.unit.dp
import androidx.lifecycle.viewmodel.compose.viewModel
import androidx.navigation.NavController
import androidx.wear.compose.material.TimeText
import androidx.wear.compose.material.curvedText
import ca.carleton.rewatch.presentation.viewModels.JoinExperimentViewModel

@Composable
/**
 * Creates input box for experiment ID, which will enable
 * user to join experiment
 *
 * @param navController Controller for navigation of views
 */
fun JoinExperimentView(
    navController: NavController,
) {

    val viewModel: JoinExperimentViewModel = viewModel()
    val localFocus: FocusManager = LocalFocusManager.current

    return Box(
        contentAlignment = Alignment.Center
    ) {
        TimeText(
            startCurvedContent = { curvedText("ReWatch") }
        )

        // See: https://stackoverflow.com/questions/75851827/kotlin-compose-cant-type-into-textfields-using-viewmodel
        OutlinedTextField(
            value = viewModel.experimentID,
            onValueChange = { viewModel.onExperimentChanged(it) },
            label = { Text("Assessment ID") },
            modifier = Modifier.fillMaxWidth()
                .padding(horizontal = 20.dp),
            keyboardOptions = KeyboardOptions(
                imeAction = ImeAction.Done,
                keyboardType = KeyboardType.Number
            ),
            keyboardActions = KeyboardActions(
                onDone = {
                    localFocus.clearFocus()
                    viewModel.submitExperiment(navController)
                }
            )
        )
    }
}