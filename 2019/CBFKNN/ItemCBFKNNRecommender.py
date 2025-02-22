from Utils.Base.Similarity.Compute_Similarity_Python import Compute_Similarity_Python
from Utils.Base.BaseSimilarityMatrixRecommender import BaseItemSimilarityMatrixRecommender
import numpy as np

class ItemCBFKNNRecommender():

    def __init__(self, target_user_profile, ICM):
        #super(BaseItemSimilarityMatrixRecommender, self).__init__(URM)
        self.URM = target_user_profile
        self.ICM = ICM

    def fit(self, topK=50, shrink=100, normalize=True, similarity="cosine", asymmetric_alpha=0.5,
                   tversky_alpha=1.0, tversky_beta=1.0, row_weights=None):

        similarity_object = Compute_Similarity_Python(self.ICM.T, shrink=shrink,
                                                      topK=topK, normalize=normalize,
                                                      similarity=similarity, asymmetric_alpha=asymmetric_alpha,
                                                      tversky_alpha=tversky_alpha, tversky_beta=tversky_beta,
                                                      row_weights=row_weights)
        self.W_sparse = similarity_object.compute_similarity()
        self.recs = self.URM.dot(self.W_sparse)

    def recommend(self, user_id, at=None, exclude_seen=True):
        # compute the scores using the dot product
        user_profile = self.URM[user_id]
        scores = user_profile.dot(self.W_sparse).toarray().ravel()

        if exclude_seen:
            scores = self.filter_seen(user_id, scores)

        # rank items
        ranking = scores.argsort()[::-1]

        return ranking[:at]

    def get_expected_ratings(self, user_id):
        #user_profile = self.URM[user_id]
        #return user_profile.dot(self.W_sparse).toarray().ravel()
        expected_ratings = self.recs[user_id].todense()
        return np.squeeze(np.asarray(expected_ratings))

    def filter_seen(self, user_id, scores):
        start_pos = self.URM.indptr[user_id]
        end_pos = self.URM.indptr[user_id + 1]

        user_profile = self.URM.indices[start_pos:end_pos]

        scores[user_profile] = -np.inf

        return scores