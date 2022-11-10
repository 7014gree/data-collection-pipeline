from selenium import webdriver
from selenium.webdriver.common.by import By
import time


driver = webdriver.Chrome()
url = "https://www.sainsburys.co.uk/"
driver.get(url)

homepage = driver.find_element(by=By.XPATH, value='//a[@data-label="Groceries"]')
link = homepage.get_attribute('href')
time.sleep(4)

accept_cookies_button = homepage.find_element(by=By.XPATH, value='//button[@id="onetrust-accept-btn-handler"]')
accept_cookies_button.click()
time.sleep(4)

driver.get(link)
grocery_categories = driver.find_elements(by=By.XPATH, value='//div[@class="mNavigationPropositionTile mNavigationBlock-desktop"]')
list_links = []
for category in grocery_categories:
    category_a_tag = category.find_element(by=By.XPATH, value='./a')
    link = category_a_tag.get_attribute('href')
    time.sleep(4)

    driver.get(link)
    product_grid = driver.find_element(by=By.XPATH, value='//div[@class="productLister_gridView"]')
    product_a_tags = product_grid.find_elements(by=By.XPATH, value = './/a')
    """for tag in product_a_tags:
        list_links.append(tag.get_attribute('href'))
"""
    break


print(list_links)
print(len(list_links))

while True:
    pass