import csv
import numpy as np
import scipy.sparse as sps
import pandas as pd
from sklearn import preprocessing, feature_extraction


class Extractor(object):
    DATA_FILE_PATH = "data/"

    def get_target_users_of_recs(self):
        # Composing the name
        file_name = self.DATA_FILE_PATH + "data_target_users_test.csv"

        with open(file_name) as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=',')
            line_count = 0

            users = []
            for line in csv_reader:
                if line_count != 0:
                    users.append(int(line[0]))
                line_count += 1

            print(f'Processed {line_count} users to make recommendations.')
            return users

    def get_target_users_of_specific_part(self, index: int):
        # Composing the name
        file_name = self.DATA_FILE_PATH + "urm" + str(index) + "_target_users_test.csv"

        with open(file_name) as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=',')
            line_count = 0

            users = []
            for line in csv_reader:
                if line_count != 0:
                    users.append(int(line[0]))
                line_count += 1

            # print(f'Processed {line_count} users to make recommendations.')
            return users


    def get_interaction_rating(self):
        # Composing the name
        file_name = self.DATA_FILE_PATH + "data_train.csv"

        with open(file_name) as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=',')
            line_count = 0

            for _ in csv_reader:
                line_count += 1

            return line_count - 1

    def get_urm_all(self):
        # Composing the name
        file_name = self.DATA_FILE_PATH + "data_train.csv"

        with open(file_name) as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=',')
            line_count = 0

            users = []
            items = []
            for line in csv_reader:
                if line_count != 0:
                    users.append(int(line[0]))
                    items.append(int(line[1]))
                line_count += 1

            print(f'Processed {line_count} interactions.')

            ones_matrix = np.ones(line_count - 1)

            return sps.coo_matrix((ones_matrix, (users, items))).tocsr()


    def get_single_urm(self, number: int):
        name = "urm" + str(number) + ".csv"
        return self._urm_extractor_code(name)

    def get_others_urm(self, selected_one: int):
        numbers = np.arange(1, 5)
        numbers = np.delete(numbers, selected_one - 1)

        array = []
        for index in numbers:
            array.append(self.get_single_urm(index))

        return array

    def get_others_urm_vstack(self, selected_one: int):
        array = self.get_others_urm(selected_one)

        array_coo = []
        for matrix in array:
            array_coo.append(matrix.tocoo())

        values = []
        rows = []
        cols = []

        for matrix in array_coo:
            for i, j, v in zip(matrix.row, matrix.col, matrix.data):
                values.append(v)
                rows.append(i)
                cols.append(j)

        return sps.coo_matrix((values, (rows, cols)), shape=self.get_urm_all().shape).tocsr()

    def _urm_extractor_code(self, name: str):
        # Composing the name
        file_name = self.DATA_FILE_PATH + name

        with open(file_name) as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=',')
            line_count = 0

            users = []
            items = []
            for line in csv_reader:
                if line_count != 0:
                    users.append(int(line[0]))
                    items.append(int(line[1]))
                line_count += 1

            print(f'Processed {line_count} interactions.')

            ones_matrix = np.ones(line_count - 1)
            return sps.coo_matrix((ones_matrix, (users, items)), shape=self.get_urm_all().shape).tocsr()

    def get_icm_asset(self):
        # Composing the name
        file_name = self.DATA_FILE_PATH + "data_ICM_asset.csv"

        with open(file_name) as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=',')
            line_count = 0

            items = []
            assets = []
            for line in csv_reader:
                if line_count != 0:
                    items.append(int(line[0]))
                    assets.append(float(line[2]))
                line_count += 1

            print(f'Processed {line_count} items.')

            le = preprocessing.LabelEncoder()
            le.fit(assets)
            assets = le.transform(assets)

            values = np.ones(line_count - 1)

            return sps.coo_matrix((values, (items, assets)))

    def get_icm_price(self):
        # Composing the name
        file_name = self.DATA_FILE_PATH + "data_ICM_price.csv"

        with open(file_name) as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=',')
            line_count = 0

            items = []
            prices = []
            for line in csv_reader:
                if line_count != 0:
                    items.append(int(line[0]))
                    prices.append(float(line[2]))
                line_count += 1

            print(f'Processed {line_count} items.')

            le = preprocessing.LabelEncoder()
            le.fit(prices)
            prices = le.transform(prices)

            values = np.ones(line_count - 1)

            return sps.coo_matrix((values, (items, prices)))

    def get_icm_subclass(self):
        # Composing the name
        file_name = self.DATA_FILE_PATH + "data_ICM_sub_class.csv"

        with open(file_name) as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=',')
            line_count = 0

            items = []
            assets = []
            for line in csv_reader:
                if line_count != 0:
                    items.append(int(line[0]))
                    assets.append(int(line[1]))
                line_count += 1

            print(f'Processed {line_count} items.')

            ones_matrix = np.ones(line_count - 1)

            return sps.coo_matrix((ones_matrix, (items, assets)))

    # ICM obtained merging horizontally all the different ICMs
    def get_icm_all(self, no_tfidf=False):
        asset_matrix = self.get_icm_asset()
        sub_matrix = self.get_icm_subclass()
        price_matrix = self.get_icm_price()
        values = []
        rows = []
        cols = []

        _, asset_cols = asset_matrix.shape
        _, sub_cols = sub_matrix.shape

        for i, j, v in zip(asset_matrix.row, asset_matrix.col, asset_matrix.data):
            values.append(v)
            rows.append(i)
            cols.append(j)

        for i, j, v in zip(sub_matrix.row, sub_matrix.col, sub_matrix.data):
            values.append(v)
            rows.append(i)
            new_j = j + asset_cols
            cols.append(new_j)

        for i, j, v in zip(price_matrix.row, price_matrix.col, price_matrix.data):
            values.append(v)
            rows.append(i)
            new_j = j + asset_cols + sub_cols
            cols.append(new_j)

        icm_all = sps.coo_matrix((values, (rows, cols))).tocsr()

        if no_tfidf:
            return icm_all

        icm_tfidf = self.preprocess_csr_matrix(icm_all)
        return icm_tfidf

    def get_ucm_age(self):
        # Composing the name
        file_name = self.DATA_FILE_PATH + "data_UCM_age.csv"

        with open(file_name) as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=',')
            line_count = 0

            users = []
            age_category = []
            for line in csv_reader:
                if line_count != 0:
                    users.append(int(line[0]))
                    age_category.append(int(line[1]))
                line_count += 1

            print(f'Processed {line_count} items.')

            ones_matrix = np.ones(line_count - 1)

            return sps.coo_matrix((ones_matrix, (users, age_category)))

    def get_ucm_region(self):
        # Composing the name
        file_name = self.DATA_FILE_PATH + "data_UCM_region.csv"

        with open(file_name) as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=',')
            line_count = 0

            users = []
            regions = []
            for line in csv_reader:
                if line_count != 0:
                    users.append(int(line[0]))
                    regions.append(int(line[1]))
                line_count += 1

            print(f'Processed {line_count} items.')

            ones_matrix = np.ones(line_count - 1)

            return sps.coo_matrix((ones_matrix, (users, regions)))

    # UCM obtained merging horizontally all the different UCMs
    def get_ucm_all(self, no_tfidf=False):
        age_matrix = self.get_ucm_age()
        reg_matrix = self.get_ucm_region()

        values = []
        rows = []
        cols = []

        _, age_cols = age_matrix.shape

        for i, j, v in zip(age_matrix.row, age_matrix.col, age_matrix.data):
            values.append(v)
            rows.append(i)
            cols.append(j)

        for i, j, v in zip(reg_matrix.row, reg_matrix.col, reg_matrix.data):
            values.append(v)
            rows.append(i)
            new_j = j + age_cols
            cols.append(new_j)

        ucm_all = sps.coo_matrix((values, (rows, cols))).tocsr()

        if no_tfidf:
            return ucm_all

        ucm_tfidf = self.preprocess_csr_matrix(ucm_all)
        return ucm_tfidf

    # Preprocessing adjustments
    def preprocess_csr_matrix(self, mat):
        ucm_tfidf = feature_extraction.text.TfidfTransformer().fit_transform(mat)
        return preprocessing.normalize(ucm_tfidf, axis=0, norm='l2')

    def get_urm_as_dataframe(self) -> pd.DataFrame:
        urm = pd.read_csv(self.DATA_FILE_PATH + 'data_train.csv')
        urm_df = pd.DataFrame(urm)
        return urm_df
