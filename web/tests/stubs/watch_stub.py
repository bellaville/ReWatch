import random
import numpy as np
import requests
import os
import logging
import time
import argparse

from typing import List, Optional, Tuple
from datetime import datetime, timezone

log = logging.getLogger(__name__)

"""
To use this stub:
Run a full fake experiment from the terminal:
python tests/stubs/watch_stub.py --base-url http://localhost:5000 -- experiment-id 123
"""


####################
# BUILD JSON LOADS #
####################
def make_sensor_reading(timestamp_ms: int, x: float, y: float, z: float) -> dict:
    """ 
    Builds one accelerometer reading 
    """
    return {
        "ts": timestamp_ms,
        "x": round(float(x), 2),
        "y": round(float(y), 2),
        "z": round(float(z), 2),
    }


def make_sensor_dto(stage: str, readings: List[dict], trial: Optional[int]= None, mem_step: Optional[int]= None) -> dict:
    """
    Builds the full JSON payload the watch POSTs to the Flask app

    stage: experiment phase
    readings: list of sensor readings (from make_sensor_reading())
    trial: trial number (used in RT_TEST), otherwise None
    mem_step: memory stimulus (used in RT_TEST), otherwise None

    """
    return {
        "metadata": {
            "stage": stage,
            "trial": trial,
            "memStep": mem_step,
        },
        "data": readings,
    }


#############################
# GENERATE FAKE SENSOR DATA #
#############################
class GaitSignalGenerator:
    """
    Generates fake accelerometer data that simulates a person walking
    """
    SAMPLE_RATE_HZ = 50 # how many readings per second

    def __init__(self, seed: Optional[int] = None):
        # creates a random number generator
        # (passing a seed makes it produce the same numbers every run)
        self.rng = np.random.default_rng(seed)

    def generate(self, duration_seconds: float = 30.0) -> List[dict]:
        """
        Returns a list of sensor readings covering 'duration_seconds' of walking
        
        sample_rate_hz = 50 represents 50 readings per second (the typical for a smartwatch accelerometer)

        A 30-second recording at 50 Hz = 1500 readings total
        
        """
        readings = []
        n_samples = int(duration_seconds * self.SAMPLE_RATE_HZ)
        interval_ms = int(1000 / self.SAMPLE_RATE_HZ) # gap between readings in ms (20 ms at 50Hz)

        start_ms = int(datetime.now(timezone.utc).timestamp() * 1000) # current time

        # evenly spaced time values
        # to represent each moment in time during the 30 second walk
        time = np.linspace(0, duration_seconds, n_samples)

        # convert time into a wave
        phase = 2 * np.pi * 1.9 * time # 1.9 Hz = approx 114 steps/min

        x = 0.3 * np.sin(phase / 2) + self.rng.normal(0, 0.08, n_samples) # x-axis: smaller front-back swing at half the frequency + noise
        y = 1.0 * np.sin(phase) + self.rng.normal(0, 0.08, n_samples) # y-axis: vertical bounce, biggest amplitude
        z = 0.15 * np.sin(phase + 1.0) + self.rng.normal(0, 0.08, n_samples) # z-axis: side sway, smallest amplitude

        # make the complete list of sensor readings for the entire walk
        for i in range(n_samples):
            # timestamp for reading = start time + how many intervals have passed
            timestamp = start_ms + i * interval_ms
            reading = make_sensor_reading(
                timestamp_ms = timestamp,
                x=x[i],
                y=y[i],
                z=z[i],
            )
            readings.append(reading)

        return readings
    

