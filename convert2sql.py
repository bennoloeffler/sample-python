
import xml.etree.ElementTree as ET
import sqlite3

# Database connection setup using langchain SQLDatabase
conn = sqlite3.connect("amf-data.sqlite3.db")
cursor = conn.cursor()

# Drop tables if they exist and then create them
table_creation_statements = {
    'articles': '''
    CREATE TABLE IF NOT EXISTS articles (
        article_id INTEGER PRIMARY KEY,
        manufacturer_aid INTEGER,
        manufacturer_name TEXT,
        order_number INTEGER,
        short_description TEXT,
        long_description TEXT,
        ean INTEGER
    );
    ''',
    'features': '''
    CREATE TABLE IF NOT EXISTS features (
        feature_id INTEGER PRIMARY KEY AUTOINCREMENT,
        article_id INTEGER,
        name TEXT,
        value TEXT,
        unit TEXT,
        FOREIGN KEY (article_id) REFERENCES articles(article_id)
    );
    ''',
    'prices': '''
    CREATE TABLE IF NOT EXISTS prices (
        price_id INTEGER PRIMARY KEY AUTOINCREMENT,
        article_id INTEGER,
        amount REAL,
        currency TEXT,
        tax REAL,
        lower_bound INTEGER,
        FOREIGN KEY (article_id) REFERENCES articles(article_id)
    );
    ''',
    'mime_info': '''
    CREATE TABLE IF NOT EXISTS mime_info (
        mime_id INTEGER PRIMARY KEY AUTOINCREMENT,
        article_id INTEGER,
        mime_type TEXT,
        source TEXT,
        purpose TEXT,
        FOREIGN KEY (article_id) REFERENCES articles(article_id)
    );
    ''',
    'keywords': '''
    CREATE TABLE IF NOT EXISTS keywords (
        keyword_id INTEGER PRIMARY KEY AUTOINCREMENT,
        article_id INTEGER,
        keyword TEXT,
        FOREIGN KEY (article_id) REFERENCES articles(article_id)
    );
    '''
}

# Drop tables if they exist
for table in ['keywords', 'mime_info', 'prices', 'features', 'articles']:
    cursor.execute(f"DROP TABLE IF EXISTS {table}")

# Create tables
for table, creation_statement in table_creation_statements.items():
    cursor.execute(creation_statement)

# Parse the XML
tree = ET.parse('Data/BME_CAT.xml')
root = tree.getroot()


# Function to insert into the database
def insert_into_db(table, columns, values):
    # try:
        vals = ', '.join("'{}'".format(val) for val in values)
        cols = ', '.join('{}'.format(col) for col in columns)
        sql = f'INSERT INTO "{table}" ({cols}) VALUES ({vals})'
        # print(f'SQL: {sql}')
        cursor.execute(sql)
    # except:
    #     print(f"SQL: {sql}")


def text_or_empty(base, key):
    val = base.find(key)
    return val.text.replace("'", '') if val is not None else ''

def int_or_empty(base, key):
    val = base.find(key)
    return int(val.text) if val is not None else 0

def float_or_empty(base, key):
    val = base.find(key)
    return float(val.text) if val is not None else 0

article_id = 0

# Iterate through the XML structure and extract data
for article in root.findall('.//ARTICLE'):
    article_id += 1
    print(f"\r{article_id}", end='')

    detail = article.find('.//ARTICLE_DETAILS')

    if detail is not None:
        # Extract and insert article data
        manufacturer_aid = int_or_empty(detail, 'MANUFACTURER_AID')
        manufacturer_name = text_or_empty(detail, 'MANUFACTURER_NAME')
        order_number = int_or_empty(detail, 'ARTICLE_ORDER')
        short_desc = text_or_empty(detail, 'DESCRIPTION_SHORT')
        long_desc = text_or_empty(detail, 'DESCRIPTION_LONG')
        ean = int_or_empty(detail, 'EAN')
        print(f" {ean}", end='  ')

        insert_into_db('articles', 
                    ['article_id', 'manufacturer_aid', 'manufacturer_name', 
                        'order_number', 'short_description', 'long_description', 'ean'], 
                    [article_id, manufacturer_aid, manufacturer_name,
                        order_number, short_desc, long_desc, ean])

        # Extract and insert feature data
        for feature in article.findall('.//FEATURE'):
            name = text_or_empty(feature, 'FNAME')
            value = text_or_empty(feature, 'FVALUE')
            unit = text_or_empty(feature, 'FUNIT')
            insert_into_db('features',
                            ['article_id', 'name', 'value', 'unit'], 
                            [article_id, name, value, unit])

        # Extract and insert price data
        for price in article.findall('.//ARTICLE_PRICE'):
            amount = float_or_empty(price, 'PRICE_AMOUNT')
            currency = text_or_empty(price, 'PRICE_CURRENCY')
            tax = float_or_empty(price, 'TAX')
            lower_bound = int_or_empty(price, 'LOWER_BOUND')
            insert_into_db('prices',
                          ['article_id', 'amount', 'currency', 'tax', 'lower_bound'],
                          [article_id, amount, currency, tax, lower_bound])

        # Extract and insert MIME info
        for mime in article.findall('.//MIME'):
            mime_type = text_or_empty(mime, 'MIME_TYPE')
            source = text_or_empty(mime, 'MIME_SOURCE')
            purpose = text_or_empty(mime, 'MIME_PURPOSE')
            insert_into_db('mime_info',
                           ['article_id', 'mime_type', 'source', 'purpose'], 
                           [article_id, mime_type, source, purpose])

        # Extract and insert keywords
        for keyword_elem in article.findall('.//KEYWORD'):
            keyword = keyword_elem.text
            insert_into_db('keywords',
                           ['article_id', 'keyword'],
                           [article_id, keyword])

    conn.commit()

