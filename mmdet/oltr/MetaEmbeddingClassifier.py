import torch
import torch.nn as nn
from .CosNormClassifier import CosNorm_Classifier
# from utils import *

import pdb

class MetaEmbedding_Classifier(nn.Module):
    
    def __init__(self, feat_dim=2048, num_classes=1000):
        super(MetaEmbedding_Classifier, self).__init__()

        self.num_classes = num_classes

        self.fc_hallucinator = nn.Linear(feat_dim, num_classes)
        self.fc_selector = nn.Linear(feat_dim, feat_dim)

        self.cosnorm_classifier = CosNorm_Classifier(feat_dim, num_classes)

        # self.normal_classifier = nn.Linear(feat_dim, num_classes)
        
    def forward(self, x,centroids):

        # Added by Nokia Intern Xu Ma
        # # consider the background class: padding zero
        # centroids = torch.cat([centroids,centroids[:,-1]-centroids[:,-1]],dim=0)
        # centroids = torch.cat([centroids, torch.zeros(centroids.shape[0],1)], dim=1)

        # storing direct feature
        direct_feature = x.clone()

        batch_size = x.size(0)
        feat_size = x.size(1)
        
        # set up visual memory
        x_expand = x.clone().unsqueeze(1).expand(-1, self.num_classes, -1)
        centroids_expand = centroids.clone().unsqueeze(0).expand(batch_size, -1, -1)
        keys_memory = centroids.clone()

        # computing reachability
        dist_cur = torch.norm(x_expand - centroids_expand, 2, 2)
        values_nn, labels_nn = torch.sort(dist_cur, 1)
        scale = 10.0
        # print(f"values_nn[:, 0]  contains 0 is {(values_nn[:, 0]==0).any()}")
        # print(f"values_nn[:, 0]  shape {(values_nn[:, 0]).shape}, "
        #       f"max {(values_nn[:, 0]).max()} , min {(values_nn[:, 0]).min()}")
        reachability = (scale / (values_nn[:, 0] + 1e-5)).unsqueeze(1).expand(-1, feat_size)


        # computing memory feature by querying and associating visual memory
        values_memory = self.fc_hallucinator(x.clone())
        values_memory = values_memory.softmax(dim=1)
        memory_feature = torch.matmul(values_memory, keys_memory)

        # computing concept selector
        concept_selector = self.fc_selector(x.clone())
        concept_selector = concept_selector.tanh()

        x = reachability * (direct_feature + concept_selector * memory_feature)

        
        # storing infused feature
        infused_feature = concept_selector * memory_feature
        
        logits = self.cosnorm_classifier(x)
        
        # logits = self.normal_classifier(x)

        return logits, [direct_feature, infused_feature]
        # return logits, [logits]

# def create_model(feat_dim=2048, num_classes=1000, stage1_weights=False, dataset=None, test=False, *args):
#     print('Loading Meta Embedding Classifier.')
#     clf = MetaEmbedding_Classifier(feat_dim, num_classes)
#
#     if not test:
#         if stage1_weights:
#             assert(dataset)
#             print('Loading %s Stage 1 Classifier Weights.' % dataset)
#             clf.fc_hallucinator = init_weights(model=clf.fc_hallucinator,
#                                                     weights_path='./logs/%s/stage1/final_model_checkpoint.pth' % dataset,
#                                                     classifier=True)
#         else:
#             print('Random initialized classifier weights.')
#
#     return clf
