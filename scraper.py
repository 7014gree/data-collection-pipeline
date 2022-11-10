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

grocery_category_links = []
grocery_categories = driver.find_elements(by=By.XPATH, value='//div[@class="mNavigationPropositionTile mNavigationBlock-desktop"]')
for category in grocery_categories:
    category_a_tag = category.find_element(by=By.XPATH, value='./a')
    grocery_category_links.append(category_a_tag.get_attribute('href'))

print(grocery_category_links)

list_links = []
product_dict = {'name': [], 'short desc': [], 'price': [], 'price per unit': [], 'long desc': [], 'nutritional info': {'unit': [],
'energy kJ': [], 'energy kcal': [], 'fat': [], 'saturates': [], 'carbohydrate': [], 'sugars': [], 'fibre': [], 'protein': [], 'salt': []}, 'url': []}

for grocery_category_link in grocery_category_links:
    time.sleep(5)
    driver.get(grocery_category_link)
    time.sleep(5)

    while True:
        product_grid = driver.find_element(by=By.XPATH, value='//ul[@class="productLister gridView"]')
        product_div_tags = product_grid.find_elements(by=By.XPATH, value='.//div[@class="productInfo"]')
        for product_tag in product_div_tags:
            product_link_tag = product_tag.find_element(by=By.XPATH, value='.//a')
            list_links.append(product_link_tag.get_attribute('href'))

        try:
            next_page_tag = driver.find_element(by=By.XPATH, value='//li[@class="next"]')
            time.sleep(5)
            next_page_tag.click()
            time.sleep(10)
        
        # Stop when can no longer find a tag for 
        except:
            break



for url in list_links:
    product_dict['url'].append(url)
    print(url)
    time.sleep(4)
    driver.get(url)
    time.sleep(20)
    product_dict['name'].append(driver.find_element(by=By.XPATH, value='//h1[@class="pd__header"]').text)
    product_dict['short desc'].append(driver.find_element(by=By.XPATH, value='//div[@class="pd__description"]').text)

    price_tag = driver.find_element(by=By.XPATH, value='//div[@class="pd__cost"]')
    product_dict['price'].append(price_tag.find_elements(by=By.XPATH, value='.//div')[1].text)
    product_dict['price per unit'].append(price_tag.find_element(by=By.XPATH, value='.//span[@data-test-id="pd-unit-price"]').text)

    product_dict['long desc'].append(driver.find_element(by=By.XPATH, value='//div[@class="productText"]').text)

    # Fills dictionary with 0g in case the category doesn't appear on the page
    product_dict['nutritional info']['unit'].append("N/A")
    product_dict['nutritional info']['energy kJ'].append("N/A")
    product_dict['nutritional info']['energy kcal'].append("N/A")
    product_dict['nutritional info']['fat'].append("N/A")
    product_dict['nutritional info']['saturates'].append("N/A")
    product_dict['nutritional info']['carbohydrate'].append("N/A")
    product_dict['nutritional info']['sugars'].append("N/A")
    product_dict['nutritional info']['fibre'].append("N/A")
    product_dict['nutritional info']['protein'].append("N/A")
    product_dict['nutritional info']['salt'].append("N/A")

    try:
        nutritional_info_table = driver.find_element(by=By.XPATH, value='//table[@class="nutritionTable"]')
        nutritional_table_rows = nutritional_info_table.find_elements(by=By.XPATH, value='.//tr')
        
        product_dict['nutritional info']['unit'][-1] = nutritional_table_rows[0].find_elements(by=By.XPATH, value='.//th[@scope="col"]')[1].text
        product_dict['nutritional info']['energy kJ'][-1] =  nutritional_table_rows[1].find_elements(by=By.XPATH, value='.//td')[0].text
        product_dict['nutritional info']['energy kcal'][-1] = nutritional_table_rows[2].find_elements(by=By.XPATH, value='.//td')[0].text
        
        # Fills dictionary with 0g in case the category doesn't appear on the page
        product_dict['nutritional info']['fat'].append("N/A")
        product_dict['nutritional info']['saturates'].append("N/A")
        product_dict['nutritional info']['carbohydrate'].append("N/A")
        product_dict['nutritional info']['sugars'].append("N/A")
        product_dict['nutritional info']['fibre'].append("N/A")
        product_dict['nutritional info']['protein'].append("N/A")
        product_dict['nutritional info']['salt'].append("N/A")


        # Iterates through all of the row headings in the table and replaces the last element relevant key (set to N/A above upon matching
        for row in nutritional_table_rows[3:]:
            row_name = str.lower(row.find_element(by=By.XPATH, value='.//th').text)
            row_amount = row.find_element(by=By.XPATH, value='.//td').text
            product_dict['nutritional info'][row_name][-1] = row_amount
    
    except:
        pass

    print(product_dict)

    
print(product_dict)



while True:
    pass