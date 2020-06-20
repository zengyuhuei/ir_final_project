import pymongo
import configparser

def get_db(db_name = 'github'):
    config = configparser.ConfigParser()
    config.readfp(open(r'config.ini'))
    username = config.get('DATABASE', 'USERNAME')
    password = config.get('DATABASE', 'PASSWORD')
    ip = config.get('DATABASE', 'IP')
    port = config.get('DATABASE', 'PORT')
    client = pymongo.MongoClient(f'mongodb://{username}:{password}@{ip}:{port}/')
    db = client[db_name]
    return db

def get_col(col_name):
    db = get_db()
    return db[col_name]

def find_all(col_name, target={}, field_filter={'_id': 0}):
    col = get_col(col_name)
    return list(col.find(target, field_filter))

def insert_many(col_name, datas):
    col = get_col(col_name)
    x = col.insert_many(datas)
    print(f'inserted {len(x.inserted_ids)} items')

def update_one(col_name, target, data):
    col = get_col(col_name)
    x = col.update_one(target, {"$set": data})
    print(f'updated to {col_name}... {len(x)} items')
