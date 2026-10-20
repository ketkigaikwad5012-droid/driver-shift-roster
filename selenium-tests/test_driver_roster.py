
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
        """Submit a form and wait for its redirect to finish."""
        form = self.wait.until(
            EC.presence_of_element_located((By.XPATH, form_xpath))
        )
        form.submit()

        self.wait.until(EC.staleness_of(form))
        self.wait.until(
            EC.presence_of_element_located((By.XPATH, form_xpath))
        )

    def find_available_driver_id(self):
        """Find an available driver's ID from the driver table."""
        self.driver.get(BASE_URL + "/drivers")

        self.wait.until(
            EC.presence_of_element_located(
                (By.XPATH, "//table//tbody")
            )
        )

        rows = self.driver.find_elements(
            By.XPATH, "//table//tbody/tr[td]"
        )

        # Table columns: ID, Name, Phone, Availability, Action.
        for row in rows:
            cells = row.find_elements(By.TAG_NAME, "td")

            if (
                len(cells) >= 5
                and cells[3].text.strip() == "Available"
            ):
                driver_id = cells[0].text.strip()
                if driver_id:
                    return driver_id

        self.fail(
            "No available driver found. Mark a driver as Available "
            "on the Driver Management page."
        )

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

    def test_home_page_loads(self):
        self.driver.get(BASE_URL + "/")

        self.wait.until(lambda d: d.title.strip() != "")
        self.assertEqual(
            self.driver.title.strip(),
            "Driver Shift Roster",
        )
        print("PASS: Home page loaded")

    def test_drivers_page_loads(self):
        self.driver.get(BASE_URL + "/drivers")

        self.wait.until(
            EC.visibility_of_element_located((By.TAG_NAME, "h1"))
        )
        self.assertIn("Driver Management", self.driver.page_source)
        print("PASS: Drivers page loaded")

    def test_shifts_page_loads(self):
        self.driver.get(BASE_URL + "/shifts")

        self.wait.until(
            EC.presence_of_element_located((By.ID, "driverId"))
        )
        self.assertIn("shift", self.driver.page_source.lower())
        print("PASS: Shifts page loaded")

    def test_register_driver(self):
        self.driver.get(BASE_URL + "/drivers")

        timestamp = str(time.time_ns())
        driver_name = "Selenium Test Driver " + timestamp
        unique_phone = "8" + str(time.time_ns())[-9:]

        self.wait.until(
            EC.visibility_of_element_located((By.ID, "name"))
        ).send_keys(driver_name)

        self.driver.find_element(By.ID, "phone").send_keys(unique_phone)

        self.submit_form_and_wait("//form[@action='/drivers']")

        page_text = self.get_page_message()

        self.assertIn(
            driver_name,
            page_text,
            "Driver registration failed. Page content:\n" + page_text,
        )
        self.assertIn(unique_phone, page_text)
        print("PASS: Driver registration works")

    def test_toggle_driver_availability(self):
        self.driver.get(BASE_URL + "/drivers")

        rows = self.wait.until(
            EC.presence_of_all_elements_located(
                (By.XPATH, "//table//tbody/tr[td]")
            )
        )

        target_row = None

        for row in reversed(rows):
            cells = row.find_elements(By.TAG_NAME, "td")
            if (
                len(cells) >= 5
                and "Selenium Test Driver" in cells[1].text
            ):
                target_row = row
                break

        self.assertIsNotNone(
            target_row,
            "No Selenium test driver found in the driver table.",
        )

        cells = target_row.find_elements(By.TAG_NAME, "td")
        old_status = cells[3].text.strip()

        target_row.find_element(
            By.XPATH, ".//form//button[@type='submit']"
        ).click()

        def status_changed(driver):
            try:
                current_rows = driver.find_elements(
                    By.XPATH, "//table//tbody/tr[td]"
                )

                for row in reversed(current_rows):
                    cells = row.find_elements(By.TAG_NAME, "td")

                    if (
                        len(cells) >= 5
                        and "Selenium Test Driver" in cells[1].text
                        and cells[3].text.strip() != old_status
                    ):
                        return cells[3].text.strip()

                return False
            except Exception:
                return False

        new_status = self.wait.until(status_changed)
        self.assertIn(new_status, ("Available", "Unavailable"))
        print("PASS: Driver availability toggle works")

    def test_schedule_shift(self):
        driver_id = self.find_available_driver_id()

        # Use a future date and a separate time slot.
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

    def test_overlapping_shift_is_rejected(self):
        driver_id = self.find_available_driver_id()

        # Use a different date from the ordinary scheduling test.
        shift_day = (date.today() + timedelta(days=91)).isoformat()

        self.fill_shift_form(
            driver_id,
            shift_day,
            "03:00",
            "04:00",
        )
        self.submit_shift()

        first_response = self.get_page_message()

        self.assertIn(
            "Shift scheduled successfully!",
            first_response,
            "The first shift was not created. Page content:\n"
            + first_response,
        )

        # Overlap the first shift by 30 minutes.
        self.fill_shift_form(
            driver_id,
            shift_day,
            "03:30",
            "04:30",
        )
        self.submit_shift()

        second_response = self.get_page_message()

        self.assertIn(
            "This driver already has a shift during that time.",
            second_response,
            "The overlapping shift was not rejected. Page content:\n"
            + second_response,
        )
        print("PASS: Overlapping shift rejected")


if __name__ == "__main__":
    unittest.main(verbosity=2)
