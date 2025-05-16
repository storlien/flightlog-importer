import os.path
import re
from datetime import datetime
from time import sleep

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

from username_and_password import USERNAME_FLIGHTLOG, PASSWORD_FLIGHTLOG, USERNAME_VOLANDOO, PASSWORD_VOLANDOO

MAX_ATTEMPTS = 10

# Setup
options = Options()
options.headless = False
options.add_argument("--enable-logging")
options.add_argument("--v=1")
driver = webdriver.Chrome(options=options)
driver.set_window_size(1500, 800)
driver.set_page_load_timeout(300)
driver.set_script_timeout(300)
driver.implicitly_wait(30)
wait = WebDriverWait(driver, 10)

def main():
    global wait
    flightlog_newest_date = None


    # Get the date of the newest flight uploaded to flightlog
    try:
        # Login to flightlog
        driver.get("https://flightlog.org/fl.html?l=1&a=37")

        wait.until(EC.visibility_of_element_located((By.NAME, "login_name"))).send_keys(USERNAME_FLIGHTLOG)
        driver.find_element(By.NAME, "pw").send_keys(PASSWORD_FLIGHTLOG)
        driver.find_element(By.NAME, "login").click()
        sleep(2)

        wait = WebDriverWait(driver, 10)
        td_elements = wait.until(EC.presence_of_all_elements_located((By.TAG_NAME, 'td')))

        # Get the date of the newest flight uploaded to flightlog
        for td in td_elements:
            text = td.text.strip()
            match = re.search(r'\d{4}-\d{2}-\d{2}', text)
            if match:
                flightlog_newest_date = datetime.strptime(match.group(), "%Y-%m-%d").date()
                print("Date of newest flight uploaded to flightlog.org:", flightlog_newest_date)
                break
    except Exception as e:
        print("ERROR: The flightlog.org website is probably not working.")
        print(e)

    assert flightlog_newest_date, "ERROR: The date of the newest flight was not found on flightlog.org."


    # Export flights from Volandoo.com
    try:
        # Login to Volandoo
        driver.execute_script("window.open('');")
        driver.switch_to.window(driver.window_handles[-1])
        driver.get("https://volandoo.com/")
        wait = WebDriverWait(driver, 10)

        # Find and click login button
        homepage_buttons = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '.MuiButtonBase-root.MuiButton-root.MuiButton-text.MuiButton-textPrimary.MuiButton-sizeMedium.MuiButton-textSizeMedium.MuiButton-colorPrimary.css-1dtzxei')))
        for btn in homepage_buttons:
            if btn.text.strip().lower() == "login":
                btn.click()

        # Fill out login forms
        driver.find_element(By.NAME, "username").send_keys(USERNAME_VOLANDOO)
        driver.find_element(By.NAME, "password").send_keys(PASSWORD_VOLANDOO)

        # Find and click login button
        button = driver.find_element(By.XPATH, '//div[@class="MuiStack-root css-1j8t7mm"]//button')
        print(button)
        button.click()
        sleep(5)

        # Go to logbook site
        driver.get("https://volandoo.com/logbook")
        sleep(1)

        # Retrieve flight dates newer than flightlog logbook
        date_elements = wait.until(EC.visibility_of_all_elements_located((By.XPATH, '//a[contains(@href, "/tracks/")]//p/span')))
        volandoo_dates = [datetime.strptime(date_element.text, "%m/%d/%Y").date() for date_element in date_elements]
        assert volandoo_dates, "ERROR: No flight dates found on volandoo website."

        new_flight_date_indices = list()
        for i, new_flight_date in enumerate(volandoo_dates):
            if new_flight_date > flightlog_newest_date:
                new_flight_date_indices.append(i)
                print("New flight date:", new_flight_date)

        print(len(new_flight_date_indices), "number of new flights to import!")

        # Save flight number and href links of new flights
        flight_number_href_list = list()
        for i in new_flight_date_indices:
            flight_link = date_elements[i].find_element(By.XPATH, './ancestor::a')
            href = flight_link.get_attribute('href')
            # distance = [column.text.removesuffix(" km") for column in flight_link.find_elements(By.XPATH, './/td') if "km" in column.text][0]
            flight_number_href_list.append((href.split('/')[-1], href))

        print("Number of flights in list:", len(flight_number_href_list))

        # Check if the .igc files are already downloaded
        igc_files_downloaded = True
        for flight_tuple in flight_number_href_list:
            file_path = os.path.join(os.path.expanduser("~"), "Downloads", f"{flight_tuple[0]}.igc")
            if not os.path.exists(file_path):
                igc_files_downloaded = False

        # Download the .igc file from each flight
        if not igc_files_downloaded:
            for flight_tuple in flight_number_href_list:
                print(flight_tuple[0])
                driver.get(flight_tuple[1])
                sleep(2)

                # Click info button (button number 14)
                buttons = driver.find_elements(By.TAG_NAME, "button")
                circle_buttons = [button for button in buttons if "MuiButtonBase-root MuiFab-root MuiFab-circular MuiFab-sizeSmall MuiFab-default MuiFab-root MuiFab-circular MuiFab-sizeSmall MuiFab-default css-1nbbke5" in button.get_attribute("class")]
                assert circle_buttons, "No info button found! Empty list."
                if len(circle_buttons) == 5:
                    driver.execute_script("arguments[0].click();", circle_buttons[1])
                elif len(circle_buttons) == 4:
                    driver.execute_script("arguments[0].click();", circle_buttons[0])
                else:
                    raise Exception("No info button found!")
                sleep(1)

                # Download the .igc file
                download_link = driver.find_element(By.CSS_SELECTOR, "a[href$='.igc']")
                driver.execute_script("arguments[0].click();", download_link)
                print("Downloaded!")
                sleep(2)

        else:
            print("All .igc files have been downloaded before!")

        # Reverse sort list to get oldest flights first
        flight_number_href_list.sort(reverse=True)

    except Exception as e:
        print("ERROR: The volandoo.com website is probably not working.")
        print(e)


    # Import flights to flightlog.org
    try:
        for flight_tuple in flight_number_href_list:
            print("Starting import of flight number", flight_tuple[0], "...")
            # Go to "New flight" on the flightlog website
            driver.switch_to.window(driver.window_handles[0])
            driver.find_element(By.LINK_TEXT, "New flight").click()
            register_new_flight_link = wait.until(EC.presence_of_element_located((By.PARTIAL_LINK_TEXT, "Register a new flight or group of flights not connected to a specific start")))
            driver.get(register_new_flight_link.get_attribute("href"))

            # Upload tracklog file
            file_path = os.path.join(os.path.expanduser("~"), "Downloads", f"{flight_tuple[0]}.igc")
            upload_tracklog_link = wait.until(EC.presence_of_element_located((By.NAME, "tracklog")))
            try:
                upload_tracklog_link.send_keys(file_path)
            except Exception as e:
                print("Upload failed:", e)

            # Click save
            sleep(2)
            for _ in range(MAX_ATTEMPTS):
                try:
                    driver.find_element(By.NAME, "save").click()
                    print("Successful attempt")
                    break
                except Exception as e:
                    print("Failed attempt to save")
                    continue

            # Fill out form
            print("Filling out form...")
            wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "input[name='takeofftype_id'][id='mountain']"))).click() # Takeoff type (mountain)
            wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "input[name='class_id'][id='1']"))).click() # Type of flight (PG)
            wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "input[name='brandmodel_id']")))[0].click() # Wing (first wing)
            print("Done with form")

            # Upload tracklog file again
            upload_tracklog_link = wait.until(EC.presence_of_element_located((By.NAME, "tracklog")))
            try:
                upload_tracklog_link.send_keys(file_path)
            except Exception as e:
                print("Upload failed:", e)

            # Click save
            sleep(2)
            for _ in range(MAX_ATTEMPTS):
                try:
                    driver.find_element(By.NAME, "save").click()
                    print("Successful attempt")
                    break
                except Exception as e:
                    print("Failed attempt to save")
                    continue

            details_element = wait.until(EC.presence_of_element_located((By.XPATH, "//pre[contains(text(), 'Total distance')]")))
            match = re.search(r"Total distance\s+([\d.]+) km", details_element.text)
            distance = str(match.group(1).strip()) if match else None
            assert distance, "Error. No distance found."

            # Update distance of trip
            print("Found distance.")
            edit_flight_link = wait.until(EC.element_to_be_clickable((By.LINK_TEXT, "Edit flight")))
            edit_flight_link.click()
            wait.until(EC.staleness_of(edit_flight_link))
            distance_input_link = driver.find_element(By.CSS_SELECTOR, "input[name='distance']")
            distance_input_link.clear()
            distance_input_link.send_keys(distance)
            driver.find_element(By.NAME, "save").click()
            wait.until(EC.staleness_of(distance_input_link))

            print("Done with importing of flight number", flight_tuple[0])

        print("Done with all imports!")

    except Exception as e:
        print("ERROR: The flightlog.org website might not be working.", e)

if __name__ == "__main__":
    main()