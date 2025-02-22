from Hybrid.WeightedHybrid import WeightedHybrid
from OwnUtils.Extractor import Extractor
from OwnUtils.Writer import Writer
from datetime import datetime
from Utils.evaluation_function import evaluate_algorithm
import WeightConstants
import ParametersTuning
from SLIM.SLIM_BPR_Cython import SLIM_BPR_Cython

import random
import Utils.Split.split_train_validation_leave_k_out as loo

"""
Specify the report and the submission in which we will write the results
"""

report_counter = 20
submission_counter = 2


class GenericRunner(object):

    def __init__(self, cbfknn=True, icfknn=True, ucfknn=True, slim_bpr=True, pure_svd=True, als=True, cfw=True,
                 p3a=True, rp3b=True, slim_en=True):
        """
        Initialization of the generic runner in which we decide whether or not use an algorithm
        """
        self.cbfknn = cbfknn
        self.icfknn = icfknn
        self.ucfknn = ucfknn
        self.slim_bpr = slim_bpr
        self.pure_svd = pure_svd
        self.als = als
        self.cfw = cfw
        self.p3a = p3a
        self.rp3b = rp3b
        self.slim_en = slim_en

        self.is_test = None
        self.writer = Writer
        self.result_dict = None

        self.urm_train = None
        self.urm_validation = None
        self.urm_test = None
        self.urm_post_validation = None
        self.icm = None

        self.p_cbfknn = None
        self.p_icfknn = None
        self.p_ucfknn = None
        self.p_slimbpr = None
        self.p_puresvd = None
        self.p_als = None
        self.p_cfw = None
        self.p_p3a = None
        self.p_rp3b = None
        self.p_slimen = None

        if self.cbfknn:
            self.p_cbfknn = ParametersTuning.CBFKNN_BEST
        if self.icfknn:
            self.p_icfknn = ParametersTuning.ICFKNN_BEST
        if self.ucfknn:
            self.p_ucfknn = WeightConstants.UCFKNN
        if self.slim_bpr:
            self.p_slimbpr = WeightConstants.SLIM_BPR
        if self.pure_svd:
            self.p_puresvd = WeightConstants.PURE_SVD
        if self.als:
            self.p_als = WeightConstants.ALS
        if self.cfw:
            self.p_cfw = WeightConstants.CFW
        if self.p3a:
            self.p_p3a = WeightConstants.P3A
        if self.rp3b:
            self.p_rp3b = WeightConstants.RP3B
        if self.slim_en:
            self.p_slimen = ParametersTuning.SLIM_ELASTIC_NET[0]


    def run(self, is_test, is_SSLIM):
        """
        From here we start each algorithm.
        :param is_test: specifies if we want to write a report or a submission
        """
        self.is_test = is_test
        self.is_SSLIM = is_SSLIM

        if self.is_test:
            extractor = Extractor()
            urm = extractor.get_urm_all()

            self.icm = extractor.get_icm_all()

            # Splitting into post-validation & testing in case of parameter tuning
            matrices = loo.split_train_leave_k_out_user_wise(urm, 1, False, True)

            self.urm_post_validation = matrices[0]
            self.urm_test = matrices[1]

            # Splitting the post-validation matrix in train & validation
            # (Problem of merging train and validation again at the end => loo twice)
            matrices_for_validation = loo.split_train_leave_k_out_user_wise(self.urm_post_validation, 1, False, True)
            self.urm_train = matrices_for_validation[0]
            self.urm_validation = matrices_for_validation[1]

            self.urm_train = extractor.preprocess_csr_matrix(self.urm_train)

            self.write_report()

            if self.is_SSLIM:
                # for topK in [50, 100, 200]:
                #     for epochs in [10, 20, 50, 100, 200, 300]:
                self.sslim_pars = WeightConstants.SLIM_BPR_ICM
                slim_bpr = SLIM_BPR_Cython(self.icm.copy())
                slim_bpr.fit(**self.sslim_pars)

                self.icm = slim_bpr.recs.copy().tocsr()
                self.evaluate()

            else:
                self.evaluate()

        else:
            extractor = Extractor()
            users = extractor.get_target_users_of_recs()
            self.urm_train = extractor.get_urm_all()
            self.icm = extractor.get_icm_all()

            self.write_submission(users)


    def write_report(self):
        """
        This method is useful to write the report, selecting only chosen algorithms
        """
        now = datetime.now()
        date = datetime.fromtimestamp(datetime.timestamp(now))

        self.writer.write_report(self.writer, "--------------------------------------", report_counter)
        self.writer.write_report(self.writer, "--------------------------------------\n", report_counter)
        self.writer.write_report(self.writer, "REPORT " + str(date) + "\n", report_counter)
        self.writer.write_report(self.writer, "Fixed parameters", report_counter)

        if self.cbfknn:
            self.writer.write_report(self.writer, "CBFKNN: " + str(self.p_cbfknn), report_counter)
        if self.icfknn:
            self.writer.write_report(self.writer, "ICFKNN: " + str(self.p_icfknn), report_counter)
        if self.ucfknn:
            self.writer.write_report(self.writer, "UCFKNN: " + str(self.p_ucfknn), report_counter)
        if self.slim_bpr:
            self.writer.write_report(self.writer, "SLIM_BPR: " + str(self.p_slimbpr), report_counter)
        if self.pure_svd:
            self.writer.write_report(self.writer, "PURE_SVD: " + str(self.p_puresvd), report_counter)
        if self.als:
            self.writer.write_report(self.writer, "ALS: " + str(self.p_als), report_counter)
        if self.cfw:
            self.writer.write_report(self.writer, "CFW: " + str(self.p_cfw), report_counter)
        if self.p3a:
            self.writer.write_report(self.writer, "P3A: " + str(self.p_p3a), report_counter)
        if self.rp3b:
            self.writer.write_report(self.writer, "P3A: " + str(self.p_rp3b), report_counter)
        if self.slim_en:
            self.writer.write_report(self.writer, "SLIM_ELASTIC_NET: " + str(self.p_slimen), report_counter)

        self.writer.write_report(self.writer, "VALIDATION", report_counter)
        self.writer.write_report(self.writer, "--------------------------------------", report_counter)


    def write_submission(self, users):
        """
        This method is used to write the submission, selecting only chosen algorithms
        :return:
        """
        self.writer.write_header(self.writer, sub_counter=submission_counter)

        from SLIM.SLIM_BPR_Cython import SLIM_BPR_Cython
        slim_bpr = SLIM_BPR_Cython(self.icm)
        slim_bpr.fit(**WeightConstants.SLIM_BPR)

        self.icm = slim_bpr.recs.copy().tocsr()

        recommender = WeightedHybrid(self.urm_train, self.icm, self.p_icfknn, self.p_ucfknn, self.p_cbfknn,
                                     self.p_slimbpr, self.p_puresvd, self.p_als, self.p_cfw, self.p_p3a, self.p_rp3b,
                                     self.p_slimen, WeightConstants.SUBM_WEIGHTS)
        recommender.fit()

        from tqdm import tqdm

        for user_id in tqdm(users):
            recs = recommender.recommend(user_id, at=10)
            self.writer.write(self.writer, user_id, recs, sub_counter=submission_counter)

        print("Submission file written")



    def evaluate(self):
        """
        Method used for the validation and the calculation of the weights
        """
        generated_weights = []
        results = []

        for weight in self.get_test_weights(add_random=False):
            generated_weights.append(weight)
            print("--------------------------------------")

            recommender = WeightedHybrid(self.urm_train, self.icm, self.p_icfknn, self.p_ucfknn, self.p_cbfknn,
                                         self.p_slimbpr, self.p_puresvd, self.p_als, self.p_cfw, self.p_p3a,
                                         self.p_rp3b, self.p_slimen, weight)
            recommender.fit()
            result_dict = evaluate_algorithm(self.urm_validation, recommender)
            results.append(float(result_dict["MAP"]))

            self.writer.write_report(self.writer, str(weight), report_counter)
            if self.is_SSLIM:
                self.writer.write_report(self.writer, str(self.sslim_pars), report_counter)
            self.writer.write_report(self.writer, str(result_dict), report_counter)

        # Retriving correct weight
        # results.sort()
        weight = generated_weights[int(results.index(max(results)))]

        self.writer.write_report(self.writer, "--------------------------------------", report_counter)
        self.writer.write_report(self.writer, "TESTING", report_counter)
        self.writer.write_report(self.writer, "--------------------------------------", report_counter)

        recommender = WeightedHybrid(self.urm_post_validation, self.icm, self.p_icfknn, self.p_ucfknn, self.p_cbfknn,
                                     self.p_slimbpr, self.p_puresvd, self.p_als, self.p_cfw, self.p_p3a, self.p_rp3b,
                                     self.p_slimen, weight)
        recommender.fit()
        result_dict = evaluate_algorithm(self.urm_test, recommender)

        self.writer.write_report(self.writer, str(weight), report_counter)
        self.writer.write_report(self.writer, str(result_dict), report_counter)

    def get_test_weights(self, add_random=False):
        if not add_random:
            return WeightConstants.NO_WEIGHTS
        else:
            new_weights = []
            for weight in WeightConstants.IS_TEST_WEIGHTS:
                new_weights.append(weight)
                for i in range(0, 5):
                    new_obj = weight.copy()
                    new_obj["icfknn"] += round(random.uniform(- min(0.5, weight["icfknn"]), 0.5), 2)
                    new_obj["ucfknn"] += round(random.uniform(- min(0.5, weight["ucfknn"]), 0.5), 2)
                    new_obj["cbfknn"] += round(random.uniform(- min(0.5, weight["cbfknn"]), 0.5), 2)
                    new_obj["slimbpr"] += round(random.uniform(- min(0.5, weight["slimbpr"]), 0.5), 2)
                    new_obj["puresvd"] += round(random.uniform(- min(0.5, weight["puresvd"]), 0.5), 2)
                    new_obj["als"] += round(random.uniform(- min(0.5, weight["als"]), 0.5), 2)
                    new_obj["cfw"] += round(random.uniform(- min(0.5, weight["cfw"]), 0.5), 2)
                    new_obj["p3a"] += round(random.uniform(- min(0.5, weight["p3a"]), 0.5), 2)
                    new_obj["rp3b"] += round(random.uniform(- min(0.5, weight["rp3b"]), 0.5), 2)
                    new_weights.append(new_obj)

            return new_weights

