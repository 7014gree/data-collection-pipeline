from selenium import webdriver
from selenium.webdriver.common.by import By
import time


driver = webdriver.Chrome()
url = "https://www.sainsburys.co.uk/"
driver.get(url)

a = driver.find_element(by=By.XPATH, value='//a[@data-label="Groceries"]')
link = a.get_attribute('href')
time.sleep(4)

driver.get(link)
