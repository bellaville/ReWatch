package ca.carleton.rewatch.presentation.views

import androidx.compose.material3.Button
import ca.carleton.rewatch.presentation.viewModels.TestingIMUViewModel

import androidx.compose.foundation.layout.Box
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.lifecycle.viewmodel.compose.viewModel
import androidx.wear.compose.material.Text
import androidx.compose.foundation.layout.fillMaxSize

@Composable
/**
 * Page for performing IMU Testing
 */
fun TestingIMUViewModel(
    viewModel: TestingIMUViewModel = viewModel()
) {

    return Box(
        modifier = Modifier.fillMaxSize(),
        contentAlignment = Alignment.Center
    ) {
        Button(
            onClick = { viewModel.changeCollection() },
            content = { Text("Click") }
        )
    }
}