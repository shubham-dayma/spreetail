### Overview
The purpose of this project is to parse product details along with their reviews from the links stored in the [attachments/urls.csv](https://github.com/shubham-dayma/spreetail/blob/main/attachments/urls.csv) file. It uses the Python [Scrapy](https://pypi.org/project/scrapy/) framework to perform this task. Execution begins by opening the browser to mimic human behavior, and then Scrapy's spider takes over.

### Installation
Works best with Python 3.12 and Chrome version 132.*

Run the following command to install project dependencies:
```bash
pip install -r requirements.txt
```

### Execution
To run the crawler, use:
```bash
scrapy crawl product_spider
```

### Demo
https://github.com/user-attachments/assets/815e1e0a-e15f-43e4-b261-d621dbfb1904

