# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


import duckdb


class DuckDBPipeline:
    def open_spider(self, spider):
        self.conn = duckdb.connect("./scraped_data.db")
        self.conn.execute(
            "CREATE TABLE IF NOT EXISTS products (id INTEGER PRIMARY KEY, title TEXT, brand TEXT, price DOUBLE, ratings DOUBLE, description TEXT)"
        )

        self.conn.execute(
            "CREATE TABLE IF NOT EXISTS reviews (review_id INTEGER PRIMARY KEY, product_id INTEGER, reviewer_name TEXT, rating TEXT, review_title TEXT, review_body TEXT, date TIMESTAMP, verified BOOLEAN, FOREIGN KEY (product_id) REFERENCES products(id))"
        )

        self.conn.execute("CREATE SEQUENCE IF NOT EXISTS seq_product_id START 1;")
        self.conn.execute("CREATE SEQUENCE IF NOT EXISTS seq_review_id START 1;")

    def process_item(self, item, spider):
        product_id = self.conn.execute(
            "SELECT nextval('seq_product_id') as id;"
        ).fetchone()[0]
        self.conn.execute(
            "INSERT INTO products VALUES (?, ?, ?, ?, ?, ?)",
            (
                product_id,
                item["title"],
                item["brand"],
                item["price"],
                item["ratings"],
                item["description"],
            ),
        )

        for review in item["reviews"]:
            review_id = self.conn.execute(
                "SELECT nextval('seq_review_id') as id;"
            ).fetchone()[0]
            self.conn.execute(
                "INSERT INTO reviews VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    review_id,
                    product_id,
                    review["reviewer_name"],
                    review["rating"],
                    review["review_title"],
                    review["review_body"],
                    review["date"],
                    review["verified"],
                ),
            )

        return item

    def close_spider(self, spider):
        self.conn.close()
