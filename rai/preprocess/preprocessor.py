from abc import ABC, abstractmethod
import pandas as pd

from rai.defaults import (PROCESSED_NAME_COL, PROCESSED_LENGTH_COL,
                          ENDPOINT_COLS)


class Preprocessor(ABC):
    processed_name_col: str = PROCESSED_NAME_COL
    processed_length_col: str = PROCESSED_LENGTH_COL
    # simple_cases_regex: str = r'^[\s\w]+? - [\s\w]+?$'
    simple_cases_regex: str = r'^(?:(?! - ).)* - (?:(?! - ).)*$'

    def __init__(self, df: pd.DataFrame) -> None:
        self.orig_df = pd.DataFrame(df)
        self.df = df

    def run(self):
        self.add_standardized_columns()
        self.process()
        self.filter_simple_cases()
        self.parse_endpoints()

    @abstractmethod
    def add_standardized_columns(self):
        self.df.loc[:, self.processed_length_col] = self.df[
            self.processed_length_col].astype(float)

    @abstractmethod
    def process(self):
        pass

    def filter_simple_cases(self):
        name_col = self.processed_name_col
        simple_mask = self.df[name_col].str.contains(self.simple_cases_regex)
        self.df = pd.DataFrame(self.df[simple_mask])

    def parse_endpoints(self):
        name_col = self.processed_name_col
        ep1_col, ep2_col = ENDPOINT_COLS
        self.df.loc[:, ep1_col] = [
            p.strip()
            for (p, _) in self.df[name_col].str.split(' - ').to_list()
        ]
        self.df.loc[:, ep2_col] = [
            p.strip()
            for (_, p) in self.df[name_col].str.split(' - ').to_list()
        ]
