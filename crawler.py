import requests
import json
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor
from time import time

def parse_link(link):
    links = link.split(',')
    result = []
    for l in links:
        url = l.split(';')[0].strip()[1:-1]
        rel = l.split(';')[1].strip()[5:-1]
        result.append((url, rel))
    return result

def get_next_page(links):
    page = None
    for link in links:
        if link[1] == 'next':
            page = link[0].split('&page=')[1]
    return page

def get_user_starred_repo(user, page=1, per_page=100):
    print(f'crawling user {user}... page {page}...')
    response = requests.get(f'https://api.github.com/users/{user}/starred?per_page={per_page}&page={page}')
    datas = response.json()
    # not only one page
    next_page = None
    if 'link' in response.headers:
        links = parse_link((response.headers['link']))
        next_page = get_next_page(links)
    repos = []
    for data in datas:
        repos.append(data['html_url'].replace('https://github.com/', ''))
    if next_page != None:
        repos += get_user_starred_repo(user, next_page)
    return repos 

def get_stargazer_from_repo(repo_name):
    start_time = time()
    print(f'{repo_name} ... Started')
    users= []
    is_end = False
    url = f'https://github.com/{repo_name}/stargazers'
    while not is_end:
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        lis = soup.select('#repos > ol')[0].find_all('li')
        try:
            next_button = soup.select('#repos > div.paginate-container > div')[0].findChildren()[1]
            if next_button.name == 'button':
                is_end = True
            else:
                url = next_button['href']
        except:
            is_end = True
        for li in lis:
            users.append(li.a['href'][1:])
        print(len(users))
    print(users)
    print(f'{repo_name} ... Cost {start_time-time()} seconds')
    return users

def get_top1000(mode):
    '''
    params: mode = 'users' or 'repositories
    '''
    base_url = f'https://gitstar-ranking.com/{mode}'
    repos = []
    for i in range(1, 11):
        url = base_url + f'?page={i}'
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        _as = soup.select('body > div.container > div.row > div:nth-child(1) > div')[0].find_all('a') + \
              soup.select('body > div.container > div.row > div:nth-child(2) > div')[0].find_all('a')
        
        for a in _as:
            repos.append(a['href'][1:])
        print(len(repos))
    return repos

def concurrent_crawl_top_repos(max_workers):
    db = get_db()
    repos_col = db['repos']
    repos = list(repos_col.find({}, {'_id': 0}))
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        for repo in repos:
            executor.submit(get_stargazer_from_repo, repo['name'])

if __name__ == '__main__':
    #repos = get_user_starred_repo('ysam12345')
    '''
    users = get_stargazer_from_repo('https://github.com/CTeX-org/forum')
    
    for user in users:
        repos = get_user_starred_repo(user)
        print(repos)
    '''
    #repos = get_top1000('repositories')
    users = get_top1000('users')
    #insert_repos_to_db(repos)
    #concurrent_crawl_top_repos(1)