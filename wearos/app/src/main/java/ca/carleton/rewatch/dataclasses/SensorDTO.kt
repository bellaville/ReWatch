package ca.carleton.rewatch.dataclasses

import kotlinx.serialization.Serializable

@Serializable
/**
 * Used to package data sent to the ReWatch web application
 */
data class SensorDTO(
    val metadata: DTOMetadata,
    val data: Array<SensorReading>,
) {
    override fun equals(other: Any?): Boolean {
        if (this === other) return true
        if (javaClass != other?.javaClass) return false

        other as SensorDTO

        if (metadata != other.metadata) return false
        if (!data.contentEquals(other.data)) return false

        return true
    }

    override fun hashCode(): Int {
        var result = metadata.hashCode()
        result = 31 * result + data.contentHashCode()
        return result
    }
}
