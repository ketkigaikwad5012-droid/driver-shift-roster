
import os
import time
import unittest
from datetime import date, timedelta

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC


BASE_URL = os.environ.get("BASE_URL", "http://localhost:8082")


class DriverRosterTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        options = Options()
        options.add_argument("--start-maximized")

        cls.driver = webdriver.Chrome(options=options)
        cls.wait = WebDriverWait(cls.driver, 15)

    @classmethod
    def tearDownClass(cls):
        if hasattr(cls, "driver"):
            cls.driver.quit()

    def get_page_message(self):
        return self.driver.find_element(By.TAG_NAME, "body").text

    def set_input_value(self, element_id, value):
        element = self.wait.until(
            EC.presence_of_element_located((By.ID, element_id))
        )

        self.driver.execute_script(
            """
            const input = arguments[0];
            input.value = arguments[1];
            input.dispatchEvent(new Event('input', {bubbles: true}));
            input.dispatchEvent(new Event('change', {bubbles: true}));
            """,
            element,
            value,
        )

    def set_time(self, element_id, value):
        self.set_input_value(element_id, value)

    def submit_form_and_wait(self, form_xpath):
        form = self.wait.until(
            EC.presence_of_element_located((By.XPATH, form_xpath))
        )

        form.submit()

        self.wait.until(EC.staleness_of(form))

        self.wait.until(
            EC.presence_of_element_located((By.XPATH, form_xpath))
        )

    def find_available_driver_id(self):
        self.driver.get(BASE_URL + "/drivers")

        self.wait.until(
            EC.presence_of_element_located(
                (By.XPATH, "//table//tbody")
            )
        )

        rows = self.driver.find_elements(
            By.XPATH, "//table//tbody/tr[td]"
        )

        for row in rows:
            cells = row.find_elements(By.TAG_NAME, "td")

            if len(cells) >= 5 and cells[3].text.strip() == "Available":
                driver_id = cells[0].text.strip()

                if driver_id:
                    return driver_id

        self.fail(
            "No available driver found. Mark a driver as Available "
            "on the Driver Management page."
        )

    def register_test_driver(self, name_prefix):
        """Register a unique driver and return the new driver's ID."""

        self.driver.get(BASE_URL + "/drivers")

        timestamp = str(time.time_ns())
        driver_name = name_prefix + " " + timestamp
        unique_phone = "8" + str(time.time_ns())[-9:]

        name_input = self.wait.until(
            EC.visibility_of_element_located((By.ID, "name"))
        )
        name_input.send_keys(driver_name)

        self.driver.find_element(
            By.ID, "phone"
        ).send_keys(unique_phone)

        self.submit_form_and_wait("//form[@action='/drivers']")

        rows = self.wait.until(
            EC.presence_of_all_elements_located(
                (By.XPATH, "//table//tbody/tr[td]")
            )
        )

        for row in rows:
            cells = row.find_elements(By.TAG_NAME, "td")

            if len(cells) >= 3 and cells[1].text.strip() == driver_name:
                driver_id = cells[0].text.strip()

                if driver_id:
                    return driver_id

        self.fail("Could not find the newly registered test driver.")

    def fill_shift_form(self, driver_id, shift_day, start_time, end_time):
        self.driver.get(BASE_URL + "/shifts")

        driver_select = Select(
            self.wait.until(
                EC.presence_of_element_located((By.ID, "driverId"))
            )
        )

        driver_select.select_by_value(str(driver_id))

        self.set_input_value("shiftDate", shift_day)
        self.set_time("startTime", start_time)
        self.set_time("endTime", end_time)

    def submit_shift(self):
        self.submit_form_and_wait("//form[@action='/shifts']")

    # ---------------------------------------------------------
    # TEST 1: Home page loads
    # ---------------------------------------------------------

    def test_home_page_loads(self):
        self.driver.get(BASE_URL + "/")

        page_text = self.get_page_message()

        self.assertIn("Driver Shift Roster", page_text)

        print("PASS: Home page loaded")

    # ---------------------------------------------------------
    # TEST 2: Driver management page loads
    # ---------------------------------------------------------

    def test_drivers_page_loads(self):
        self.driver.get(BASE_URL + "/drivers")

        self.wait.until(
            EC.presence_of_element_located(
                (By.XPATH, "//table")
            )
        )

        page_text = self.get_page_message()

        self.assertIn("Driver Management", page_text)

        print("PASS: Drivers page loaded")

    # ---------------------------------------------------------
    # TEST 3: Shift scheduling page loads
    # ---------------------------------------------------------

    def test_shifts_page_loads(self):
        self.driver.get(BASE_URL + "/shifts")

        self.wait.until(
            EC.presence_of_element_located((By.ID, "driverId"))
        )

        page_text = self.get_page_message()

        self.assertIn("Shift Scheduling", page_text)

        print("PASS: Shifts page loaded")

    # ---------------------------------------------------------
    # TEST 4: Driver registration works
    # ---------------------------------------------------------

    def test_register_driver(self):
        driver_name = "Selenium Test Driver " + str(time.time_ns())
        unique_phone = "8" + str(time.time_ns())[-9:]

        self.driver.get(BASE_URL + "/drivers")

        self.wait.until(
            EC.visibility_of_element_located((By.ID, "name"))
        ).send_keys(driver_name)

        self.driver.find_element(
            By.ID, "phone"
        ).send_keys(unique_phone)

        self.submit_form_and_wait("//form[@action='/drivers']")

        page_text = self.get_page_message()

        self.assertIn(driver_name, page_text)
        self.assertIn(unique_phone, page_text)

        print("PASS: Driver registration works")

    # ---------------------------------------------------------
    # TEST 5: Driver availability can be toggled
    # ---------------------------------------------------------

    def test_toggle_driver_availability(self):
        self.driver.get(BASE_URL + "/drivers")

        self.wait.until(
            EC.presence_of_element_located(
                (By.XPATH, "//table//tbody")
            )
        )

        rows = self.driver.find_elements(
            By.XPATH, "//table//tbody/tr[td]"
        )

        target_row = None

        for row in rows:
            cells = row.find_elements(By.TAG_NAME, "td")

            if len(cells) >= 5:
                target_row = row
                break

        self.assertIsNotNone(
            target_row,
            "No registered driver was found to test availability."
        )

        cells = target_row.find_elements(By.TAG_NAME, "td")
        driver_id = cells[0].text.strip()
        original_status = cells[3].text.strip()

        self.assertTrue(driver_id, "Driver ID is missing.")

        toggle_button = target_row.find_element(
            By.XPATH, ".//button"
        )

        toggle_button.click()

        self.wait.until(EC.staleness_of(target_row))

        self.driver.get(BASE_URL + "/drivers")

        self.wait.until(
            EC.presence_of_element_located(
                (By.XPATH, "//table//tbody")
            )
        )

        updated_rows = self.driver.find_elements(
            By.XPATH, "//table//tbody/tr[td]"
        )

        updated_status = None

        for row in updated_rows:
            updated_cells = row.find_elements(By.TAG_NAME, "td")

            if (
                len(updated_cells) >= 5
                and updated_cells[0].text.strip() == driver_id
            ):
                updated_status = updated_cells[3].text.strip()
                break

        self.assertIsNotNone(
            updated_status,
            "Driver could not be found after availability toggle."
        )

        expected_status = (
            "Unavailable"
            if original_status == "Available"
            else "Available"
        )

        self.assertEqual(
            expected_status,
            updated_status,
            "Driver availability did not change as expected."
        )

        print("PASS: Driver availability toggle works")

    # ---------------------------------------------------------
    # TEST 6: Shift scheduling works
    # ---------------------------------------------------------

    def test_schedule_shift(self):
        driver_id = self.register_test_driver(
            "Selenium Schedule Driver"
        )

        shift_day = (date.today() + timedelta(days=90)).isoformat()

        self.fill_shift_form(
            driver_id,
            shift_day,
            "03:00",
            "04:00",
        )

        self.submit_shift()

        page_text = self.get_page_message()

        self.assertIn(
            "Shift scheduled successfully!",
            page_text,
            "Shift scheduling failed. Page content:\n" + page_text,
        )

        self.assertIn(shift_day, page_text)

        print("PASS: Shift scheduling works")

    # ---------------------------------------------------------
    # TEST 7: Overlapping shifts are rejected
    # ---------------------------------------------------------

    def test_overlapping_shift_is_rejected(self):
        # Register a dedicated driver to avoid old database records.
        driver_id = self.register_test_driver(
            "Selenium Overlap Driver"
        )

        shift_day = (date.today() + timedelta(days=92)).isoformat()

        # Create the first shift.
        self.fill_shift_form(
            driver_id,
            shift_day,
            "09:00",
            "10:00",
        )

        self.submit_shift()

        page_text = self.get_page_message()

        self.assertIn(
            "Shift scheduled successfully!",
            page_text,
            "The first shift was not created. Page content:\n" + page_text,
        )

        # Attempt a second shift that overlaps from 09:30 to 10:00.
        self.fill_shift_form(
            driver_id,
            shift_day,
            "09:30",
            "10:30",
        )

        self.submit_shift()

        page_text = self.get_page_message()

        self.assertIn(
            "This driver already has a shift during that time.",
            page_text,
            "The application did not reject the overlapping shift. "
            "Page content:\n" + page_text,
        )

        print("PASS: Overlapping shift was rejected")


if __name__ == "__main__":
    unittest.main(verbosity=2)
