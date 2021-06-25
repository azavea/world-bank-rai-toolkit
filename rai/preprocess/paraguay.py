import numpy as np

from rai.preprocess.preprocessor import Preprocessor

NAME_COL = 'SECT_NAME'
LENGTH_COL = 'LENGTH'


class ParaguayPreprocessor(Preprocessor):
    def add_standardized_columns(self):
        self.df.loc[:, self.processed_name_col] = self.df[NAME_COL]
        self.df.loc[:, self.processed_length_col] = self.df[LENGTH_COL]
        super().add_standardized_columns()

    def process(self):
        self.extract_code_col()
        self.merge_route_parts()

    def extract_code_col(self):
        name_col = self.processed_name_col
        df = self.df
        parsed = df[name_col].str.extract(r'^([^\s]+) (.*)$')
        df.loc[:, 'code'] = parsed[0]
        df.loc[:, name_col] = parsed[1]
        self.df = df

    def merge_route_parts(self):
        name_col = self.processed_name_col
        length_col = self.processed_length_col
        df = self.df

        # extract name into 3 columns:
        # 0: names that do not end in numbers,
        # 1: the name part of names that do end in numbers,
        # 2: the number part of names that do end in numbers
        _df = df[name_col].str.extract(r'(.+)[^\d]$|(.+) ([\d+_])$')
        # merge columns 0 and 1 (the name columns)
        mask = _df[0].isna()
        _df.loc[mask, 0] = _df[mask][1]
        # write this merged column to the main name column
        df[name_col] = _df[0]

        # merge repeated names
        # https://stackoverflow.com/a/31521177/5908685
        def weighted_mean(x):
            return np.average(x, weights=df.loc[x.index, length_col])

        grouped = df[[name_col, length_col, 'ROUGHNESS']].groupby(name_col)
        df = grouped.agg({length_col: 'sum', 'ROUGHNESS': weighted_mean})
        df['merged_parts'] = grouped.size()
        df = df.reset_index()

        self.df = df
