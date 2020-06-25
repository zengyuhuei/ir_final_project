import requests
import json
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor
from time import time, sleep
from database import find_all, insert_many, update_one
from proxy import proxy_get
from copy import deepcopy
import configparser


headers = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36'}

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

def get_with_token(url, rate_limit=5000):
    config = configparser.ConfigParser()
    config.readfp(open(r'config.ini'))
    access_token = config.get('GITHUB', 'ACCESSTOKEN')
    header_with_token = deepcopy(headers)
    header_with_token['Authorization'] = f'token {access_token}'
    res = requests.get(url, headers=header_with_token)
    if res.status_code != 200:
        print(f"ERROR status_code: {res.status_code}")
        print(f"ERROR message: {res.text}")
    if int(res.headers['X-RateLimit-Limit']) < rate_limit or int(res.headers['X-RateLimit-Remaining']) == 0:
        print(f"Limit Error, X-RateLimit-Limit: {res.headers['X-RateLimit-Limit']}, \
                             X-RateLimit-Remaining: {res.headers['X-RateLimit-Remaining']}")
    assert(int(res.headers['X-RateLimit-Limit']) >= rate_limit)
    assert(int(res.headers['X-RateLimit-Remaining']) > 0)
    return res

def get_user_starred_repo(user, mode='token', page=1, per_page=30):
    '''
    mode: token(use GitHub access token), proxy(use proxy), normal(direct send request)
    '''
    print(f'crawling user {user}... page {page}...')
    assert(mode in ['normal', 'proxy', 'token'])
    if mode == 'normal':
        response = requests.get(f'https://api.github.com/users/{user}/starred?per_page={per_page}&page={page}')
    elif mode == 'proxy':
        response = proxy_get(f'https://api.github.com/users/{user}/starred?per_page={per_page}&page={page}')
    elif mode == 'token':
        response = get_with_token(f'https://api.github.com/users/{user}/starred?per_page={per_page}&page={page}')
    # handle error
    if response.status_code != 200:
        print(f"[Error] code: {response.status_code}")
        print(response.json())
    # handle not found
    if response.status_code == 404:
        return None
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
        repos += get_user_starred_repo(user, mode, next_page)
    return repos 


def get_repo_detail(repo_name, mode='token', retry=5):
    '''
    mode: token(use GitHub access token), proxy(use proxy), normal(direct send request)
    '''
    print(f'crawling repo {repo_name}...')
    assert(mode in ['normal', 'proxy', 'token'])
    if mode == 'normal':
        response = requests.get(f'https://api.github.com/repos/{repo_name}')
    elif mode == 'proxy':
        response = proxy_get(f'https://api.github.com/repos/{repo_name}')
    elif mode == 'token':
        response = get_with_token(f'https://api.github.com/repos/{repo_name}')
    # handle error
    '''
    if response.status_code != 200:
        print(f"[Error] repo: {repo_name} code: {response.status_code}")
        print(response.json())
    if retry > 0:
        return get_repo_detail(repo_name, mode='token', retry=retry-1)
    else:
        # handle not found
        if response.status_code == 404:
            return None
        return response.json()
    '''
    if response.status_code != 200:
        print(f"[Error] repo: {repo_name} code: {response.status_code}")
        print(response.json())
    if response.status_code == 404:
        return None
    return response.json()

    

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
    params: mode = 'users' or 'repositories'
    '''
    base_url = f'https://gitstar-ranking.com/{mode}'
    datas = []
    for i in range(1, 11):
        url = base_url + f'?page={i}'
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        _as = soup.select('body > div.container > div.row > div:nth-child(1) > div')[0].find_all('a') + \
              soup.select('body > div.container > div.row > div:nth-child(2) > div')[0].find_all('a')
        
        for a in _as:
            datas.append(a['href'][1:])
        print(len(datas))
    return datas

def get_most_active_users():
    '''
    # get 256 users from commits.top website
    '''
    url = 'https://commits.top/worldwide.html'
    users = []
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    trs = soup.select('table')[0].find_all('tr')
    for tr in trs:
        tds = tr.find_all('td')
        # avoid table title
        if len(tds) == 4:
            username = tds[1].find('a').text
            users.append(username)
    print(len(users))
    return users


'''
def concurrent_crawl_top_repos(max_workers):
    repos = find_all('repos')
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        for repo in repos:
            executor.submit(get_stargazer_from_repo, repo['name'])
