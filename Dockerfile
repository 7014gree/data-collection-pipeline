FROM python:3.8

# Adding trusting keys to apt for repositories, you can download and add them using the following command:
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add -

# Add Google Chrome. Use the following command for that
RUN sh -c 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list'

# Update apt:
RUN apt-get -y update

# And install google chrome:
RUN apt-get install -y google-chrome-stable

# Download chromdriver zip
RUN wget -O /tmp/chromedriver.zip http://chromedriver.storage.googleapis.com/`curl -sS chromedriver.storage.googleapis.com/LATEST_RELEASE`/chromedriver_linux64.zip

# Unzip chromedriver
RUN apt-get install -yqq unzip

RUN unzip /tmp/chromedriver.zip chromedriver -d /usr/local/bin/

# Copy scraper.py
COPY scraper.py scraper.py

# Copy and install requirements
COPY requirements.txt requirements.txt

RUN python -m pip install --upgrade pip

RUN pip3 install -r requirements.txt

ENTRYPOINT [ "python3", "scraper.py" ]



