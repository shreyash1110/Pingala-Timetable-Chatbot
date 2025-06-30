import pandas as pd
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
import os

USERNAME = input("Enter your Pingala username: ")
PASSWORD = input("Enter your Pingala password: ")

driver = webdriver.Chrome()
driver.get("https://pingala.iitk.ac.in/")

wait = WebDriverWait(driver, 20)

try:
    iframe = wait.until(EC.presence_of_element_located((By.TAG_NAME, "iframe")))
    driver.switch_to.frame(iframe)
    print("Switched to iframe.")
except:
    print("No iframe found or unable to switch.")

username_box = wait.until(EC.presence_of_element_located((By.ID, "username")))
password_box = wait.until(EC.presence_of_element_located((By.NAME, "password")))

username_box.send_keys(USERNAME)
password_box.send_keys(PASSWORD)
password_box.send_keys(Keys.RETURN)
print("Login credentials entered.")

try:
    academic_management_link = wait.until(
        EC.element_to_be_clickable((By.XPATH, "//span[text()='Academic Management']"))
    )
    academic_management_link.click()
    print("Clicked 'Academic Management'.")

    time_table_link = wait.until(
        EC.element_to_be_clickable((By.XPATH, "//a[contains(.,'Time Table')]"))
    )
    time_table_link.click()
    print("Clicked 'Time Table'.")

    check_timetable_link = wait.until(
        EC.element_to_be_clickable((By.XPATH, "//a[contains(@href, \"javascript:loadFormext('listViewTimetable')\")]"))
    )
    check_timetable_link.click()
    print("Clicked 'Check Timetable'. Successfully navigated.")

    academic_year_chosen_container = wait.until(
        EC.element_to_be_clickable((By.ID, "academic_session_pk_chosen"))
    )
    academic_year_chosen_container.click()

    academic_year_option = wait.until(
        EC.element_to_be_clickable((By.XPATH, "//li[text()='2024-2025']"))
    )
    academic_year_option.click()
    print("Selected Academic Year: 2024-2025")

    semester_chosen_container = wait.until(
        EC.element_to_be_clickable((By.ID, "semester_master_pk_chosen"))
    )
    semester_chosen_container.click()

    semester_option_even = wait.until(
        EC.element_to_be_clickable((By.XPATH, "//ul[@class='chosen-results']/li[text()='Even']"))
    )
    semester_option_even.click()
    print("Selected Semester: Even")

    show_button = wait.until(
        EC.element_to_be_clickable((By.ID, "showTimeTableBtn"))
    )
    show_button.click()
    print("Clicked 'Show' button. Waiting for table to load.")

    display_records_select_element = wait.until(
        EC.visibility_of_element_located((By.NAME, "datatable_length"))
    )
    
    display_records_dropdown = Select(display_records_select_element)
    
    initial_rows_xpath = "//table[@id='datatable']/tbody/tr"
    initial_row_count = len(driver.find_elements(By.XPATH, initial_rows_xpath))
    print(f"Initial number of rows displayed: {initial_row_count}")

    display_records_dropdown.select_by_value("-1")
    print("Selected 'All' records per page.")

    try:
        wait.until(lambda d: len(d.find_elements(By.XPATH, initial_rows_xpath)) > initial_row_count or \
                             (len(d.find_elements(By.XPATH, initial_rows_xpath)) == initial_row_count and initial_row_count > 0 and display_records_select_element.get_attribute("value") == "-1"))
        print("Table appears to have updated with 'All' records.")
    except Exception as update_err:
        print(f"Warning: Table update might not have completed as expected after selecting 'All': {update_err}")
        print("Proceeding anyway, but data might be incomplete if table didn't fully load.")
    
    time.sleep(1) 

    timetable_table = wait.until(
        EC.presence_of_element_located((By.ID, "datatable"))
    )
    print("Timetable table element found.")

    tbody = wait.until(
        EC.presence_of_element_located((By.XPATH, "//table[@id='datatable']/tbody"))
    )
    print("Table body (tbody) found.")

    wait.until(
        EC.presence_of_element_located((By.XPATH, "//table[@id='datatable']/tbody/tr"))
    )
    print("At least one table row (tr) found in tbody.")

    header_elements = timetable_table.find_elements(By.XPATH, "./thead/tr[2]/th")
    column_names = [header.text.strip() for header in header_elements]

    fch_column_index = -1
    for idx, name in enumerate(column_names):
        if "First Course Handout(FCH)" in name:
            fch_column_index = idx
            break

    column_names_for_df = [col.replace('\n', ' ').strip() for col in column_names]
    if fch_column_index == -1: 
        column_names_for_df.append("FCH URL") 
    else:
        column_names_for_df[fch_column_index] = "FCH URL"

    print(f"Column names for DataFrame: {column_names_for_df}")

    all_rows_data = []

    table_rows_elements = wait.until(
        EC.presence_of_all_elements_located((By.XPATH, "//table[@id='datatable']/tbody/tr"))
    )
    print(f"Found {len(table_rows_elements)} rows for processing (after selecting 'All').")

    original_window = driver.current_window_handle

    for i in range(len(table_rows_elements)):
        current_row = wait.until(
            EC.presence_of_element_located((By.XPATH, f"//table[@id='datatable']/tbody/tr[{i+1}]"))
        )
        
        cells = current_row.find_elements(By.TAG_NAME, "td")
        
        row_data = [cell.text.strip() for cell in cells]
        
        fch_url_for_row = ""

        if fch_column_index != -1 and fch_column_index < len(cells):
            fch_cell = cells[fch_column_index]
            fch_link = fch_cell.find_elements(By.TAG_NAME, "a")

            if fch_link:
                print(f"Clicking FCH link for row {i+1} to get URL...")
                try:
                    wait.until(EC.element_to_be_clickable(fch_link[0])).click()
                    
                    wait.until(EC.number_of_windows_to_be(2))
                    
                    new_window_handle = [handle for handle in driver.window_handles if handle != original_window][0]
                    driver.switch_to.window(new_window_handle)
                    
                    fch_url_for_row = driver.current_url
                    print(f"Extracted FCH URL: {fch_url_for_row}")

                    driver.close()
                    driver.switch_to.window(original_window)
                    print("Closed new tab and switched back.")
                    time.sleep(0.5)

                except Exception as click_url_err:
                    print(f"Could not click FCH link or get URL for row {i+1}: {click_url_err}")
                    fch_url_for_row = ""
            else:
                print(f"No FCH <a> tag found in FCH column for row {i+1}.")
        else:
            if fch_column_index == -1:
                print(f"FCH column not found in headers for row {i+1}. FCH URL will be empty.")
            else:
                print(f"FCH column index out of bounds for cells in row {i+1}. FCH URL will be empty.")

        if fch_column_index != -1 and fch_column_index < len(row_data):
            row_data[fch_column_index] = fch_url_for_row
        else:
            row_data.append(fch_url_for_row)
        
        if any(row_data):
            all_rows_data.append(row_data)
        else:
            print(f"Skipping empty row {i+1} for DataFrame.")

    df = pd.DataFrame(all_rows_data, columns=column_names_for_df)

    print("\nDataFrame created successfully:")
    print(df.head())
    print(f"\nDataFrame shape: {df.shape}")

    try:
        csv_file_path = os.path.join(os.getcwd(), "timetable_data.csv")
        df.to_csv(csv_file_path, index=False)
        print(f"\nDataFrame saved to: {csv_file_path}")
    except Exception as csv_err:
        print(f"Error saving DataFrame to CSV: {csv_err}")

except Exception as e:
    print(f"An error occurred during the process: {e}")

input("Press Enter to quit...")
driver.quit()
