from scraper import Scraper
from os import path
from os import mkdir
from time import sleep
from json import load
import unittest

class ScraperTestCase(unittest.TestCase):
    def setUp(self):
        self.test_scraper = Scraper()

    def test_navigate_to_groceries(self):
        self.test_scraper.navigate_to_groceries()
        sleep(2)
        current_url = self.test_scraper._driver.current_url
        expected_url = "https://www.sainsburys.co.uk/webapp/wcs/stores/servlet/gb/groceries"
        message = f"current_url: {current_url}"
        self.assertIn(expected_url, current_url, message)

    def test_get_category_urls(self):
        category_urls = self.test_scraper.get_category_urls()
        self.assertIsInstance(category_urls[0], str, f"Number of category urls = {len(category_urls)}, {category_urls}")

    def test_get_product_urls(self):
        category_last_page_url = "https://www.sainsburys.co.uk/shop/CategoryDisplay?listId=&catalogId=10241&searchTerm=&beginIndex=120&pageSize=60&orderBy=TOP_SELLERS%7CSEQUENCING&top_category=12518&langId=44&storeId=10151&categoryId=474593&promotionId=&parent_category_rn=12518"
        product_urls = self.test_scraper.get_product_urls(category_last_page_url)
        self.assertIsInstance(product_urls[0], str, f"Number of product_urls = {len(product_urls)}. {product_urls}")

    def test_get_product_info(self):
        product_url = "https://www.sainsburys.co.uk/gol-ui/product/fruitandveg-essentials/sainsburys-loose-fairtrade-bananas"
        test_product_info = self.test_scraper.get_product_info(product_url)
        self.assertIsInstance(test_product_info, dict, f"Product information = {test_product_info}")   
    
    def test_write_to_JSON(self):
        write_dict = {'name': 'test', 'test1': 1, 'test2': {'test2a': 2, 'test2b': '2b'}}
        folder_path = f"{self.test_scraper.cwd}\\raw_data\\test"
        try:
            assert path.exists(folder_path)
        except AssertionError:
            mkdir(folder_path)
        Scraper.write_to_JSON(self.test_scraper.cwd, write_dict)
        with open(f'{folder_path}\\data.json', 'r') as json_file:
            read_dict = load(json_file)
        self.assertDictEqual(write_dict, read_dict)

    def tearDown(self) -> None:
        self.test_scraper._driver.close()


unittest.main(argv=[''], verbosity=0, exit=False)