'''

def get_user_from_github(query='followers:>2500', page=1, per_page=100):
    print(f'crawling user {query}... page {page}...')
    users = []
    response = get_with_token(f'https://api.github.com/search/users?q={query}&per_page={per_page}&page={page}', 30)
    # handle error
    if response.status_code != 200:
        print(f"[Error] code: {response.status_code}")
        print(response.json())
    data = response.json()
    # not only one page
    next_page = None
    if 'link' in response.headers:
        links = parse_link((response.headers['link']))
        next_page = get_next_page(links)
    
    for item in data['items']:
        users.append(item['login'])
    if next_page != None:
        sleep_second = 2
        print(f'total {data["total_count"]}, sleep for {sleep_second} seconds to avoid reach API limit')
        sleep(sleep_second)
        users += get_user_from_github(query, next_page)
    return users 

def init_users_to_db(users):
    #datas = [{'name': user} for user in users]
    users_in_db = find_all('users', field_filter={'_id': 0, 'repos': 0})
    users_in_db = [user['name'] for user in users_in_db]
    new_users = [user for user in users if user not in users_in_db]
    print(f"{len(users) - len(new_users)} users already in db, insert {len(new_users)} users")
    if len(new_users) > 0:
        insert_many('users', [{'name': user} for user in new_users])

def crawl_top_users():
    users = find_all('users')
    users = [user for user in users if len(user) == 1]
    for i, user in enumerate(users):
        print(f'crawling {i+1}/{len(users)}...')
        repos = get_user_starred_repo(user['name'])
        print(f"finish {user['name']} total: {len(repos)} update to db")
        update_one('users', {'name': user['name']}, {'repos': repos})

def insert_user_starred_repo(user, mode='token'):
    repos = get_user_starred_repo(user['name'], mode)
    print(f"finish {user['name']} total: {len(repos)} update to db")
    update_one('users', {'name': user['name']}, {'repos': repos})

def concurrent_crawl_repo_of_users(max_workers, mode='token'):
    users = find_all('users')
    users = [user for user in users if len(user) == 1]
    print(f'crawl user num: {len(users)}......')
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        for i, user in enumerate(users):
            #print(f'crawling {i+1}/{len(users)}...')
            executor.submit(insert_user_starred_repo, user, mode)

def concurrent_crawl_top1000_repo_details(max_workers, mode='token'):
    repos = find_all('top1000_repos')
    exist_repos = find_all('top1000_repos_detail', field_filter={'_id': 0, 'full_name': 1})
    exist_repo_names = [exist_repo['full_name'].lower() for exist_repo in exist_repos]
    repo_names = [repo['name'] for repo in repos if repo['name'].lower() not in exist_repo_names]
    print(len(repo_names))
    #print(repo_names)
    #exit()
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        for i, repo_name in enumerate(repo_names):
            #print(f'crawling {i+1}/{len(users)}...')
            executor.submit(insert_repo_detail, repo_name, mode)

def insert_repo_detail(repo_name, mode='token'):
    repo_detail = get_repo_detail(repo_name, mode)
    print(f"finish {repo_name} update to db")
    update_one('top1000_repos_detail', {'name': repo_detail['name']}, repo_detail)



if __name__ == '__main__':
    #repos = get_user_starred_repo('ysam12345')
    '''
    users = get_stargazer_from_repo('https://github.com/CTeX-org/forum')
    
    for user in users:
        repos = get_user_starred_repo(user)
        print(repos)
    '''
    #repos = get_top1000('repositories')
    '''
    get top 1000 users and insert to db
    '''
    #users = get_top1000('users')
    #init_users_to_db(users)

    '''
    get most activate 256 users and insert to db
    '''
    #users = get_most_active_users()
    #init_users_to_db(users)

    '''
    get users > 1000 followers
    because of the GitHub API limit that can only query 1000 result,
    we have to split our query to multiple query to retrive complete user list
    follower > 2500: 715 users, 2500 > follower > 1500: 746 users, 1500 > follower > 1000: 870 users
    '''
    #users = get_user_from_github(query='followers:>2500')
    #users += get_user_from_github(query='followers:1500..2500')
    #users += get_user_from_github(query='followers:1000..1500')
    #init_users_to_db(users)

    #insert_repos_to_db(repos)
    #concurrent_crawl_repo_of_users(300, 'proxy')
    #crawl_top_users()
    #concurrent_crawl_repo_of_users(1, 'token')

    concurrent_crawl_top1000_repo_details(300, mode='proxy')