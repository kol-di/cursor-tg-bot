import pandas as pd
from pandas import ExcelWriter
from io import BytesIO
from datetime import datetime


class ReportBuilder:
    def __init__(self, doc_path, delimiter=";"):
        self._data = pd.read_csv(doc_path, sep=delimiter).convert_dtypes()

        # convert to strings for clear representation in excel
        int_types = self._data.select_dtypes(include=[int])
        self._data[int_types.columns] = int_types.astype(str)

        self.size = self._data.shape[0]

        self.cols = [
            'RegNumber', 
            'ContractStatus', 
            'PublishDate', 
            'URL']

    def __str__(self):
        data_slice = self._data[self.cols].copy()
        return data_slice.to_string(index=False, justify='center')
    
    def get_file(self):
        data_slice = self._data[self.cols]

        b_buf = BytesIO()
        b_buf.name = "Контракты_без_позиций {}.xlsx".format(datetime.now().strftime("%d-%m-%Y %H:%M"))
        writer = ExcelWriter(b_buf, engine='xlsxwriter')
        data_slice.to_excel(writer, sheet_name='Отчет', index=False)
        writer.close()

        b_buf.seek(0)

        return b_buf