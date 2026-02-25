package ca.carleton.rewatch.presentation

import androidx.compose.foundation.layout.Box
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.wear.compose.material.CircularProgressIndicator
import androidx.wear.compose.material.TimeText
import androidx.wear.compose.material.curvedText

@Composable
/**
 * Loading spinner that can be used in the app to
 * easily show awaiting
 */
fun LoadingSpinner() {

    return Box(
        contentAlignment = Alignment.Center
    ) {
        TimeText(
            startCurvedContent = { curvedText("ReWatch") }
        )

        CircularProgressIndicator()
    }
}