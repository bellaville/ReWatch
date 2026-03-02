"""
Holds fixtures for UI and integration tests (these fixtures only run when
UI tests are being executed)

The four fixtures:
    live_server_url - runs Flask in a background thread on port 5001
    watch_stub - WatchStub pointed at the live server (http://127.0.0.1:5001)
    browser - opens hrome browser (without a visible window) controlled by Selenium
    logged_in_broswer - uses browser and already logged in as a physician
"""
import pytest
import threading
import requests as req
import time

from run import create_app
from tests.stubs.watch_stub import WatchStub
from selenium.webdriver.chrome.options import Options
from selenium import webdriver

###############
# LIVE SERVER #
###############
@pytest.fixture(scope="module")
def live_server_url():
    """
    Starts Flask in a background thread on port 5001

    scope="module" -> server starts once per test file, shared across
    all tests in that file
    """
    host = "127.0.1"
    port = 5001

    flask_app = create_app(test_config=True)

    from tests.endpoint_creation import register_testing_endpoints
    register_testing_endpoints(flask_app)

    # start Flask in a background thread so it runs alongside the tests
    threading.Thread(
        target=lambda: flask_app.run(host=host, port=port, use_reloader=False),
        daemon=True # the thread dies automatically when tests finish
    ).start()

    base_url = f"http://{host}:{port}"
    # poll until Flask responds
    for u in range(20):
        try:
            # send GET request to see if Flask is responding yet
            req.get(base_url, timeout=1)
            break
        except req.exceptions.ConnectionError:
            time.sleep(0.3)

    yield base_url # hand the URL to test


##############
# WATCH STUB #
##############
@pytest.fixture(scope="function") # scope="function" -> each individual tests gets a new stub
def watch_stub(live_server_url):
    """
    Returns a WatchStub connected to the live test server
    """
    stub = WatchStub(
        base_url=live_server_url,
        experiment_id="12345",
        upload_path="/api/sensor-data",
        seed=123
    )
    stub.gait_duration = 5.0 # overriding so that tests run faster
    return stub


####################
# SELENIUM BROWSER #
####################
@pytest.fixture(scope="module")
def browser():
    """
    Opens a headless (no visible window required for GitHub Action CI)
    Chrome browser for UI tests
    """
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox") # required in GitHub Actions
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")

    driver = webdriver.Chrome(options=options)
    driver.implicitly_wait(5) # tell Selenium to wait up to 5 seconds for elements to render

    yield driver # hand the browser to the test

    driver.quit() # after all test sin the module finish, close browser

#####################
# LOGGED-IN BROWSER #
#####################
@pytest.fixture(scope="module")
def logged_in_browser(browser, live_server_url):
    """
    Returns a Selenium browser already logged in as a physician

    Most UI tests need an authenticated user. This fixture handles
    login once and shares the session across all tests in the module
    """
    from selenium.webdriver.common.by import By # By provides ways to locate elements
    from selenium.webdriver.support.ui import WebDriverWait # WebDriverWait pauses until a condition is met 
    from selenium.webdriver.support import expected_conditions as EC # EC provides pre-built conditions to wait for 

    # tell Chrome to navigate to the login page
    browser.get(f"{live_server_url}/auth/login") 

    # wait up to 5 seconds for the email field to appear
    WebDriverWait(browser, 5).until(
        EC.presence_of_element_located((By.NAME, "email"))
    )

    browser.find_element(By.NAME, "email").send_keys("dr.stephen@avengers.com")
    browser.find_element(By.NAME, "password").send_keys("password123")
    # find the submit button and click it
    browser.find_element(By.CSS_SELECTOR, "button[type='submit']").click()

    time.sleep(1) # wait 1 second for the login redirect to complete

    # hand the now logged-in browser to any test that requests this fixture
    yield browser 