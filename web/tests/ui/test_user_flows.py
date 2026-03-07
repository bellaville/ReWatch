import time
import requests

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

from tests.stubs.watch_stub import make_sensor_dto, make_sensor_reading

###########
# HELPERS #
###########
def login(browser, base_url, email, password):
    """
    Navigate to the login page and submit credentials
    """
    browser.get(f"{base_url}/auth/login")
    WebDriverWait(browser, 5).until(
        EC.presence_of_element_located((By.NAME, "email"))
    )

    browser.find_element(By.NAME, "email").clear()
    browser.find_element(By.NAME, "email").send_keys(email)
    browser.find_element(By.NAME, "password").clear()
    browser.find_element(By.NAME, "password").send_keys(password)
    browser.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
    time.sleep(1) # wait 1 second for the login redirect to complete before the test continues


#############################
# TEST CLASS 1 - LOGIN FLOW #
#############################
class TestLoginFlow:
    def test_login_page_loads(self, browser, live_server_url):
        """
        GIVEN the app is running
        WHEN the login page is visited
        THEN the page loads and the email input field is present.
        """
        browser.get(f"{live_server_url}/auth/login") # navigate to the login page
        WebDriverWait(browser, 5).until(
            EC.presence_of_element_located((By.NAME, "email")) # wait until the email field appears — confirms the page actually loaded
        )
        assert browser.find_element(By.NAME, "email") is not None  # confirm the email input field exists on the page

    def test_physician_can_log_in(self, browser, live_server_url):
        """
        GIVEN a seeded physician account exists
        WHEN valid credentials are submitted
        THEN the physician is redirected away from the login page.

        UPDATE email and password to match your seed_users() function.
        """
        login(browser, live_server_url, "dr.stephen@avengers.com", "password123") # submit valid credentials using the helper function above 
        assert "login" not in browser.current_url.lower() # after a successful login Flask redirects away — if "login" is still in the URL, login failed

    def test_invalid_login_stays_on_login_page(self, browser, live_server_url):
        """
        GIVEN wrong credentials are entered
        WHEN the login form is submitted
        THEN the user stays on the login page.
        """
        login(browser, live_server_url, "nobody@fake.com", "wrongpassword") # submit credentials that don't belong to any seeded user
        assert "login" in browser.current_url.lower() or \
               browser.find_element(By.NAME, "email") # either still on the login URL, or the email field is still visible — both confirm login was rejected

    def test_protected_page_redirects_unauthenticated_user(self, browser, live_server_url):
        """
        GIVEN a user is not logged in
        WHEN they try to visit a protected page directly
        THEN they are redirected to the login page.
        """
        browser.get(f"{live_server_url}/auth/logout") # visit the logout route to clear any existing session cookie
        time.sleep(0.5) # wait for the logout redirect to complete
        browser.get(f"{live_server_url}/patient_details") # try to visit a protected page without being logged in
        time.sleep(1) # wait for Flask's redirect to the login page to complete
        assert "login" in browser.current_url.lower() # Flask should have redirected to the login page — @login_required does this automatically


#######################################
# TEST CLASS 2 - PATIENT DETAILS FLOW #
#######################################
class TestPatientDetailsFlow:
    def test_patient_details_page_loads(self, logged_in_browser, live_server_url):
        """
        GIVEN a logged-in physician
        WHEN they navigate to the patient details page
        THEN the page loads and they are not redirected to login.
        """
        logged_in_browser.get(f"{live_server_url}/patient_details") 
        time.sleep(1) 
        assert "login" not in logged_in_browser.current_url.lower() 

    def test_patient_details_page_has_content(self, logged_in_browser, live_server_url):
        """
        GIVEN a logged-in physician
        WHEN the patient details page loads
        THEN the page body has visible content (not blank).
        """
        logged_in_browser.get(f"{live_server_url}/patient_details") # navigate to the patient details page
        time.sleep(1) # wait for the page to fully load
        body_text = logged_in_browser.find_element(By.TAG_NAME, "body").text  # grab all the visible text from the entire page body
        assert len(body_text.strip()) > 0  # confirm the page has actual content — an empty page would have length 0

    def test_profile_page_loads(self, logged_in_browser, live_server_url):
        """
        GIVEN a logged-in physician
        WHEN they navigate to their profile page
        THEN the page loads successfully.
        """
        logged_in_browser.get(f"{live_server_url}/profile") # navigate to the profile page
        time.sleep(1) # wait for the page to fully load
        assert "login" not in logged_in_browser.current_url.lower() # confirm we weren't redirected to login — page loaded for the authenticated user

