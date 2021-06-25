from rai.preprocess.preprocessor import Preprocessor

NAME_COL = 'Descripción_Tramo'
LENGTH_COL = 'Longitud'


class GuatemalaPreprocessor(Preprocessor):
    def add_standardized_columns(self):
        self.df.loc[:, self.processed_name_col] = self.df[NAME_COL]
        self.df.loc[:, self.processed_length_col] = self.df[LENGTH_COL]
        super().add_standardized_columns()

    def process(self):
        name_col = self.processed_name_col
        self.df.loc[:, name_col] = self.df[name_col].str.replace(
            'bif.', 'bifurcacion', case=False, regex=False)
        self.df.loc[:, name_col] = self.df[name_col].str.replace(
            'bif ', 'bifurcacion ', case=False, regex=False)
        self.df.loc[:, name_col] = self.df[name_col].str.replace(
            'fca.', 'finca', case=False, regex=False)
        self.df.loc[:, name_col] = self.df[name_col].str.replace(
            'fca ', 'finca ', case=False, regex=False)
        self.df.loc[:, name_col] = self.df[name_col].str.replace(
            r' -(\w)', r' \1', case=False, regex=True)
