from datetime import datetime
from json import dump as json_dump
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import NoSuchElementException
from os import path as os_path
from os import mkdir as os_mkdir
from requests import get as requests_get
from time import sleep
from logging import error


class Scraper:

    """
    This class a web scraper used to extract data from https://www.sainsburys.co.uk

    Attributes:
        driver is the selenium webdriver used for navigating web pages.
        category_links contains a list of urls for categories to scrape.
        product_links is populated with urls scraped from each category link.
        delay is used throughout the class for WebDriverWait.
        cwd is the path for the current working directory, used for making/checking directories and writing files.

    Upon initialising an instance of the class, the following methods are called:
        make_raw_data_folder() checks that a folder exists to store product information, if not it makes one.
        accept_cookies() accepts cookies on the web page if they pop up
    """

    def __init__(self, url: str):
        self.__driver = webdriver.Chrome()
        self.__driver.get(url)
        self.delay = 10
        self.cwd = os_path.dirname(os_path.realpath(__file__))

        self.__make_raw_data_folder()
        self.__accept_cookies()

    def __make_raw_data_folder(self) -> None:
        """
        This function checks if a folder named "raw_data" already exists in the current working directory.
        It is called upon creating an instance of the Scraper class.
        If the folder already exists, the rest of the code executes as normal.
        If the folder does not already exist, the folder will be created.
        The "raw_data" folder is used to store the information retrieved by the scraper.        
        """
        try:
            assert os_path.exists(f"{self.cwd}/raw_data")
        except AssertionError:
            error("No raw data folder found, making new raw data folder.")
            os_mkdir(f"{self.cwd}/raw_data")

    def navigate_to_groceries(self) -> None:
        """
        This function navigates from https://www.sainsburys.co.uk to the Groceries section.
        """
        sleep(1)
        groceries_tag = self.__driver.find_element(by=By.XPATH, value='//a[@data-label="Groceries"]')
        self.__driver.get(groceries_tag.get_attribute('href'))
        sleep(1)

    def __accept_cookies(self) -> None:
        """
        This function clicks the accept cookies button once the element for the button has loaded.
        If the element does not load within 10 seconds, the script continues to run as normal.
        """
        try:
            WebDriverWait(self.__driver, self.delay).until(EC.presence_of_element_located((By.XPATH, '//button[@id="onetrust-accept-btn-handler"]')))
            accept_cookies_button = self.__driver.find_element(by=By.XPATH, value='//button[@id="onetrust-accept-btn-handler"]')
            accept_cookies_button.click()
        except TimeoutException:
            error("Cookie timeout error - either cookies took too long to load or have already been accepted.")
            pass
        sleep(2)

    def get_category_urls(self) -> list:
        """
        This function waits until the Groceries page has loaded, and then retrieves the urls for the categories of groceries.
        If the elements for the categories of groceries does not appear within 10 seconds the function attempts to navigate to the Groceries page.
        Then the function is called again, reloading the page.
        The function prints the urls from which product urls will be received.
        """

        category_links = []
        try:
            WebDriverWait(self.__driver, self.delay).until(EC.presence_of_element_located((By.XPATH, '//div[@class="mFourCols mNavigationProposionTileWrapper bottomMargin30"]')))
            category_tags = self.__driver.find_elements(by=By.XPATH, value='//div[@class="mNavigationPropositionTile mNavigationBlock-desktop"]')
            for category in category_tags:
                category_a_tag = category.find_element(by=By.XPATH, value='./a')
                category_links.append(category_a_tag.get_attribute('href'))
        except TimeoutException:
            print(f"Timeout error retrieving category urls. Refreshing page and retrying...")
            try:
                self.navigate_to_groceries()
            except:
                pass
            self.get_category_urls()
        print(f"Scraping product information from: {category_links}.")
        sleep(2)
        return category_links

    def get_product_urls(self, category_link: str) -> list:
        """
        This function first navigates to the first page for a grocery category.
        Then the function waits for the ul element containing html for products to be loaded.
        If the ul element is not loaded within 10 seconds, the function is called again, which reloads the page.
        The function then finds all div elements on the page which contain product information.
        Within each product div element, the a element is found and the url is retrieved from the a element.
        Once all product div elements have had a product url extracted, the link for the next page is found and navigated to.
        If a next page link cannot be found (i.e. all pages have been scraped) the function ends.

        Args:
            category_link (str): the url for the category page from which product page urls are to be extracted

        Returns:
            Nothing.
            Populates self.product_links with the product page urls retrieved.
        """

        product_links = []

        self.__driver.get(category_link)

        try:
            WebDriverWait(self.__driver, self.delay).until(EC.presence_of_element_located((By.XPATH, '//ul[@class="productLister gridView"]')))
            while True:
                product_grid = self.__driver.find_element(by=By.XPATH, value='//ul[@class="productLister gridView"]')
                product_div_tags = product_grid.find_elements(by=By.XPATH, value='.//div[@class="productInfo"]')
                for product_tag in product_div_tags:
                    product_link_tag = product_tag.find_element(by=By.XPATH, value='.//a')
                    product_links.append(product_link_tag.get_attribute('href'))
                sleep(1)

                try:
                    next_page_tag = self.__driver.find_element(by=By.XPATH, value='//li[@class="next"]')
                    next_page_url = next_page_tag.find_element(by=By.XPATH, value='.//a').get_attribute('href')
                    product_links.extend(self.get_product_urls(next_page_url))
                # Stop when can no longer find a tag for next page
                except NoSuchElementException:
                    break
        except TimeoutException:
            print(f"Timeout error retrieving product urls from: {category_link}. Refreshing page and retrying...")
            self.get_product_urls(category_link)

        return product_links

    def get_product_info(self, product_link: str) -> None:
        """
        This function retrieves all product information from a product page and puts the information in a dictionary.
        Then it calls a function write the dictionary to a JSON file.
        If the page is not loaded within 10 seconds, the function will wait 1000 seconds before calling itself, which reloads the page.
        The function checks whether or not a folder exists with cwd/raw_data for the current product name. If not, the folder is created.
        The function calls download_images to save any extracted images as jpg files within the cwd/raw_data/name/images folder.

        Args:
            product_link (str): the url for the product page to retrieve information from

        Returns:
            Nothing.
            Retrieves information, enters information into a dictionary, calls methods to download images and write the dictionary to JSON.
        """
        try:
            self.__driver.get(product_link)
            # Gets timestamp in required format for timestamp in dictionary and name of image file.
            timestamp = datetime.now().strftime("%d%m%Y_%H%M%S")
            
            # Waits until page is loaded up to long description/nutrtional table.
            WebDriverWait(self.__driver, self.delay).until(EC.presence_of_element_located((By.XPATH, '//div[@class="ln-c-card pd-details ln-c-card--soft"]')))

            name = self.__driver.find_element(by=By.XPATH, value='//h1[@class="pd__header"]').text
            short_desc = self.__driver.find_element(by=By.XPATH, value='//div[@class="pd__description"]').text

            # Ensures that a folder exists to store the JSON file and images/
            folder_path = f"{self.cwd}/raw_data/{name}"
            try:
                assert os_path.exists(folder_path)
            except AssertionError:
                os_mkdir(folder_path)

            image_paths = self.__download_images(folder_path, timestamp)

            price_tag = self.__driver.find_element(by=By.XPATH, value='//div[@class="pd__cost"]')
            price = price_tag.find_elements(by=By.XPATH, value='.//div')[1].text

            # Catches cases where an item is on sale and hence the tags used are slightly different.
            try:
                price_per_unit = price_tag.find_element(by=By.XPATH, value='.//*[@data-test-id="pd-unit-price"]').text
            except NoSuchElementException:
                error(f"For url {product_link}: unable to find price per unit at default location, assuming item is on sale and re-entering price and price per unit.")
                offer_price_tag = self.__driver.find_element(by=By.XPATH, value='//div[@data-test-id="pd-retail-price"]')
                offer_price_divs = offer_price_tag.find_element(by=By.XPATH, value='.//div')
                price = offer_price_divs[1].text
                price_per_unit = self.__driver.find_element(by=By.XPATH, value='//div[@data-test-id=""pd-unit-price"]')

            # Catches cases where a long description uses a slightly different tag or just doesn't exist
            try:
                long_desc = self.__driver.find_element(by=By.XPATH, value='//div[@class="productText"]').text
            except NoSuchElementException:
                error(f"For url {product_link}: unable to find long description at default location, trying for class = memo.")      
                try:
                    long_desc = self.__driver.find_element(by=By.XPATH, value='//div[@class="memo"]').text
                except NoSuchElementException:
                    error(f"For url {product_link}: unable to find long description, dictionary populated with 'N/A'.")
                    long_desc = "N/A"

            # Fills dictionary with N/A in case the category doesn't appear on the page
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

            # If there is a nutritional information table on the page, this tries to retrieve the data from the first column.
            # If there isn't a table, passes and the values remain as N/A.
            try:
                nutritional_info_table = self.__driver.find_element(by=By.XPATH, value='//table[@class="nutritionTable"]')
                nutritional_table_rows = nutritional_info_table.find_elements(by=By.XPATH, value='.//tr')

                nutritional_info_dict['unit'] = nutritional_table_rows[0].find_elements(by=By.XPATH, value='.//th[@scope="col"]')[1].text
                nutritional_info_dict['energy kJ'] =  nutritional_table_rows[1].find_elements(by=By.XPATH, value='.//td')[0].text
                nutritional_info_dict['energy kcal'] = nutritional_table_rows[2].find_elements(by=By.XPATH, value='.//td')[0].text

                # Iterates through all of the row headings.
                # Where the heading matches as key in nutritional_info dict, it replaces N/A as the value.
                # If the heading is not found as a key in nutrional_info_dict, it is removed due to it being a rare outlier.
                # If a key is never found, it remains as N/A.
                # This covers pulling the information which is on the vast majority of pages, excluding the odd outlier to avoid having N/A in most dictionaries.
                for row in nutritional_table_rows[3:]:
                    row_name = str.lower(row.find_element(by=By.XPATH, value='.//th').text)
                    if row_name[:9] == "of which ":
                        row_name = row_name[9:]
                    try:
                        row_amount = row.find_element(by=By.XPATH, value='.//td').text
                        nutritional_info_dict[row_name] = row_amount
                    except NoSuchElementException:
                        error(f"For url {product_link}: '{row_name}' not in nutritional information dictionary. Information discarded.")
            except NoSuchElementException:
                error(f"For url {product_link}: no nutritional information found. Dictionary populated with 'N/A'.")

        # If no inforamtion has loaded, tries again in 1,000 seconds.
        # Prints to console in case it starts looping indefinitely and user wants to stop the script.
        # Prints status of timer every 10 seconds.
        except TimeoutException:
            print(f"Error retrieving product information for: {product_link}. Retrying in 1000 seconds...")
            for _ in range(100):
                print(f"{1000 - _ * 10} seconds remaining...")
                sleep(10)
            print("Retrying...")
            self.get_product_info(product_link)
        
        sleep(1)

        product_dict = {
            'name': name,
            'short desc': short_desc,
            'price': price,
            'price per unit': price_per_unit,
            'long desc': long_desc,
            'nutritional info': nutritional_info_dict,
            'url': product_link,
            'timestamp': timestamp,
            'image paths': image_paths
        }

        return product_dict

    @staticmethod
    def write_to_JSON(cwd: str, product_dict: dict) -> None:
        """
        Writes a dictionary to a JSON file.
        Called by get_product_info to write the dictionaries to a JSON file.

        Args:
            cwd (str): a string for the current working directory
            product-dict (dict): a dictionary containing product information
            name (str): the name of the product, equivalent to product_dict['name']

        Returns:
            Nothing.
            Writes dictionary to JSON file.
        """
        with open(f'{cwd}/raw_data/{product_dict["name"]}/data.json', 'w') as data_file:
            json_dump(product_dict, data_file)

    def __download_images(self, folder_path: str, timestamp: str) -> list:
        """
        Ensures that a folder to store images exists.
        Downloads product images from a page to the images folder and returns a list of the file paths they are saved to.

        Args:
            folder_path (str): the path where the product information is to be stored, containing an images folder to save downloaded images to
            timestamp (str): the formatted timestamp for when the web page was accessed, used to construct the title for the image

        Returns:
            image_paths (list): a list containing the file paths for each image as strings
        """
        image_folder_path = f"{folder_path}/images"
        try:
            assert os_path.exists(image_folder_path)
        except AssertionError:
            os_mkdir(image_folder_path)

        try:
            image_paths = []

            # Originally only looked for @class='pd__image' but this did not work for all cases.
            # Now tries to catch the main exception and gives up otherwise.
            try:
                image_tags = self.__driver.find_elements(by=By.XPATH, value='//img[@class="pd__image"]')
                assert image_tags != []
            except AssertionError:
                error(f"No image tags found with default class attribute in {folder_path}, retrying with alternative attribute.")
                image_tags = self.__driver.find_elements(by=By.XPATH, value='//img[@class="pd__image pd__image__nocursor"]')

            # enumerate used to keep track of the image number.    
            for index, tag in enumerate(image_tags):
                image_src = tag.get_attribute('src')
                image_data = requests_get(image_src).content

                # File name format <date>_<time>_<image_number_from_page>.jpg
                image_path = f'{image_folder_path}/{timestamp}_{index}.jpg'
                with open(image_path, 'wb') as handler:
                    handler.write(image_data)

                # Makes the slashes the same direction for dictionary/writing dictionary to JSON
                image_path = image_path.replace('\\','/')
                image_paths.append(image_path)
            return image_paths
        except:
            error(f"No images found for folder path {folder_path}.")
            return ["No images found."]

if __name__ == "__main__":
    sainsburys_scraper = Scraper("https://www.sainsburys.co.uk/")
    cwd = sainsburys_scraper.cwd

    sainsburys_scraper.navigate_to_groceries()
    #category_urls = sainsburys_scraper.get_category_urls()
    product_links = []

    #for category_link in category_urls:
    product_links = sainsburys_scraper.get_product_urls('https://www.sainsburys.co.uk/shop/gb/groceries/fruit-veg/fruitandveg-essentials')
    
    for product_url in product_links:
        product_data = sainsburys_scraper.get_product_info(product_url)
        sainsburys_scraper.write_to_JSON(cwd, product_data)

    # To stop browser from closing once done
    print("Scraping complete")
    while True:
        pass