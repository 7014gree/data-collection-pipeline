# Data Collection Pipeline
- Graduadly implemented functions additional functions to run through the entire scraping process, modifying as required whenever they ran into errors
- First instantiated the driver to retrieve www.sainsburys.co.uk
- Then identified the tag for accepting cookies, implemented a function to click accept all
- Identified the tag to go to the groceries page and put the links for all sub categories on that page into a list
- Iterated through the list to navigate to each page for that category
- On each category page, added functions to retreive all product page links
- From there, looked through the html to identify the relevant tags that would need to be retrieved in order to collect the relevant information
- Prototyped an implementation to retrieve all of the information and put it into a dictionary.
- Ran the entire scraper, upon error the code would print the last used url. I would navigate to that page and manually review the html to identify what was causing the error and modify the code to retrieve the information to deal with those cases.
- Added code to identify the next page button tag on a given category page. Now the code would navigate to each category link, add the url for each product on the first page to a list, then navigate to the next page within that category and add all product urls on that page to a list, repeated until the next page button could no longer be found, at which point the process would repeat from the next category.
- Ran the entire scraper again to see which product pages were causing errors, modified the code after inspecting the html for the error-causing pages in order to deal with those errors without impacting current functionality.

# Milestone 4
- Had to change how product information was stored, from a dictionary of lists to individual dictionaries for each product
- Imported json for a function to write the dictionary to json. Made a write to json method
- Added a method to check if the raw data folder already exists, and if not to make the folder. Imported os to get the current working directory file path in order to construct stings containing full file paths.
- 