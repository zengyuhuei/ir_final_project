import argparse
import random
import numpy as np
import torch

dev = torch.device("cpu")

class MF_BPR(torch.nn.Module):
    def __init__(self, n_users, n_items, f):
        super().__init__()
        self.users = torch.nn.Embedding(n_users, f)
        self.items = torch.nn.Embedding(n_items, f)
        torch.nn.init.normal_(self.users.weight, std=0.01)
        torch.nn.init.normal_(self.items.weight, std=0.01)
    def forward(self, user, pos_i, neg_j):
        user = self.users(user)
        pos_i = self.items(pos_i)
        neg_j = self.items(neg_j)
        pos_predict = (user*pos_i).sum(dim=1)
        neg_predict = (user*neg_j).sum(dim=1)
        log_prob = torch.nn.functional.logsigmoid(pos_predict - neg_predict).sum()
        # return loss function
        return -log_prob
    def recommend(self, user):
        user = self.users(user)
        pred = torch.mm(user, self.items.weight.t())
        pred = torch.argsort(pred, dim=1, descending=True)
        return pred
        
class UpdateUser(torch.nn.Module):
    def __init__(self, f):
        super().__init__()
        self.new_user = torch.nn.Embedding(1, f)
        torch.nn.init.normal_(self.new_user.weight, std=0.01)
    def forward(self, n_user, pos_i, neg_j, items):
        user = self.new_user(n_user)
        pos_i = items(pos_i)
        neg_j = items(neg_j)
        pos_predict = (user*pos_i).sum(dim=1)
        neg_predict = (user*neg_j).sum(dim=1)
        log_prob = torch.nn.functional.logsigmoid(pos_predict - neg_predict).sum()
        # return loss function
        return -log_prob
 
def ParseData(filepath, all_i):
    negative_set = set([i for i in range(all_i)])
    
    with open(args.data_path, 'r') as f:
        data = f.readlines()
    positive_set = data[0].strip().split(' ')
    positive_set = set(map(int, positive_set))
    for pos in positive_set:
        negative_set.remove(pos)
    
    return positive_set, negative_set

def DirectParseData(data, all_i):
    negative_set = set([i for i in range(all_i)])
    positive_set = data
    positive_set = set(map(int, positive_set))
    for pos in positive_set:
        negative_set.remove(pos)
    
    return positive_set, negative_set

def GetTopKRecommend(path, all_u, all_i, dim, epoch, ratio, top_k, positive_set, negative_set):
    pretrain_model = MF_BPR(all_u, all_i, dim)
    pretrain_model.load_state_dict(torch.load(path, map_location=dev))
    update_model = UpdateUser(dim)
    update_model = update_model.to(dev)
    opt = torch.optim.SGD(update_model.parameters(), lr=1e-3, weight_decay=0.025)
    
    rel_u = []
    rel_i = []
    for pos in positive_set:
        for i in range(ratio):
            rel_u.append(0)
            rel_i.append(pos)

    for i in range(epoch):
        user = torch.LongTensor(rel_u).to(dev)
        pos_i = torch.LongTensor(rel_i).to(dev)
        # negative sampling
        rel_j = []
        rel_j.extend(random.choices(list(negative_set), k=len(positive_set)*ratio))
        neg_j = torch.LongTensor(rel_j).to(dev)
        opt.zero_grad()
        loss = update_model(user, pos_i, neg_j, pretrain_model.items)
        loss.backward()
        opt.step()
    
    pred = torch.mm(update_model.new_user.weight, pretrain_model.items.weight.t())
    pred = torch.argsort(pred, dim=1, descending=True)
    recommend_list = pred.tolist()[0]
    cnt, i = 0, 0
    top_k_list = []
    while cnt < top_k and i < len(recommend_list):
        if recommend_list[i] not in positive_set:
            top_k_list.append(recommend_list[i])
            cnt += 1
        i += 1
    return top_k_list
    
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-u", help="User number", required=False, default=1168, dest="all_u")
    parser.add_argument("-i", help="Item number", required=False, default=838, dest="all_i")
    parser.add_argument("-d", help="vector dimension", required=False, default=64, dest="dim")
    parser.add_argument("-e", help="epoch", required=False, default=256, dest="epoch")
    parser.add_argument("-n", help="negative:positive", required=False, default=20, dest="ratio")
    parser.add_argument("-k", help="output top k items", required=False, default=10, dest="top_k")
    parser.add_argument("-m", help="model file path", required=True, dest="model_path")
    parser.add_argument("-f", help="file path of new user positive feedback", required=True, dest="data_path")
    args = parser.parse_args()
    
    positive_set, negative_set = ParseData(args.data_path, args.all_i)
    top_k_list = GetTopKRecommend(args.model_path, args.all_u, args.all_i, args.dim, args.epoch, args.ratio, args.top_k, positive_set, negative_set)
    print(top_k_list)
