import time
import logging
import datetime
import json
from faker import Faker
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException, TimeoutException, WebDriverException
import boto3

s3 = boto3.client('s3')
bucket = 'scraped-sites-coding-test'

#This part make logging work locally when testing and in lambda cloud watch
if logging.getLogger().hasHandlers():
    logging.getLogger().setLevel(logging.INFO)
else:
    logging.basicConfig(level=logging.INFO)

def get_driver():
    fake_user_agent = Faker()
    options = Options()

    options.binary_location = '/opt/chrome/chrome'
    options.add_experimental_option("excludeSwitches", ['enable-automation'])
    options.add_argument('--disable-infobars')
    options.add_argument('--disable-extensions')
    options.add_argument('--no-first-run')
    options.add_argument('--headless')
    options.add_argument('--disable-client-side-phishing-detection')
    options.add_argument('--allow-running-insecure-content')
    options.add_argument('--disable-web-security')
    options.add_argument('--user-agent=' + fake_user_agent.user_agent()) 
    options.add_argument('--ignore-certificate-errors') 
    options.add_argument('--no-sandbox')
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1280x1696")
    options.add_argument("--single-process")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-dev-tools")
    options.add_argument("--no-zygote")
    options.add_argument("--remote-debugging-port=9222")
    # add more options as necessary

    driver = webdriver.Chrome(
        service=ChromeService('/opt/chromedriver'),
        options=options
    )

    return driver

def remove_element(driver, selector):
    try:
        element = driver.find_element(By.CSS_SELECTOR, selector)
        driver.execute_script("arguments[0].remove", element)
    except NoSuchElementException:
        logging.info(f"There is no {selector} in the page")

def lambda_handler(event, context):
    print(event)
    try:
        # each lambda only scrapes a single URL
        url = event['Records'][0]['body']

        driver = get_driver()
        driver.get(url)

        # let the page load a bit
        time.sleep(3)

        # scrape the text on the page
        html_body = driver.find_element(By.TAG_NAME, 'body')
        text = html_body.text

        # remove the unnecessary components, such as header and footer
        # note that since these components may be implemented in numerous ways,
        # we use various CSS selectors. The code may be modified to use XPath
        # instead for a more complex element finding
        to_remove = ['header', 'footer', 'nav', '.navbar']
        for selector in to_remove:
            remove_element(driver, selector)
        
        # scrape the body of the text on the page
        new_body = driver.find_element(By.TAG_NAME, 'body')
        body = new_body.text

        # scrape the list of the links on the page, including the text on the link
        anchor_tags = driver.find_elements(By.CSS_SELECTOR, 'a')
        links = [ (anchor.get_attribute('href'), anchor.text) for anchor in anchor_tags ]

        # may not be necessary
        driver.close()

        res = {
                "url": url,
                "text": text,
                "body": body,
                "links": links
            }
        
        filename = f'{url}-{str(datetime.datetime.now())}.json'
        uploadByteStream = bytes(json.dumps(res).encode('utf-8'))
        s3.put_object(Bucket=bucket, Key=filename, Body=uploadByteStream)

        return {
            "status": 200,
            "filename": filename,
            "data": res
        }
    
    except TimeoutException:
        logging.error('Request Time Out')
        driver.close()
        return {
            "status": 500
        }
    except WebDriverException:
        logging.error('------------------------ WebDriver-Error! ---------------------', exc_info=True)
        logging.error('------------------------ WebDriver-Error! END ----------------')
        driver.close()
        return {
            "status": 500
        }
    except Exception:
        logging.error('------------------------ Exception-Error! -----------------', exc_info=True)
        logging.error('------------------------ Exception-Error! END -------------')
        driver.close()
        return {
            "status": 500
        }