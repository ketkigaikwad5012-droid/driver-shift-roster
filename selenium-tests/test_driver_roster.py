
import unittest
import time
from datetime import date, timedelta

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC

import os

BASE_URL = os.environ.get("BASE_URL", "http://localhost:8082")


class DriverRosterTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        options = Options()
        options.add_argument("--start-maximized")
        cls.driver = webdriver.Chrome(options=options)
        cls.wait = WebDriverWait(cls.driver, 10)

    @classmethod
    def tearDownClass(cls):
        cls.driver.quit()

    def set_time(self, element_id, value):
        """Set an HTML time input using its 24-hour value."""
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
            value
        )

    def find_available_driver_id(self):
        self.driver.get(BASE_URL + "/drivers")

        rows = self.wait.until(
            EC.presence_of_all_elements_located(
                (By.XPATH, "//tbody/tr[td]")
            )
        )

        for row in rows:
            cells = row.find_elements(By.TAG_NAME, "td")
            if len(cells) >= 5 and cells[3].text.strip() == "Available":
                return cells[0].text.strip()

        self.fail("No available driver found. Mark a driver Available first.")

    def fill_shift_form(self, driver_id, shift_day, start_time, end_time):
        self.driver.get(BASE_URL + "/shifts")

        driver_select = Select(
            self.wait.until(
                EC.presence_of_element_located((By.ID, "driverId"))
            )
        )
        driver_select.select_by_value(str(driver_id))

        date_input = self.driver.find_element(By.ID, "shiftDate")
        self.driver.execute_script(
            """
            const input = arguments[0];
            input.value = arguments[1];
            input.dispatchEvent(new Event('input', {bubbles: true}));
            input.dispatchEvent(new Event('change', {bubbles: true}));
            """,
            date_input,
            shift_day
        )

        self.set_time("startTime", start_time)
        self.set_time("endTime", end_time)

    def submit_shift(self):
        self.driver.find_element(
            By.XPATH,
            "//button[@type='submit' and normalize-space()='Schedule Shift']"
        ).click()

    def test_home_page_loads(self):
        self.driver.get(BASE_URL + "/")
        self.wait.until(lambda d: d.title.strip() != "")
        self.assertEqual(self.driver.title.strip(), "Driver Shift Roster")
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

        unique_phone = "8" + str(int(time.time()))[-9:]
        driver_name = "Selenium Test Driver " + str(int(time.time()))

        self.wait.until(
            EC.visibility_of_element_located((By.ID, "name"))
        ).send_keys(driver_name)
        self.driver.find_element(By.ID, "phone").send_keys(unique_phone)

        self.driver.find_element(
            By.XPATH,
            "//button[@type='submit' and normalize-space()='Add Driver']"
        ).click()

        self.wait.until(
            EC.text_to_be_present_in_element(
                (By.TAG_NAME, "body"), driver_name
            )
        )
        self.assertIn(unique_phone, self.driver.page_source)
        print("PASS: Driver registration works")

    def test_toggle_driver_availability(self):
        self.driver.get(BASE_URL + "/drivers")
        driver_name = "Selenium Test Driver"

        rows = self.driver.find_elements(
            By.XPATH,
            f"//tr[td[starts-with(normalize-space(), '{driver_name}')] and td[5]//button]"
        )
        self.assertTrue(rows, "No Selenium test driver found")

        row = rows[-1]
        old_status = row.find_element(By.XPATH, "./td[4]").text.strip()
        row.find_element(By.XPATH, ".//button[@type='submit']").click()

        self.wait.until(
            lambda d: d.find_element(
                By.XPATH,
                f"//tr[td[starts-with(normalize-space(), '{driver_name}')]][last()]/td[4]"
            ).text.strip() != old_status
        )
        print("PASS: Driver availability toggle works")

    def test_schedule_shift(self):
        driver_id = self.find_available_driver_id()
        shift_day = (date.today() + timedelta(days=30)).isoformat()

        self.fill_shift_form(
            driver_id, shift_day, "09:00", "10:00"
        )
        self.submit_shift()

        self.wait.until(
            EC.text_to_be_present_in_element(
                (By.TAG_NAME, "body"),
                "Shift scheduled successfully!"
            )
        )
        self.assertIn(shift_day, self.driver.page_source)
        print("PASS: Shift scheduled successfully")

    def test_overlapping_shift_is_rejected(self):
        # Create a fresh date so the first shift is unlikely to conflict
        # with existing records.
        driver_id = self.find_available_driver_id()
        shift_day = (date.today() + timedelta(days=60)).isoformat()

        # First shift: 09:00–10:00.
        self.fill_shift_form(
            driver_id, shift_day, "09:00", "10:00"
        )
        self.submit_shift()

        self.wait.until(
            EC.text_to_be_present_in_element(
                (By.TAG_NAME, "body"),
                "Shift scheduled successfully!"
            )
        )

        # Second shift overlaps the first by 30 minutes.
        self.fill_shift_form(
            driver_id, shift_day, "09:30", "10:30"
        )
        self.submit_shift()

        self.wait.until(
            EC.text_to_be_present_in_element(
                (By.TAG_NAME, "body"),
                "This driver already has a shift during that time."
            )
        )
        print("PASS: Overlapping shift rejected successfully")


if __name__ == "__main__":
    unittest.main(verbosity=2)