class ReactionTimeGenerator:
    """
    Generates fake arm-movement data for the memory/reaction time test

    During the memory test, a stimulus (the set of shapes) appears and the patient
    physically moves their arm in response. The watch records when the arm moved. The time
    between stimulus and arm movement is the reaction time

    We will simulate this as:
        1. A quiet period where the arm is at rest (low sensor readings)
        2. A suddent burst of movement after a realisitic delay (1500ms)
        3. The signal then dies down as the arm lowers
    """
    # reaction time constants based on documented control group ranged from 900ms - 4200ms
    RT_MIN_MS = 900.0
    RT_MAX_MS = 4200.0
    RT_MEAN_MS = (RT_MIN_MS + RT_MAX_MS)/2
    RT_STD_MS = (RT_MAX_MS - RT_MIN_MS)/6 # divide by the 6 std devs
    

    def __init__(self, seed: Optional[int] = None):
        # used for generating the arm movement signal shapes
        self.rng_np = np.random.default_rng(seed) 
        # used for drawing a single random reaction time from the bell curve
        self.rng = random.Random(seed)

    def generate_trial(self, trial: int, mem_step: int, stimulus_time_ms: int) -> Tuple[dict, float]:
        """
        Simulate one stimulus-response event
        Returns payload dict ready to POST to Flask
        """
        sample_rate_hz = 50

        # get a random reaction time from the bell curve centered at 2100ms (typical reaction time)
        rt_ms = self.rng.gauss(self.RT_MEAN_MS, self.RT_STD_MS)
        # we clamp, forcing a value to stay within a minimum and maximum limit
        rt_ms = max(self.RT_MIN_MS, min(self.RT_MAX_MS, rt_ms))

        # record slightly longer than the max possible RT so we always capture the full arm movement
        window_ms = self.RT_MAX_MS + 500 
        # total readings in the window (i.e. 4.7s * 50Hz = 235 samples)
        n_samples = int((window_ms / 1000) * sample_rate_hz)
        # which sample index the arm starts moving (i.e. 2550ms -> sample 127)
        rt_sample = int((rt_ms / 1000) * sample_rate_hz)
        # time between readings in ms (i.e. 20ms at 50Hz)
        interval_ms = int(1000 / sample_rate_hz)

        readings = []

        # loop throguh each sample in the recording window
        for i in range(n_samples):
            # timestamp = stimulus time + how many intervals have passed
            ts = stimulus_time_ms + i * interval_ms

            if i < rt_sample:
                # small noise on x,y,z - arm is at rest
                x = float(self.rng_np.normal(0, 0.02)) 
                y = float(self.rng_np.normal(0, 0.02)) 
                z = float(self.rng_np.normal(0, 0.02)) 
            else: # after arm moves -> burst of acceleration
                fade = max(0.0, 1.0 - (i - rt_sample) / sample_rate_hz * 0.3) # fade from 1.0 -> 0.0 over 0.3 seconds so that signal dies down naturally
                x = float(0.8 * fade * self.rng_np.normal(1.0, 0.2)) # x movement burst, scaled by fade
                y = float(1.2 * fade * self.rng_np.normal(1.0, 0.15)) # y movement burst, strongest axis when arm lifts
                z = float(0.4 * fade * self.rng_np.normal(0.5, 0.1)) # z movement burst, smaller lateral component

            readings.append(make_sensor_reading(ts,x,y,z))
        
        payload = make_sensor_dto(
            stage="RT_TEST",
            readings=readings,
            trial=trial,
            mem_step=mem_step,
        )
        return payload, round(rt_ms, 2)



