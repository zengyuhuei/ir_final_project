import pymongo
import configparser

def get_db():
    config = configparser.ConfigParser()
    config.readfp(open(r'config.ini'))
    username = config.get('DATABASE', 'USERNAME')
    password = config.get('DATABASE', 'PASSWORD')
    ip = config.get('DATABASE', 'IP')
    port = config.get('DATABASE', 'PORT')
    client = pymongo.MongoClient(f'mongodb://{username}:{password}@{ip}:{port}/')
    db = client['github']
    return db
        
def init_repos_to_db(repos):    
    db = get_db()
    repos_col = db['repos']
    datas = [{'name': repo} for repo in repos]
    x = repos_col.insert_many(datas)
    print(len(x.inserted_ids))

def update_repo(repo_name):
    users = get_stargazer_from_repo(repo_name)
    db = get_db()
    repos_col = db['repos']
    repos_col.update_one({'name': repos_col}, {'stargazers': users})
    print(f'{repo_name} ... Update to db')
