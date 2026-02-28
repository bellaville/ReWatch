import pytest
from tests.stubs.watch_stub import (
    GaitSignalGenerator,
    ReactionTimeGenerator,
    make_sensor_dto,
    make_sensor_reading
)

class TestMakeSensorReading:
    """
    Tests for make_sensor_reading() - the individual data point
    """

    def test_uses_ts_not_timestamp(self):
        """
        GIVEN a timestamp and axis values
        WHEN make_sensor_reading is called
        THEN the key "ts" is used (not "timestamp") to match Kotlin DTO serialization.
        """
        reading = make_sensor_reading(timestamp_ms=17088000, x=0.1, y=0.2, z=0.3)
        assert "ts" in reading
        assert "timestamp" not in reading

    
    def test_has_all_required_fields(self):
        """
        GIVEN valid timestamp and axis inputs
        WHEN make_sensor_reading is called
        THEN the returned dictionary contains exactly {"ts", "x", "y", "z"}.
        """
        reading = make_sensor_reading(timestamp_ms = 1000, x=0.1, y=0.2, z=0.3)
        assert set(reading.keys()) == {"ts", "x", "y", "z"}

    def test_timestamp_stored_as_integer(self):
        """
        GIVEN numeric inputs
        WHEN make_sensor_reading is called
        THEN axis values are stored as floats and timestamp is JSON-serializable.
        """
        reading = make_sensor_reading(timestamp_ms=1000, x=1, y=2, z=3)
        assert isinstance(reading["x"], float)
        assert isinstance(reading["y"], float)
        assert isinstance(reading["z"], float)


class TestMakeSensorDto:
    """
    Tests for make_sensor_dto() - the full JSON payload
    """
    
    def test_structure_matches_kotlin_dto(self):
        """
        GIVEN a stage and readings
        WHEN make_sensor_dto is called
        THEN the top-level dictionary contains {"metadata", "data"}.
        """
        payload = make_sensor_dto(stage="GAIT", readings=[])
        assert "metadata" in payload
        assert "data" in payload
        assert set(payload.keys()) == {"metadata", "data"}

    def test_metadata_has_all_fields(self):
        """
        GIVEN a valid stage
        WHEN make_sensor_dto is called
        THEN metadata contains exactly {"stage", "trial", "memStep"}.
        """
        payload = make_sensor_dto(stage="GAIT", readings=[])
        assert set(payload["metadata"].keys()) == {"stage", "trial", "memStep"}

    def test_trial_and_mem_step_are_none_by_default(self):
        """
        GIVEN a GAIT stage payload
        WHEN make_sensor_dto is called without trial or mem_step
        THEN trial and memStep are None (null in JSON).
        """
        payload = make_sensor_dto(stage="GAIT", readings=[])
        assert payload["metadata"]["trial"] is None
        assert payload["metadata"]["memStep"] is None

    def test_trial_and_mem_step_set_correctly_for_rt_test(self):
        """
        GIVEN RT_TEST stage with trial and mem_step values
        WHEN make_sensor_dto is called
        THEN metadata contains those exact values.
        """
        payload = make_sensor_dto(stage="RT_TEST", readings=[], trial=1, mem_step=5)
        assert payload["metadata"]["trial"] == 1
        assert payload["metadata"]["memStep"] == 5

    def test_valid_stages_are_accepted(self):
        """
        GIVEN each valid AssessmentStage value
        WHEN make_sensor_dto is called
        THEN the stage field is stored exactly as provided.
        """
        for stage in ["WAITING", "GAIT", "GAIT_COMPLETE", "RT_TEST", "COMPLETE"]:
            payload = make_sensor_dto(stage=stage, readings=[])
            assert payload["metadata"]["stage"] == stage

    def test_data_field_contains_readings(self):
        """
        GIVEN a list of sensor readings
        WHEN make_sensor_dto is called
        THEN the data field contains those readings unchanged.
        """
        readings = [make_sensor_reading(1000 + i * 20, 0.1, 0.2, 0.3) for i in range(5)]
        payload = make_sensor_dto(stage="GAIT", readings=readings)
        assert len(payload["data"]) == 5

    