#########################
# CREATE THE WATCH STUB #
#########################
class WatchStub:
    """
    How the watch will work:
        1. Watch calls GET /join/<experimentID> to register
        2. Watch polls GET /join/<experimentID>/status repeatedly
        3. Flask's global state counter increments each poll and
        returns a stage name based on how many times it's been polled:
            polls 0-5: WAITING
            polls 6-15: GAIT
            polls 16-20: GAIT_COMPLETE
            polls 21-30: RT_TEST
            polls 31+: COMPLETE
        4. When the watch sees "GAIT" it starts recording and eventually POSTs
        data to /api/sensor-data
        5. Same for RT_TEST

    This stub polls the status endpoint and responds to stage changes
    """
    # polls needed before next stage appears
    POLLS_TO_ADVANCE = {
        "WAITING": 6,
        "GAIT": 10,
        "GAIT_COMPLETE": 5,
        "RT_TEST": 10
    }

    def __init__(
            self,
            base_url: str,
            experiment_id: str,
            upload_path: str = "/api/sensor-data", 
            seed: Optional[int] = None,
            timeout_s: int = 10,
            poll_interval_s: float = 0.1
    ):
        # remove any trailing slash from the url
        self.base_url = base_url.rstrip("/")
        # store experiment ID so we can attach it to every request
        self.experiment_id = experiment_id
        # full URL to POST
        self.upload_url = f"{self.base_url}{upload_path}"
        self.timeout = timeout_s 
        self.poll_interval = poll_interval_s

        # Session lets us reuse the same connection and headers across multiple requests
        self._session = requests.Session()
        self._session.headers.update({
            "Content-Type": "application/json",
            "X-Experiment-ID": experiment_id, # UPDATE
        })

        self._gait_gen = GaitSignalGenerator(seed=seed)
        self._rt_gen = ReactionTimeGenerator(seed=seed)

        self.gait_duration = float(os.getenv("WATCH_STUB_GAIT_DURATION", "30"))

    ###################
    # PRIVATE HELPERS #
    ###################
    def _post(self, payload: dict) -> requests.Response:
        """
        Send one payload to Flask and return the response
        """
        try:
            resp = self._session.post(self.upload_url, json=payload, timeout=self.timeout)
            resp.raise_for_status()
            log.debug("WatchStub POST -> %d", resp.status_code)
        except requests.exceptions.ConnectionError:
            raise ConnectionError(
                f"WatchStub could not connect to {self.upload_url}\n"
            )
            

    def _join(self) -> dict:
        """
        Step 1: call GET /join/<experimentID> to register with Flask.
        This resets Flask's global state counter back to 0
        """
        url = f"{self.base_url}/join/{self.experiment_id}"
        resp = self._session.get(url, timeout=self.timeout)
        resp.raise_for_status()
        log.info("WatchStub: joined experiment %s", self.experiment_id)
        return resp.json()

    def _poll_until_stage(self, target_stage: str, max_polls: int = 100) -> str:
        """
        Step 2: poll GET /join/<experimentID>/status until Flask returns the target stage.
        This mimics how the real watch waits for instructions
        """
        url = f"{self.base_url}/join/{self.experiment_id}/status"

        for poll_number in range(max_polls):
            resp = self._session.get(url, timeout=self.timeout)
            resp.raise_for_status()
            current_stage = resp.json().get("stage")

            log.debug("WatchStub: poll %d -> stage = %s", poll_number, current_stage)

            if current_stage == target_stage:
                log.info("WatchStub: stage %s reached after %d polls", target_stage, poll_number + 1)
                return current_stage
            
            time.sleep(self.poll_interval) # wait before polling again

        raise TimeoutError(
            f"WatchStub: stage '{target_stage}' never appeared after {max_polls} polls"
        )
    

    #################
    # PHASE METHODS #
    #################
    def send_gait_data(self, duration_seconds: Optional[float] = None) -> requests.Response:
        """
        Generate walking data and POST it to /api/sensor-data with stage="GAIT"
        Called when Flask's status endpoint returns "GAIT"
        
        Simulates: when the patient finishes the walking calibration, uploading
        the whole batch of accelerometer readings
        """
        duration = duration_seconds or self.gait_duration
        log.info("WatchStub: sending %0.fs of GAIT data", duration)
        readings = self._gait_gen.generate(duration_seconds=duration) # generate the fake walking data
        return self._post(make_sensor_dto(stage="GAIT", readings=readings))
    
    def send_rt_test_data(
            self,
            n_mem_steps: int = 10,
            # 6 seconds between stimuli (must be longer than max RT, 4.2s so stimuli don't overlap)
            inter_stimulus_interval_s: float = 6.0
            ) -> List[Tuple[requests.Response, float]]:
        """
        Simulate the reaction time memory test.

        Sends one POST per memory step, called when Flask returns "RT_TEST"
        Returns a list of (response, reaction_time_ms) so tests can check the values for each step
        """
        results = []
        now_ms = int(datetime.now(timezone.utc).timestamp() * 1000)

        for step in range(n_mem_steps):
            # space stimuli 6 seconds apart so they don't overlap
            stimulus_ms = now_ms + int(step * inter_stimulus_interval_s * 1000)
            payload, rt_ms = self._rt_gen.generate_trial(
                trial = 0,
                mem_step = step,
                stimulus_time_ms = stimulus_ms,
            )
            log.info("WatchStub: RT_TEST memStep=%d RT=%.1f ms", step, rt_ms)
            results.append((self._post(payload), rt_ms))

        return results
    
    def run_full_experiment(
            self,
            gait_duration_s: Optional[float] = None,
            n_mem_steps: int = 10,
    ) -> dict:
        """
        Run a complete simulated experiment by polling Flask for stage changes:
            1. JOIN -> register with Flask, reset state counter
            2. Poll -> wait for GAIT stage
            3. POST -> send gait accelerometer data
            4. Poll -> wait for RT_TEST stage
            5. POST -> send reaction time data for each memory step
            6. Poll -> wait for COMPLETE stage

        Returns a summary dict as follows:
            {
            "gait_readings_sent": 1500,
            "rt_results": [(response, rt_ms), ...],
            "all_ok": True,
            }
        """
        log.info("WatchStub: starting full experiment (experiment_id=%s)", self.experiment_id)

        # step 1: join the experiment (reset Flask's state counter)
        self._join()

        # step 2: poll until Flask says GAIT
        self._poll_until_stage("GAIT")

        # step 3: send gait data
        gait_resp = self.send_gait_data(duration_seconds=gait_duration_s)

        # step 4: poll until Flask says RT_TEST
        self._poll_until_stage("RT_TEST")

        # step 5: send reaction time data
        rt_results = self.send_rt_test_data(n_mem_steps=n_mem_steps)

        # step 6: poll until Flask says COMPLETE
        self._poll_until_stage("COMPLETE")

        all_ok = gait_resp.ok and all(r.ok for r, _ in rt_results) # true only if every single HTTP response was 2xx
        log.info("WatchStub: done. All response OK: %s", all_ok)

        return {
            "gait_readings_sent": int((gait_duration_s or self.gait_duration) * GaitSignalGenerator.SAMPLE_RATE_HZ), # total readings = duration * sample rate
            "rt_results": rt_results,
            "all_ok": all_ok,
        }
        
#####################
# RUN FROM TERMINAL #
#####################

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Simulate the Rewatch smartwatch")
    parser.add_argument("--base-url", default="http://localhost:5000")
    parser.add_argument("--experiment-id", required=True)
    parser.add_argument("--upload-path", default="/api/sensor-data")
    parser.add_argument("--gait-duration", type=float, default=30.0)
    parser.add_argument("--n-mem-steps", type=int, default=10)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO)

    stub = WatchStub(
        base_url = args.base_url,
        experiment_id = args.experiment_id,
        upload_path = args.upload_path,
        seed=args.seed
    )
    stub.gait_duration = args.gait_duration

    result = stub.run_full_experiment(n_mem_steps=args.n_mem_steps)

    print("\n--- WatchStub Summary ---")
    print(f" Gait readings sent: {result['gait_readings_sent']}")
    print(f" RT steps sent: {len(result['rt_results'])}")
    print(f" All responses OK: {result['all_ok']}")
    if result["rt_results"]:
        rts = [rt for _, rt in result["rt_results"]]
        print(f"Avg reaction time: {sum(rts)/len(rts): .1f} ms")

