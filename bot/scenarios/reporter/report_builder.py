import pandas as pd
from pandas import ExcelWriter
from io import BytesIO
from datetime import datetime
from dataclasses import dataclass
from typing import List, Optional

from bot.access import ReportType


@dataclass(frozen=True)
class ReportProperties:
    columns: List[int]
    filename_prefix: str


REPORTS_PROPERTIES = {
    ReportType.REC_CONTRACTS_NO_ITEMS: ReportProperties(
        columns=['RegNumber', 'ContractStatus'], 
        filename_prefix="Контракты_без_позиций"), 

    ReportType.REC_ODNOPOZ_ODNOLOT_LS_NO_CONTRACT_223: ReportProperties(
        columns=['RegNumber', 'ContractStatus', 'PublishDate'], 
        filename_prefix="Однопозы_однолоты_ЛС_без_контракта_223"
    )
}



class ReportBuilder:
    def __init__(self, df=Optional[pd.DataFrame]):
        self._data = df

        if df is None:
            self.cols = []
            self.size = 0
        else:
            self.cols = df.columns
            self.size = df.shape[0]

    def __str__(self):
        try:
            data_slice = self._data[self.cols]
        except AttributeError:
            raise Exception("No data for report")
        
        return data_slice.to_string(index=False, justify='center')
    
    def create_file(self, filename_prefix):
        try:
            data_slice = self._data[self.cols]
        except AttributeError:
            raise Exception("No data for report")
        
        b_buf = BytesIO()
        b_buf.name = "{} {}.xlsx".format(filename_prefix, datetime.now().strftime("%d-%m-%Y %H:%M"))
        writer = ExcelWriter(b_buf, engine='xlsxwriter')
        data_slice.to_excel(writer, sheet_name='Отчет', index=False, na_rep='NULL')
        writer.close()

        b_buf.seek(0)

        return b_buf
    
    def read_data(self, doc_path, delimiter=";"):
        self._data = pd.read_csv(doc_path, sep=delimiter).convert_dtypes()
        self.size = self._data.shape[0]

        # convert integers columns to strings for clear representation in excel
        int_types = self._data.select_dtypes(include=[int])
        self._data[int_types.columns] = int_types.astype(str)

    @classmethod
    def from_db(cls, *args, **kwargs):
        data = kwargs.pop('data')
        columns = kwargs.pop('columns')

        df = pd.DataFrame.from_records(data, columns=columns)
        inst = cls(df, *args, **kwargs)

        return inst

