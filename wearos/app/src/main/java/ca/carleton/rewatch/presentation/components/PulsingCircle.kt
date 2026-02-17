package ca.carleton.rewatch.presentation.components

import androidx.compose.animation.core.RepeatMode
import androidx.compose.animation.core.animateFloat
import androidx.compose.animation.core.infiniteRepeatable
import androidx.compose.animation.core.rememberInfiniteTransition
import androidx.compose.animation.core.tween
import androidx.compose.foundation.layout.Box
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.scale

/**
 * Creates a pulsating circle, informing user that action is being
 * taken on their screen
 *
 * @param pulseFraction Amount of pulse of the circle
 * @param content Content being pulsed
 *
 * CREDIT: https://medium.com/nerd-for-tech/jetpack-compose-pulsating-effect-4b9f2928d31a
 */
@Composable
fun PulsatingCircle(pulseFraction: Float = 1.5f, content: @Composable () -> Unit) {
    val infiniteTransition = rememberInfiniteTransition()

    val scale by infiniteTransition.animateFloat(
        initialValue = 1f,
        targetValue = pulseFraction,
        animationSpec = infiniteRepeatable(
            animation = tween(1000),
            repeatMode = RepeatMode.Reverse
        )
    )

    Box(modifier = Modifier.scale(scale)) {
        content()
    }
}