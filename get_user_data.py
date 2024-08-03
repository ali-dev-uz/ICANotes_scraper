import psycopg2
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time
from colorama import Fore
from config import WEBSITE_LOGIN, WEBSITE_PASSWORD, DB_USER, DB_PASS, DB_NAME, DB_HOST, CHROMEDRIVER_PATH

from intro import _start_script, _end_script

db_config = {
    'dbname': DB_NAME,
    'user': DB_USER,
    'password': DB_PASS,
    'host': DB_HOST,
    'port': 5432
}

def create_table():
    conn = None
    try:
        conn = psycopg2.connect(**db_config)
        cur = conn.cursor()
        cur.execute('''
            CREATE TABLE IF NOT EXISTS files_data (
                user_id VARCHAR(255),
                url VARCHAR(255) UNIQUE,
                file_name TEXT
            );
        ''')
        conn.commit()
        cur.close()
    except Exception as e:
        print(f"Error creating table: {e}")
    finally:
        if conn is not None:
            conn.close()

def insert_file_data(user_id, url, file_name):
    conn = None
    try:
        conn = psycopg2.connect(**db_config)
        cur = conn.cursor()
        cur.execute('''
            INSERT INTO files_data (user_id, url, file_name) VALUES (%s, %s, %s)
        ''', (user_id, url, file_name))
        conn.commit()
        cur.close()
    except Exception as e:
        print(f"Error inserting data: {e}")
    finally:
        if conn is not None:
            conn.close()

def find_items_with_badge_greater_than_zero(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    ul_no_padding = soup.find('ul', class_='ulNoPadding')
    items_with_badge_gt_zero = []
    for li in ul_no_padding.find_all('li', class_='squareBorder list-group-item pointer'):
        badge_span = li.find('span', class_='badge')
        if badge_span:
            badge_value = int(badge_span.text.strip())
            if badge_value > 0:
                items_with_badge_gt_zero.append(li)

    return items_with_badge_gt_zero


def save_items_to_file(items, file_path):
    with open(file_path, 'w', encoding='utf-8') as file:
        for item in items:
            file.write(str(item) + '\n')


def click_li(driver, items, dir_name, folder_id):
    for item in items:
        item_id = item.find('span', class_='badge').text.strip()
        li_element = driver.find_element(By.XPATH, f"//li[.//span[text()='{item_id}']]")
        li_element.click()
        time.sleep(5)

        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')

        a_tags = soup.find_all('a', class_='glyphicon glyphicon-download-alt pointer')
        results = []
        print("files started download")
        for a_tag in a_tags:
            href = a_tag.get('href')
            parent_div = a_tag.find_parent('div')
            strong_tag = parent_div.find('strong')
            if strong_tag:
                strong_text = strong_tag.text.strip()
                result = {
                    'strong_element_text': strong_text,
                    'a_element_href': href
                }
                insert_file_data(dir_name, href, strong_text)
                time.sleep(0.0001)
    return results


def main_function(item, folder_id):
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    driver = webdriver.Chrome(service=Service(CHROMEDRIVER_PATH), options=chrome_options)
    login_url = 'https://upload.icanotes.com/idp/account/signin'

    # Open the login page
    driver.get(login_url)

    # Fill in the login form
    try:
        username = driver.find_element(By.NAME, 'UserName')
        password = driver.find_element(By.NAME, 'Password')
        username.send_keys(WEBSITE_LOGIN)
        password.send_keys(WEBSITE_PASSWORD)
        password.send_keys(Keys.RETURN)  # Submit the form
        WebDriverWait(driver, 30).until(
            EC.url_changes(login_url)
        )
    except Exception as e:
        driver.quit()
        print(f'Error during login: {e}')
        exit()

    # Check if login was successful
    if driver.current_url != login_url:
        driver.get('https://upload.icanotes.com/')
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.TAG_NAME, 'html'))
        )
        input_field = driver.find_element(By.CSS_SELECTOR, 'input[placeholder="Name or ID"]')
        input_field.send_keys(str(item))
        checkbox = driver.find_element(By.CSS_SELECTOR, 'input[type="checkbox"]')
        if not checkbox.is_selected():
            checkbox.click()
        search_button = driver.find_element(By.CSS_SELECTOR, 'input[type="button"][value="Search"]')
        search_button.click()
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'list-group-item'))
        )
        time.sleep(5)
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')
        pretty_html = soup.prettify()
        with open("page_content.html", "w", encoding="utf-8") as file:
            file.write(pretty_html)

        a_tag = driver.find_element(By.XPATH, f"//a[.//div[contains(text(), '{item}')]]")

        if a_tag:
            a_tag.click()
            time.sleep(10)
            page_source_after_click = driver.page_source
            soup_after_click = BeautifulSoup(page_source_after_click, 'html.parser')
            pretty_html_after_click = soup_after_click.prettify()
            items = find_items_with_badge_greater_than_zero(pretty_html_after_click)
            return click_li(driver, items, item, folder_id)
        else:
            print('Target link not found')
    else:
        print('Failed to log in or incorrect URL.')

    driver.quit()

# Main script
items_list = [1025812]
google_drive_folder_id = ['16u7kgN6R2Tv6aRfHTvd0swm0mWuTTNBdv']
create_table()
for item, folder_ids in zip(items_list, google_drive_folder_id):
    _start_script()
    print(Fore.LIGHTYELLOW_EX + f"Patient ID: {item}" + Fore.WHITE)
    urls = main_function(item, folder_ids)
    print(urls)
    _end_script()
