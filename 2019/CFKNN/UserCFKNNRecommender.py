from Utils.Base.Similarity.Compute_Similarity_Python import Compute_Similarity_Python
from Utils.Base.BaseSimilarityMatrixRecommender import BaseItemSimilarityMatrixRecommender
import numpy as np


class UserCFKNNRecommender():

    def __init__(self, train, target_users_profile):
        self.train = train

        # IN CROSS VALIDATION THIS IS THE URM OF TARGET USERS WITHOUT THE TEST ITEMS
        self.URM = target_users_profile

    def fit(self, topK=50, shrink=100, normalize=True, similarity="cosine", asymmetric_alpha=0.5,
            tversky_alpha=1.0, tversky_beta=1.0, row_weights=None):

        similarity_object = Compute_Similarity_Python(self.URM.transpose(), shrink=shrink,
                                                      topK=topK, normalize=normalize,
                                                      similarity=similarity, asymmetric_alpha=asymmetric_alpha,
                                                      tversky_alpha=tversky_alpha, tversky_beta=tversky_beta,
                                                      row_weights=row_weights)

        self.W_sparse = similarity_object.compute_similarity()
        self.recs = self.W_sparse.dot(self.URM)

    def recommend(self, user_id, at=None, exclude_seen=True):
        # compute the scores using the dot product
        scores = self.W_sparse[user_id, :].dot(self.URM).toarray().ravel()

        if exclude_seen:
            scores = self.filter_seen(user_id, scores)

        # rank items
        ranking = scores.argsort()[::-1]

        return ranking[:at]

    def get_expected_ratings(self, user_id):
        expected_ratings = self.recs[user_id].todense()
        return np.squeeze(np.asarray(expected_ratings))

    def filter_seen(self, user_id, scores):
        start_pos = self.URM.indptr[user_id]
        end_pos = self.URM.indptr[user_id + 1]

        user_profile = self.URM.indices[start_pos:end_pos]

        scores[user_profile] = -np.inf

        return scores
