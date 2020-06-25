import numpy as np
import pandas as pd
from random import sample
from database import find_one, find_all, insert_many, update_one
import crawler
from predict.online_learning_predict import GetTopKRecommend, DirectParseData


def get_user_starred_repo(username, filter_repos_in_db=False):
    repos = crawler.get_user_starred_repo(username)
    if repos is not None and filter_repos_in_db == True:
        df = pd.read_csv('repo2idx.csv')
        items = list(df['repo'])
        repos = [repo for repo in repos if repo in items]
    return repos


def get_user_info(username):
    '''
    return user starred repos if user exist in db
    '''
    user = find_one('online_user', {'name': username})
    return user


def predict(username):
    '''
    return top 10 predict repos to user
    '''
    repos = get_user_starred_repo(username)
    positive_set, negative_set = DirectParseData(repo2idx(repos), 838)
    predict_repos = idx2repo(GetTopKRecommend(
        path='./predict/weight/model_MAP_0.10040_np_20_epoch_32_d_64',
        all_u=1168, all_i=838, dim=64,
        epoch=256, ratio=20, top_k=10, positive_set=positive_set, negative_set=negative_set))
    predict_detail = find_all(col_name='top1000_repos_detail',
                       target={"full_name": {"$in": predict_repos}},
                       field_filter={'_id': 0, 'full_name': 1, 'description': 1,
                                     'language': 1, 'stargazers_count': 1})
    return predict_detail


def random_get_repos(n=10):
    df = pd.read_csv('repo2idx.csv')
    items = list(df['repo'])
    return find_all(col_name='top1000_repos_detail',
                    target={"full_name": {"$in": sample(items, n)}},
                    field_filter={'_id': 0, 'full_name': 1, 'description': 1,
                                  'language': 1, 'stargazers_count': 1})


def repo2idx(repos):
    '''
    given a list of repo, filter repos in db and return index of repos.
    '''
    df = pd.read_csv('repo2idx.csv')
    items = list(df['repo'])
    # df[df['repo']=='alibaba/arthas']['idx'].values[0]
    return [items.index(repo) for repo in repos if repo in items]


def idx2repo(idxs):
    '''
    given a list of index, return list of repo names.
    '''
    df = pd.read_csv('repo2idx.csv')
    items = list(df['repo'])
    # df[df['repo']=='alibaba/arthas']['idx'].values[0]
    return [items[idx] for idx in idxs if idx in range(len(items))]
