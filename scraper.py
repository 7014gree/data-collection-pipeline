from datetime import datetime
from json import dump as json_dump
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from os import path as os_path
from os import mkdir as os_mkdir
from requests import get as requests_get
from time import sleep as time_sleep


class Scraper:
    def __init__(self, url: str):
        self.driver = webdriver.Chrome()
        self.driver.get(url)
        self.category_links = []
        self.product_links = []
        self.delay = 10
        self.cwd = os_path.dirname(os_path.realpath(__file__))

        self.raw_data_folder()
        self.accept_cookies()

    def raw_data_folder(self) -> None:
        try:
            assert os_path.exists(f"{self.cwd}/raw_data")
        except:
            os_mkdir(f"{self.cwd}/raw_data")

    def navigate_to_groceries(self) -> None:
        time_sleep(1)
        groceries_tag = self.driver.find_element(by=By.XPATH, value='//a[@data-label="Groceries"]')
        self.driver.get(groceries_tag.get_attribute('href'))
        time_sleep(1)

    def accept_cookies(self) -> None:
        try:
            WebDriverWait(self.driver, self.delay).until(EC.presence_of_element_located((By.XPATH, '//button[@id="onetrust-accept-btn-handler"]')))
            accept_cookies_button = self.driver.find_element(by=By.XPATH, value='//button[@id="onetrust-accept-btn-handler"]')
            accept_cookies_button.click()
        except TimeoutException:
            pass
        time_sleep(2)

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
        print(f"Scraping product information from: {self.category_links}.")
        time_sleep(2)

    def get_product_urls(self, category_link: str) -> None:
        self.driver.get(category_link)

        try:
            WebDriverWait(self.driver, self.delay).until(EC.presence_of_element_located((By.XPATH, '//ul[@class="productLister gridView"]')))
            while True:
                product_grid = self.driver.find_element(by=By.XPATH, value='//ul[@class="productLister gridView"]')
                product_div_tags = product_grid.find_elements(by=By.XPATH, value='.//div[@class="productInfo"]')
                for product_tag in product_div_tags:
                    product_link_tag = product_tag.find_element(by=By.XPATH, value='.//a')
                    self.product_links.append(product_link_tag.get_attribute('href'))
                time_sleep(1)

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

    def get_product_info(self, product_link: str) -> None:
        try:
            self.driver.get(product_link)
            timestamp = datetime.now().strftime("%d%m%Y_%H%M%S")
            

            WebDriverWait(self.driver, self.delay).until(EC.presence_of_element_located((By.XPATH, '//div[@class="ln-c-card pd-details ln-c-card--soft"]')))

            name = self.driver.find_element(by=By.XPATH, value='//h1[@class="pd__header"]').text
            short_desc = self.driver.find_element(by=By.XPATH, value='//div[@class="pd__description"]').text

            try:
                assert os_path.exists(f"{self.cwd}/raw_data/{name}")
            except:
                os_mkdir(f"{self.cwd}/raw_data/{name}")

            image_paths = self.download_images(name, timestamp)

            price_tag = self.driver.find_element(by=By.XPATH, value='//div[@class="pd__cost"]')
            price = price_tag.find_elements(by=By.XPATH, value='.//div')[1].text
            try:
                price_per_unit = price_tag.find_element(by=By.XPATH, value='.//*[@data-test-id="pd-unit-price"]').text
            except:
                offer_price_tag = self.driver.find_element(by=By.XPATH, value='//div[@data-test-id="pd-retail-price"]')
                offer_price_divs = offer_price_tag.find_element(by=By.XPATH, value='.//div')
                price = offer_price_divs[1].text
                price_per_unit = self.driver.find_element(by=By.XPATH, value='//div[@data-test-id=""pd-unit-price"]')

            try:
                long_desc = self.driver.find_element(by=By.XPATH, value='//div[@class="productText"]').text
            except:       
                try:
                    long_desc = self.driver.find_element(by=By.XPATH, value='//div[@class="memo"]').text
                except:
                    long_desc = "N/A"

            # Fills dictionary with 0g in case the category doesn't appear on the page
            nutritional_info_dict = {
                'unit': "N/A",
                'energy kJ': "N/A",
                'energy kcal': "N/A",
                'fat': "N/A",
                'saturates': "N/A",
                'carbohydrate': "N/A",
                'sugars': "N/A",
                'fibre': "N/A",
                'protein': "N/A",
                'salt': "N/A"
            }

            try:
                nutritional_info_table = self.driver.find_element(by=By.XPATH, value='//table[@class="nutritionTable"]')
                nutritional_table_rows = nutritional_info_table.find_elements(by=By.XPATH, value='.//tr')

                nutritional_info_dict['unit'] = nutritional_table_rows[0].find_elements(by=By.XPATH, value='.//th[@scope="col"]')[1].text
                nutritional_info_dict['energy kJ'] =  nutritional_table_rows[1].find_elements(by=By.XPATH, value='.//td')[0].text
                nutritional_info_dict['energy kcal'] = nutritional_table_rows[2].find_elements(by=By.XPATH, value='.//td')[0].text

                # Iterates through all of the row headings in the table and replaces the last element relevant key (set to N/A above upon matching
                for row in nutritional_table_rows[3:]:
                    row_name = str.lower(row.find_element(by=By.XPATH, value='.//th').text)
                    if row_name[:9] == "of which ":
                        row_name = row_name[9:]
                    try:
                        row_amount = row.find_element(by=By.XPATH, value='.//td').text
                        nutritional_info_dict[str.lower(row_name)] = row_amount
                    except:
                        pass
            except:
                pass

        except TimeoutException:
            print(f"Error retrieving product information for: {product_link}. Retrying in 1000 seconds...")
            for _ in range(100):
                print(f"{1000 - _ * 10} seconds remaining...")
                time_sleep(10)
            print("Retrying...")
            self.get_product_info(product_link)
        
        time_sleep(1)

        product_dict = {
            'name': name,
            'short desc': short_desc,
            'price': price,
            'price per unit': price_per_unit,
            'long desc': long_desc,
            'nutritional info': nutritional_info_dict,
            'url': product_link,
            'timestamp': timestamp,
            'image_path': image_paths
        }
        self.write_to_JSON(product_dict, name)


    def write_to_JSON(self, product_dict: dict, name: str) -> None:
        with open(f'{self.cwd}/raw_data/{name}/data.json', 'w') as data_file:
            json_dump(product_dict, data_file)


    def download_images(self, name: str, timestamp: str) -> str:
        folder_path = f"{self.cwd}/raw_data/{name}/images"
        try:
            assert os_path.exists(folder_path)
        except:
            os_mkdir(folder_path)

        try:
            image_paths = []

            # Originally only looked for @class='pd__image' but this did not work for all cases.
            # Now tries to catch the main exception and gives up otherwise.
            try:
                image_tags = self.driver.find_elements(by=By.XPATH, value='//img[@class="pd__image"]')
                assert image_tags != []
            except:
                image_tags = self.driver.find_elements(by=By.XPATH, value='//img[@class="pd__image pd__image__nocursor"]')
                
            for index, tag in enumerate(image_tags):
                image_src = tag.get_attribute('src')
                image_data = requests_get(image_src).content

                image_path = f'{folder_path}/{timestamp}_{index}.jpg'
                with open(image_path, 'wb') as handler:
                    handler.write(image_data)

                # Makes the slashes the same direction for dictionary/writing dictionary to JSON
                image_path = image_path.replace('\\','/')
                image_paths.append(image_path)
            return image_paths
        except:
            return "No images found."

if __name__ == "__main__":
    sainsburys_scraper = Scraper("https://www.sainsburys.co.uk/")
    sainsburys_scraper.navigate_to_groceries()
    sainsburys_scraper.get_category_urls()
    for category_link in sainsburys_scraper.category_links:
        sainsburys_scraper.get_product_urls(category_link)
    
    for product_link in sainsburys_scraper.product_links:
        sainsburys_scraper.get_product_info(product_link)



# To stop browser from closing once done
print("Scraping complete")
while True:
    pass