#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on 07/09/17

@author: Maurizio Ferrari Dacrema
"""

from Utils.Base.Recommender_utils import check_matrix
from Utils.Base.BaseSimilarityMatrixRecommender import BaseSimilarityMatrixRecommender
from Utils.Base.Recommender_utils import similarityMatrixTopK
from Utils.Base.Incremental_Training_Early_Stopping import Incremental_Training_Early_Stopping


from Utils.CythonCompiler.run_compile_subprocess import run_compile_subprocess
import os, sys
import numpy as np


def estimate_required_MB(n_items, symmetric):

    requiredMB = 8 * n_items**2 / 1e+06

    if symmetric:
        requiredMB /=2

    return requiredMB


def get_RAM_status():

    try:
        data_list = os.popen('free -t -m').readlines()[1].split()
        tot_m = float(data_list[1])
        used_m = float(data_list[2])
        available_m = float(data_list[6])

    except Exception as exc:

        print("Unable to read memory status: {}".format(str(exc)))

        tot_m, used_m, available_m = None, None, None


    return tot_m, used_m, available_m





class SLIM_BPR_Cython(BaseSimilarityMatrixRecommender, Incremental_Training_Early_Stopping):

    RECOMMENDER_NAME = "SLIM_BPR_Recommender"


    def __init__(self, URM_train, target_users_profile,
                 free_mem_threshold = 0.5,
                 recompile_cython = False):


        super(SLIM_BPR_Cython, self).__init__(URM_train)

        assert free_mem_threshold>=0.0 and free_mem_threshold<=1.0, "SLIM_BPR_Recommender: free_mem_threshold must be between 0.0 and 1.0, provided was '{}'".format(free_mem_threshold)

        self.n_users, self.n_items = self.URM_train.shape
        self.target_users_profile = target_users_profile
        self.free_mem_threshold = free_mem_threshold

        if recompile_cython:
            print("Compiling in Cython")
            self.runCompilationScript()
            print("Compilation Complete")





    def fit(self, epochs=300,
            positive_threshold_BPR = None,
            train_with_sparse_weights = None,
            symmetric = True,
            verbose = False,
            random_seed = None,
            batch_size = 1000, lambda_i = 0.0, lambda_j = 0.0, learning_rate = 1e-4, topK = 200,
            sgd_mode='adagrad', gamma=0.995, beta_1=0.9, beta_2=0.999,
            **earlystopping_kwargs):


        # Import compiled module
        from SLIM.SLIM_BPR_Cython_Epoch import SLIM_BPR_Cython_Epoch



        self.symmetric = symmetric
        self.train_with_sparse_weights = train_with_sparse_weights


        if self.train_with_sparse_weights is None:

            # auto select
            required_m = estimate_required_MB(self.n_items, self.symmetric)

            total_m, _, available_m = get_RAM_status()

            if total_m is not None:
                string = "SLIM_BPR_Cython: Automatic selection of fastest train mode. Available RAM is {:.2f} MB ({:.2f}%) of {:.2f} MB, required is {:.2f} MB. ".format(available_m, available_m/total_m*100 , total_m, required_m)
            else:
                string = "SLIM_BPR_Cython: Automatic selection of fastest train mode. Unable to get current RAM status, you may be using a non-Linux operating system. "

            if total_m is None or required_m/available_m < self.free_mem_threshold:
                print(string + "Using dense matrix.")
                self.train_with_sparse_weights = False
            else:
                print(string + "Using sparse matrix.")
                self.train_with_sparse_weights = True



        # Select only positive interactions
        URM_train_positive = self.URM_train.copy()

        self.positive_threshold_BPR = positive_threshold_BPR
        self.sgd_mode = sgd_mode
        self.epochs = epochs


        if self.positive_threshold_BPR is not None:
            URM_train_positive.data = URM_train_positive.data >= self.positive_threshold_BPR
            URM_train_positive.eliminate_zeros()

            assert URM_train_positive.nnz > 0, "SLIM_BPR_Cython: URM_train_positive is empty, positive threshold is too high"


        self.cythonEpoch = SLIM_BPR_Cython_Epoch(URM_train_positive,
                                                 train_with_sparse_weights = self.train_with_sparse_weights,
                                                 final_model_sparse_weights = True,
                                                 topK=topK,
                                                 learning_rate=learning_rate,
                                                 li_reg = lambda_i,
                                                 lj_reg = lambda_j,
                                                 batch_size=1,
                                                 symmetric = self.symmetric,
                                                 sgd_mode = sgd_mode,
                                                 verbose = verbose,
                                                 random_seed = random_seed,
                                                 gamma=gamma,
                                                 beta_1=beta_1,
                                                 beta_2=beta_2)




        if(topK != False and topK<1):
            raise ValueError("TopK not valid. Acceptable values are either False or a positive integer value. Provided value was '{}'".format(topK))
        self.topK = topK


        self.batch_size = batch_size
        self.lambda_i = lambda_i
        self.lambda_j = lambda_j
        self.learning_rate = learning_rate

        self.S_incremental = self.cythonEpoch.get_S()
        self.S_best = self.S_incremental.copy()

        self._train_with_early_stopping(epochs,
                                        algorithm_name = self.RECOMMENDER_NAME,
                                        **earlystopping_kwargs)

        self.get_S_incremental_and_set_W()

        self.cythonEpoch._dealloc()

        sys.stdout.flush()

        self.recs = self.target_users_profile.dot(self.W_sparse)


    def _prepare_model_for_validation(self):
        self.get_S_incremental_and_set_W()


    def _update_best_model(self):
        self.S_best = self.S_incremental.copy()

    def _run_epoch(self, num_epoch):
       self.cythonEpoch.epochIteration_Cython()





    def get_S_incremental_and_set_W(self):

        self.S_incremental = self.cythonEpoch.get_S()

        if self.train_with_sparse_weights:
            self.W_sparse = self.S_incremental
            self.W_sparse = check_matrix(self.W_sparse, format='csr')
        else:
            self.W_sparse = similarityMatrixTopK(self.S_incremental, k = self.topK)
            self.W_sparse = check_matrix(self.W_sparse, format='csr')





    def writeCurrentConfig(self, currentEpoch, results_run, logFile):

        current_config = {'lambda_i': self.lambda_i,
                          'lambda_j': self.lambda_j,
                          'batch_size': self.batch_size,
                          'learn_rate': self.learning_rate,
                          'topK_similarity': self.topK,
                          'epoch': currentEpoch}

        print("Test case: {}\nResults {}\n".format(current_config, results_run))
        # print("Weights: {}\n".format(str(list(self.weights))))

        sys.stdout.flush()

        if (logFile != None):
            logFile.write("Test case: {}, Results {}\n".format(current_config, results_run))
            logFile.flush()





    def runCompilationScript(self):

        # Run compile script setting the working directory to ensure the compiled file are contained in the
        # appropriate subfolder and not the project root

        file_subfolder = "/SLIM_BPR/Cython"
        file_to_compile_list = ['SLIM_BPR_Cython_Epoch.pyx']

        run_compile_subprocess(file_subfolder, file_to_compile_list)

        print("{}: Compiled module {} in subfolder: {}".format(self.RECOMMENDER_NAME, file_to_compile_list, file_subfolder))

        # Command to run compilation script
        # python compile_script.py SLIM_BPR_Cython_Epoch.pyx build_ext --inplace

        # Command to generate html report
        # cython -a SLIM_BPR_Cython_Epoch.pyx

    def get_expected_ratings(self, user_id):
        expected_ratings = self.recs[user_id].todense()
        return np.squeeze(np.asarray(expected_ratings))

    def recommend(self, user_id, at=10):
        expected_ratings = self.get_expected_ratings(user_id)

        recommended_items = np.flip(np.argsort(expected_ratings), 0)

        unseen_items_mask = np.in1d(recommended_items, self.URM_train[user_id].indices,
                                    assume_unique=True, invert=True)
        recommended_items = recommended_items[unseen_items_mask]
        return recommended_items[0:at]