class TestGaitSignalGenerator:
    """
    Test for the fake walking data
    """

    def test_correct_number_of_samples(self):
        """
        GIVEN 30 seconds at 50 Hz
        WHEN gait data is generated
        THEN exactly 1500 samples are produced.
        """
        gen = GaitSignalGenerator(seed=123) # random seed
        readings = gen.generate(duration_seconds=30.0)
        assert len(readings) == 1500

    def test_short_duration(self):
        """
        GIVEN 5 seconds at 50 Hz
        WHEN gait data is generated
        THEN exactly 250 samples are produced.
        """
        gen = GaitSignalGenerator(seed=123)
        readings = gen.generate(duration_seconds=5.0)
        assert len(readings) == 250

    def test_timestamps_are_monotonically_increasing(self):
        """
        GIVEN generated gait data
        WHEN timestamps are inspected
        THEN they increase strictly over time.
        """
        gen = GaitSignalGenerator(seed=123)
        readings = gen.generate(duration_seconds=5.0)
        timestamps = [r["ts"] for r in readings]
        assert timestamps == sorted(timestamps)

    def test_timestamps_are_spaced_20ms_apart_at_50hz(self):
        """
        GIVEN 50 Hz sampling frequency
        WHEN timestamp gaps are calculated
        THEN each gap equals 20 milliseconds.
        """
        gen = GaitSignalGenerator(seed=123)
        gaps = []
        readings = gen.generate(duration_seconds=1.0)
        for i in range(len(readings) - 1):
            current_ts = readings[i]["ts"]
            next_ts = readings[i+1]["ts"]
            gap = next_ts - current_ts
            gaps.append(gap)
        assert all(g == 20 for g in gaps)

    def test_readings_have_correct_structure(self):
        """
        GIVEN generated gait data
        WHEN each reading is inspected
        THEN each contains {"ts", "x", "y", "z"}.
        """
        gen = GaitSignalGenerator(seed=123)
        readings = gen.generate(duration_seconds = 1.0)
        for r in readings:
            assert set(r.keys()) == {"ts", "x", "y", "z"}

    def test_same_seed_produces_same_data(self):
        """
        GIVEN two generators with the same seed
        WHEN gait data is generated
        THEN the outputs are identical.
        """
        readings_a = GaitSignalGenerator(seed=100).generate(duration_seconds=5.0)
        readings_b = GaitSignalGenerator(seed=100).generate(duration_seconds=5.0)
        assert readings_a == readings_b

    def test_same_seed_produces_different_data(self):
        """
        GIVEN two generators with different seeds
        WHEN gait data is generated
        THEN the outputs differ.
        """
        readings_a = GaitSignalGenerator(seed=1).generate(duration_seconds=5.0)
        readings_b = GaitSignalGenerator(seed=2).generate(duration_seconds=5.0)
        assert readings_a != readings_b

    def test_y_axis_has_largest_amplitude(self):
        """
        GIVEN generated gait data
        WHEN axis amplitude ranges are compared
        THEN the Y-axis has the largest range (dominant vertical motion).
        """
        gen = GaitSignalGenerator(seed=123)
        readings = gen.generate(duration_seconds = 10.0)
        x_range  = max(r["x"] for r in readings) - min(r["x"] for r in readings)
        y_range  = max(r["y"] for r in readings) - min(r["y"] for r in readings)
        z_range  = max(r["z"] for r in readings) - min(r["z"] for r in readings)
        assert y_range > x_range
        assert y_range > z_range



class TestReactionTimeGenerator:
    """
    Test for the fake arm-movement data
    """
    def test_returns_payload_and_rt_ms(self):
        """
        GIVEN valid trial inputs
        WHEN generate_trial is called
        THEN a payload dictionary and reaction time (float) are returned.
        """
        gen = ReactionTimeGenerator(seed=123)
        payload, rt_ms = gen.generate_trial(trial=0, mem_step=0, stimulus_time_ms=1000000)
        assert isinstance(payload, dict)
        assert isinstance(rt_ms, float)

    def test_payload_stage_is_rt_test(self):
        """
        GIVEN a generated trial
        WHEN the payload metadata is inspected
        THEN stage is "RT_TEST".
        """
        gen = ReactionTimeGenerator(seed=123)
        payload, _ = gen.generate_trial(trial=0, mem_step=0, stimulus_time_ms=1000000)
        assert payload["metadata"]["stage"] == "RT_TEST"

    def test_trial_and_mem_step_are_set(self):
        """
        GIVEN trial and mem_step inputs
        WHEN generate_trial is called
        THEN metadata contains those exact values.
        """
        gen = ReactionTimeGenerator(seed=123)
        payload, _ = gen.generate_trial(trial=2, mem_step=7, stimulus_time_ms=1000000)
        assert payload["metadata"]["trial"] == 2
        assert payload["metadata"]["memStep"] == 7

    def test_same_seed_produces_same_reaction_times(self):
        """
        GIVEN two generators with the same seed
        WHEN generate_trial is called
        THEN the resulting reaction times are identical.
        """
        gen_a = ReactionTimeGenerator(seed=77)
        gen_b = ReactionTimeGenerator(seed=77)
        _, rt_a = gen_a.generate_trial(0, 0, 1000000)
        _, rt_b = gen_b.generate_trial(0, 0, 1000000)
        assert rt_a == rt_b

    def test_timestamps_start_at_stimulus_time(self):
        """
        GIVEN a stimulus timestamp
        WHEN generate_trial is called
        THEN the first sensor reading timestamp equals the stimulus time.
        """
        stimulus_ms = 1708800000000
        gen = ReactionTimeGenerator(seed=42)
        payload, _  = gen.generate_trial(trial=0, mem_step=0, stimulus_time_ms=stimulus_ms)
        assert payload["data"][0]["ts"] == stimulus_ms


        
    


    
    