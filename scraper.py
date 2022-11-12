from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
import requests
import time

class Scraper:
    def __init__(self, url: str):
        self.driver = webdriver.Chrome()
        self.driver.get(url)
        self.category_links = []
        self.product_links = []
        self.product_information = self.new_product_info_dict()
        self.delay = 10
        self.image_downloaded = False

        self.accept_cookies()

    def navigate_to_groceries(self):
        time.sleep(5)

        groceries_tag = self.driver.find_element(by=By.XPATH, value='//a[@data-label="Groceries"]')
        self.driver.get(groceries_tag.get_attribute('href'))

        time.sleep(4)

    def accept_cookies(self):
        try:
            WebDriverWait(self.driver, self.delay).until(EC.presence_of_element_located((By.XPATH, '//button[@id="onetrust-accept-btn-handler"]')))
            accept_cookies_button = self.driver.find_element(by=By.XPATH, value='//button[@id="onetrust-accept-btn-handler"]')
            accept_cookies_button.click()
        except TimeoutException:
            pass
        time.sleep(2)

    def new_product_info_dict(self) -> dict:
        return {'name': [], 'short desc': [], 'price': [], 'price per unit': [], 'long desc': [], 'nutritional info': {'unit': [],
'energy kJ': [], 'energy kcal': [], 'fat': [], 'saturates': [], 'carbohydrate': [], 'sugars': [], 'fibre': [], 'protein': [], 'salt': []}, 'url': []}

    def get_category_urls(self):
        try:
            WebDriverWait(self.driver, self.delay).until(EC.presence_of_element_located((By.XPATH, '//div[@class="mFourCols mNavigationProposionTileWrapper bottomMargin30"]')))
            category_tags = self.driver.find_elements(by=By.XPATH, value='//div[@class="mNavigationPropositionTile mNavigationBlock-desktop"]')
            for category in category_tags:
                category_a_tag = category.find_element(by=By.XPATH, value='./a')
                self.category_links.append(category_a_tag.get_attribute('href'))
        except TimeoutException:
            print(f"Error retrieving category urls. Retrying...")
            self.get_category_urls()
        print(self.category_links)
        time.sleep(2)

    def get_product_urls(self, category_link):
        self.driver.get(category_link)

        try:
            WebDriverWait(self.driver, self.delay).until(EC.presence_of_element_located((By.XPATH, '//ul[@class="productLister gridView"]')))
            while True:
                product_grid = self.driver.find_element(by=By.XPATH, value='//ul[@class="productLister gridView"]')
                product_div_tags = product_grid.find_elements(by=By.XPATH, value='.//div[@class="productInfo"]')
                for product_tag in product_div_tags:
                    product_link_tag = product_tag.find_element(by=By.XPATH, value='.//a')
                    self.product_links.append(product_link_tag.get_attribute('href'))
                time.sleep(1)

                try:
                    next_page_tag = self.driver.find_element(by=By.XPATH, value='//li[@class="next"]')
                    next_page_url = next_page_tag.find_element(by=By.XPATH, value='.//a').get_attribute('href')
                    self.get_product_urls(next_page_url) 
                # Stop when can no longer find a tag for next page
                except:
                    break
        except:
            print(f"Timeout error retrieving product urls from: {category_link}. Retrying...")
            self.get_product_urls(category_link)

    def get_product_info(self, product_link):
        self.product_information['url'].append(product_link)
        print(product_link)
        try:
            self.driver.get(product_link)
            WebDriverWait(self.driver, self.delay).until(EC.presence_of_element_located((By.XPATH, '//div[@class="ln-c-card pd-details ln-c-card--soft"]')))

            name = self.driver.find_element(by=By.XPATH, value='//h1[@class="pd__header"]').text
            self.product_information['name'].append(name)
            self.product_information['short desc'].append(self.driver.find_element(by=By.XPATH, value='//div[@class="pd__description"]').text)

            if self.image_downloaded == False:
                image_tag = self.driver.find_element(by=By.XPATH, value='//img[@class="pd-image"]')
                image_url = image_tag.get_attribute('href')
                self.download_image(image_url, name)
                self.image_downloaded = True

            
            price_tag = self.driver.find_element(by=By.XPATH, value='//div[@class="pd__cost"]')
            self.product_information['price'].append(price_tag.find_elements(by=By.XPATH, value='.//div')[1].text)
            try:
                self.product_information['price per unit'].append(price_tag.find_element(by=By.XPATH, value='.//*[@data-test-id="pd-unit-price"]').text)
            except:
                offer_price_tag = self.driver.find_element(by=By.XPATH, value='//div[@data-test-id="pd-retail-price"]')
                offer_price_divs = offer_price_tag.find_element(by=By.XPATH, value='.//div')
                self.product_information['price'].append(offer_price_divs[1].text)
                self.product_information['price per unit'].append(self.driver.find_element(by=By.XPATH, value='//div[@data-test-id=""pd-unit-price"]'))

            try:
                self.product_information['long desc'].append(self.driver.find_element(by=By.XPATH, value='//div[@class="productText"]').text)
            except:       
                try:
                    self.product_information['long desc'].append(self.driver.find_element(by=By.XPATH, value='//div[@class="memo"]').text)
                except:
                    self.product_information['long desc'].append(["N/A"])

            # Fills dictionary with 0g in case the category doesn't appear on the page
            self.product_information['nutritional info']['unit'].append("N/A")
            self.product_information['nutritional info']['energy kJ'].append("N/A")
            self.product_information['nutritional info']['energy kcal'].append("N/A")
            self.product_information['nutritional info']['fat'].append("N/A")
            self.product_information['nutritional info']['saturates'].append("N/A")
            self.product_information['nutritional info']['carbohydrate'].append("N/A")
            self.product_information['nutritional info']['sugars'].append("N/A")
            self.product_information['nutritional info']['fibre'].append("N/A")
            self.product_information['nutritional info']['protein'].append("N/A")
            self.product_information['nutritional info']['salt'].append("N/A")

            try:
                nutritional_info_table = self.driver.find_element(by=By.XPATH, value='//table[@class="nutritionTable"]')
                nutritional_table_rows = nutritional_info_table.find_elements(by=By.XPATH, value='.//tr')

                self.product_information['nutritional info']['unit'][-1] = nutritional_table_rows[0].find_elements(by=By.XPATH, value='.//th[@scope="col"]')[1].text
                self.product_information['nutritional info']['energy kJ'][-1] =  nutritional_table_rows[1].find_elements(by=By.XPATH, value='.//td')[0].text
                self.product_information['nutritional info']['energy kcal'][-1] = nutritional_table_rows[2].find_elements(by=By.XPATH, value='.//td')[0].text

                # Iterates through all of the row headings in the table and replaces the last element relevant key (set to N/A above upon matching
                for row in nutritional_table_rows[3:]:
                    row_name = str.lower(row.find_element(by=By.XPATH, value='.//th').text)
                    if row_name[:9] == "of which ":
                        row_name = row_name[9:]
                    try:
                        row_amount = row.find_element(by=By.XPATH, value='.//td').text
                        self.product_information['nutritional info'][str.lower(row_name)][-1] = row_amount
                    except:
                        pass
            except:
                pass
        except TimeoutException:
            print(f"Error retrieving product information for: {product_link}. Retrying in 1000 seconds...")
            for _ in range(100):
                print(f"{1000 - _ * 10} seconds remaining...")
                time.sleep(10)
            print("Retrying...")
            self.get_product_info(product_link)
        
        time.sleep(1)        
        print(self.product_information)

    @staticmethod
    def download_image(image_url, name):
        image_data = requests.get(image_url).content
        with open(f'{name}.jpg', 'wb') as handler:
            handler.write(image_data)




if __name__ == "__main__":
    sainsburys_scraper = Scraper("https://www.sainsburys.co.uk/")
    sainsburys_scraper.navigate_to_groceries()
    sainsburys_scraper.get_category_urls()
    for category_link in sainsburys_scraper.category_links:
        sainsburys_scraper.get_product_urls(category_link)

    for product_link in sainsburys_scraper.product_links:
        sainsburys_scraper.get_product_info(product_link)

    # Scraper.download_image("https://assets.sainsburys-groceries.co.uk/gol/1196757/1/640x640.jpg", "banana")

"""
while True:
    pass"""