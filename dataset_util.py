import numpy as np
import pandas as pd
from database import find_all, insert_many, update_one


def check_users_with_top1000_repo(users, repos=None):
    users = find_all('users')
    if repos is None:
        top1000_repo_count = {repo['name']:0 for repo in find_all('top1000_repos')}
        repos_count = top1000_repo_count
    else:
        repos_count = {repo:0 for repo in repos}
    for i, user in enumerate(users):
        print(f"{i}/{len(users)} checking user {user['name']}")
        if len(user) == 1:
            # ignore users that not crawl repo yet 
            print("not crwal yet, ignore")
            continue
        for repo in user['repos']:
            if repo in repos_count:
                repos_count[repo] += 1
    repos_count = {k: v for k, v in sorted(repos_count.items(), key=lambda item: item[1], reverse=True)}
    
    for repo in repos_count:
        print(f"{repo}: {repos_count[repo]}")
    #print(repos_count)
    return repos_count

def check_user_star(users):
    users = [user for user in users if len(user)==2]
    users.sort(key=lambda item: len(item['repos']), reverse=True)
    for user in users:
        print(f"{user['name']} : {len(user['repos'])}")

def check_user_star_in_repos(users, repos=None):
    if repos is None:
        top1000_repos = [repo['name'] for repo in find_all('top1000_repos')]
        repos = top1000_repos
    users = [user for user in users if len(user)==2]
    for user in users:
        user['repos'] = [repo for repo in user['repos'] if repo in top1000_repos]
    users.sort(key=lambda item: len(item['repos']), reverse=True)
    for user in users:
        print(f"{user['name']} : {len(user['repos'])}")


def filter_users(users, repos, min_star=0):
    users = [user for user in users if len(user)==2]
    for user in users:
        user['repos'] = [repo for repo in user['repos'] if repo in repos]
    users = [user for user in users if len(user['repos'])>=min_star]
    return users

def filter_repos(users, repos, min_star=0):
    users = [user for user in users if len(user)==2]
    repo_count = check_users_with_top1000_repo(users)
    repos = [repo for repo in repo_count if repo_count[repo] >= min_star]
    return repos

def generate_dataset(user_treshold=20, repos_threshold=50):
    users = find_all('users')
    top1000_repos = [repo['name'] for repo in find_all('top1000_repos')]
    users = filter_users(users, top1000_repos, user_treshold)
    repos = filter_repos(users, top1000_repos, repos_threshold)
    users = filter_users(users, repos, user_treshold)
    # reverse user click star repos to [early:late]
    for user in users:
        user['repos'].reverse()
    print(f'user > {user_treshold} : {len(users)}, repos > {repos_threshold} : {len(repos)}')
    item_index = list(range(len(repos)))
    user_index = list(range(len(users)))
    item2id = {pair[0]:pair[1] for pair in zip(repos, item_index)}
    user2id = {pair[0]['name']:pair[1] for pair in zip(users, user_index)}
    dataset = []
    for user in users:
        dataset.append({
            "UserId": user2id[user['name']],
            "ItemId": str([item2id[repo] for repo in user['repos']])[1:-1].replace(',', '')
        })
    df = pd.DataFrame(dataset)
    df.to_csv('dataset.csv', index=False)

    df = pd.DataFrame([{'repo': pair[0], 'idx': pair[1]} for pair in zip(repos, item_index)])
    df.to_csv('repo2idx.csv', index=False)

    df = pd.DataFrame([{'user': pair[0]['name'], 'idx': pair[1]} for pair in zip(users, user_index)])
    df.to_csv('user2idx.csv', index=False)

if __name__ == "__main__":
    generate_dataset()
    #check_user_star(users)
    #print(len(users))
    #check_users_with_top1000_repo(users)
    #check_user_star()
    #check_user_star_in_top1000_repo()
    #check_users_with_top1000_repo()