###################################
# TEST CLASS 3 - ASSESSMENTS FLOW #
###################################
class TestAssessmentFlow:
    def test_assessments_page_loads(self, logged_in_browser, live_server_url):
        """
        GIVEN a logged-in physician
        WHEN they navigate to the assessments page
        THEN the page loads and they are not redirected to login.
        """
        logged_in_browser.get(f"{live_server_url}/assessments") 
        time.sleep(1)  
        assert "login" not in logged_in_browser.current_url.lower()

    def test_assessments_page_has_content(self, logged_in_browser, live_server_url):
        """
        GIVEN a logged-in physician
        WHEN the assessments page loads
        THEN the page body has visible content.
        """
        logged_in_browser.get(f"{live_server_url}/assessments")        
        time.sleep(1)                                                           
        body_text = logged_in_browser.find_element(By.TAG_NAME, "body").text 
        assert len(body_text.strip()) > 0 

##########################################
# TEST EXPERIMENT/WATCH STUB INTEGRATION #
##########################################
class TestExperimentFlow:
    def test_join_experiment_returns_waiting(self, live_server_url):
        """
        GIVEN a valid experiment ID
        WHEN GET /join/<experimentID> is called
        THEN Flask returns 200 with the experiment ID and stage "WAITING".

        This is the first thing the watch calls when it connects.
        """
        resp = requests.get(f"{live_server_url}/join/test-exp-001", timeout=5) # send a real GET request to the join endpoint — this is what the real watch does first
        assert resp.status_code == 200 # confirm Flask returned a success response
        data = resp.json() # parse the JSON response body into a Python dictionary
        assert data["experimentID"] == "test-exp-001"  # confirm Flask echoed back the correct experiment ID
        assert data["stage"] == "WAITING" # confirm the experiment starts in the WAITING stage as expected

    def test_status_endpoint_advances_through_all_stages(self, live_server_url):
        """
        GIVEN an experiment has been joined (state counter reset to 0)
        WHEN the status endpoint is polled enough times
        THEN all five stages appear in order:
             WAITING → GAIT → GAIT_COMPLETE → RT_TEST → COMPLETE

        This verifies Flask's state machine works correctly end-to-end.
        """
        session = requests.Session()  # use a Session so the same connection is reused across all polls — more efficient than opening a new connection each time

        session.get(f"{live_server_url}/join/test-exp-002", timeout=5)  # join the experiment first to reset Flask's global state counter back to 0

        stages_seen = []  # empty list to record each new stage as it appears
        for _ in range(40):  # poll 40 times — enough to reach COMPLETE which needs 31+ polls
            resp  = session.get(f"{live_server_url}/join/test-exp-002/status", timeout=5)  # poll the status endpoint — Flask increments its counter each time
            stage = resp.json()["stage"] # extract the current stage from the JSON response
            if stage not in stages_seen: # only record a stage the first time it appears — avoids duplicates
                stages_seen.append(stage) # add the new stage to the list

        assert stages_seen == ["WAITING", "GAIT", "GAIT_COMPLETE", "RT_TEST", "COMPLETE"]  # confirm all five stages appeared in the correct order

    def test_sensor_data_endpoint_accepts_gait_payload(self, live_server_url):
        """
        GIVEN the /api/sensor-data endpoint exists
        WHEN a valid GAIT payload is POSTed
        THEN Flask returns 200.

        This verifies the endpoint is wired up correctly before running
        the full stub integration test below.
        """
        readings = [make_sensor_reading(1000 + i * 20, 0.1, 0.9, 0.05) for i in range(3)] # build 3 fake sensor readings spaced 20ms apart
        payload  = make_sensor_dto(stage="GAIT", readings=readings) # wrap the readings in the full JSON payload the watch would send

        resp = requests.post(
            f"{live_server_url}/api/sensor-data", # POST to the sensor data endpoint
            json=payload,  # send the payload as JSON in the request body
            timeout=5,  # give Flask up to 5 seconds to respond before failing
        )
        assert resp.status_code == 200  # confirm Flask accepted the payload and returned a success response

    def test_sensor_data_endpoint_accepts_rt_test_payload(self, live_server_url):
        """
        GIVEN the /api/sensor-data endpoint exists
        WHEN a valid RT_TEST payload is POSTed with trial and memStep
        THEN Flask returns 200.
        """
        readings = [make_sensor_reading(1000 + i * 20, 0.1, 0.9, 0.05) for i in range(3)] # build 3 fake sensor readings for a reaction time trial
        payload  = make_sensor_dto(stage="RT_TEST", readings=readings, trial=0, mem_step=1) # wrap readings in a payload with RT_TEST stage, trial number, and memory round number

        resp = requests.post(
            f"{live_server_url}/api/sensor-data",  # POST to the same sensor data endpoint — it should handle both GAIT and RT_TEST payloads
            json=payload, # send the payload as JSON
            timeout=5, # give Flask up to 5 seconds to respond
        )
        assert resp.status_code == 200  # confirm Flask accepted the RT_TEST payload successfully

    def test_watch_stub_completes_full_experiment(self, watch_stub, live_server_url):
        """
        GIVEN the watch stub is connected to the live server
        WHEN run_full_experiment() is called
        THEN all HTTP responses are 2xx and the experiment completes.

        This is the main integration test — it simulates the full experiment
        lifecycle from join → gait → RT test → complete, exactly as the
        real watch would behave.
        """
        # reset Flask's global state counter before running the stub
        requests.get(f"{live_server_url}/join/test-experiment-001", timeout=5)

        result = watch_stub.run_full_experiment(
            gait_duration_s=5,  # 5 seconds of gait data instead of 30 — keeps the test fast
            n_mem_steps=3, # 3 memory rounds instead of 10 — keeps the test fast
        )

        assert result["all_ok"], ( # True only if every single HTTP response from Flask was 2xx
            "One or more HTTP responses were not 2xx — "
            "check that all Flask endpoints return success responses."
        )
        assert result["gait_readings_sent"] == 250  # 5 seconds * 50Hz = 250 readings — confirms the correct amount of data was generated
        assert len(result["rt_results"]) == 3 # one (response, rt_ms) tuple per memory round — confirms all 3 rounds were sent

    def test_watch_stub_rt_results_within_control_group_range(self, watch_stub, live_server_url):
        """
        GIVEN the watch stub runs a full experiment
        WHEN reaction times are inspected
        THEN every RT falls within the observed control group range (900ms - 4200ms).
        """
        from tests.stubs.watch_stub import ReactionTimeGenerator  # imported here to keep the top-level imports clean — only needed in this one test

        # reset Flask's global state counter before running the stub
        requests.get(f"{live_server_url}/join/test-experiment-001", timeout=5)

        result = watch_stub.run_full_experiment(
            gait_duration_s=5,   # 5 seconds of gait data — fast
            n_mem_steps=5, # 5 memory rounds — enough to test the range without being slow
        )

        for _, rt_ms in result["rt_results"]:  # loop through each (response, rt_ms) pair — we only care about the rt_ms value here
            assert ReactionTimeGenerator.RT_MIN_MS <= rt_ms <= ReactionTimeGenerator.RT_MAX_MS, (  # confirm this RT falls within the observed control group range
                f"RT of {rt_ms}ms is outside observed control group range "
                f"({ReactionTimeGenerator.RT_MIN_MS}–{ReactionTimeGenerator.RT_MAX_MS}ms)" # if it fails, print which RT was out of range and what the expected range is
            )

