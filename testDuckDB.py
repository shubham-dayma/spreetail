import duckdb


def test1():
    connection = duckdb.connect(database="scraped_data.db")

    query = "SELECT COUNT(*) as product_count FROM products;"

    products = connection.execute(query).fetchone()[0]

    query = "SELECT COUNT(*) as review_count FROM reviews;"

    reviews = connection.execute(query).fetchone()[0]

    # Print the results
    print(f"Fetched Products: {products}")

    print(f"Fetched reviews: {reviews}")

    connection.close()


if __name__ == "__main__":
    test1()
