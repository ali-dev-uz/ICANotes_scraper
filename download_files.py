import os
import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import psycopg2
import re

db_config = {
    'dbname': 'postgres',
    'user': 'postgres',
    'password': 'akow4230',
    'host': 'localhost',
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


def extract_url(html_snippet):
    start = html_snippet.find("href='") + len("href='")
    end = html_snippet.find("'", start)
    return html_snippet[start:end].replace('&amp;', '&')


def handle_form_redirect(response, session):
    soup = BeautifulSoup(response.text, 'html.parser')
    form = soup.find('form')
    if form:
        action = form['action']
        inputs = form.find_all('input')
        data = {input['name']: input['value'] for input in inputs if input['type'] != 'submit'}
        return session.post(action, data=data)
    return response


def save_file(file_url, file_name, folder_id, session):
    file_name = re.sub(r'/', '.', file_name)
    print(file_name)
    file_url = "https://upload.icanotes.com" + file_url
    directory = str(folder_id)  # Use the user_id as directory name

    os.makedirs(directory, exist_ok=True)

    try:
        response = session.get(file_url)
        if response.status_code == 200:
            if "form" in response.text.lower():
                response = handle_form_redirect(response, session)

            content_type = response.headers.get('Content-Type')
            content_length = response.headers.get('Content-Length')
            print(f"Content Type: {content_type}, Content Length: {content_length}")

            if content_type == 'application/pdf':
                with open(os.path.join(directory, file_name), 'wb') as file:
                    file.write(response.content)
                return True
            else:
                print(f"Unexpected content type: {content_type}")
        else:
            print(f"Failed to download from URL: {file_url}. Status code: {response.status_code}")
    except Exception as e:
        print(f"Error downloading file: {e}")

    return False


def delete_file_record(user_id, url):
    conn = None
    try:
        conn = psycopg2.connect(**db_config)
        cur = conn.cursor()
        cur.execute("DELETE FROM files_data WHERE user_id = %s AND url = %s", (user_id, url))
        conn.commit()
        cur.close()
    except Exception as e:
        print(f"Error deleting file record: {e}")
    finally:
        if conn is not None:
            conn.close()


def fetch_files_data(user_id):
    conn = None
    files_data = []
    try:
        conn = psycopg2.connect(**db_config)
        cur = conn.cursor()
        cur.execute("SELECT url, file_name FROM files_data WHERE user_id = %s", (user_id,))
        files_data = cur.fetchall()
        cur.close()
    except Exception as e:
        print(f"Error fetching files data: {e}")
    finally:
        if conn is not None:
            conn.close()
    return files_data


def main():
    user_id = '1025812'

    # Setup Selenium for login
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chromedriver_path = "./Chrone/chromedriver.exe"
    driver = webdriver.Chrome(service=Service(chromedriver_path), options=chrome_options)
    login_url = 'https://upload.icanotes.com/idp/account/signin'
    username_str = 'clhbotgarrison'
    password_str = 'Bot@4805$CLH$'

    driver.get(login_url)

    try:
        username = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, 'UserName')))
        password = driver.find_element(By.NAME, 'Password')
        username.send_keys(username_str)
        password.send_keys(password_str)
        password.send_keys(Keys.RETURN)
        WebDriverWait(driver, 10).until(EC.url_changes(login_url))
    except Exception as e:
        print(f'Error during login: {e}')
        driver.quit()
        return

    if driver.current_url != login_url:
        print('Login successful.')
    else:
        print('Failed to log in or incorrect URL.')
        driver.quit()
        return

    cookies = driver.get_cookies()
    session = requests.Session()
    for cookie in cookies:
        session.cookies.set(cookie['name'], cookie['value'])

    files_data = fetch_files_data(user_id)
    count = 0
    for url, file_name in files_data:
        if save_file(url, str(count)+file_name+".pdf", user_id, session):
            count += 1
            # delete_file_record(user_id, url)

    driver.quit()


if __name__ == "__main__":
    main()
