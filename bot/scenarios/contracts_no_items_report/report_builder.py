import pandas as pd
from pandas import ExcelWriter
from io import BytesIO


class ReportBuilder:
    cols = [
        'RegNumber', 
        'ContractStatus', 
        'PublishDate', 
        'URL']

    def __init__(self, doc_path, delimiter=";"):
        self._data = pd.read_csv(doc_path, sep=delimiter)
        self.size = self._data.shape[0]

    def __str__(self):
        data_slice = self._data[self.cols].copy()
        int_types = data_slice.select_dtypes(int)
        data_slice[int_types.columns]= int_types.astype(str)
        print(data_slice.dtypes)
        return data_slice.to_string()
    
    def get_file(self):
        data_slice = self._data[self.cols]

        b_buf = BytesIO()
        b_buf.name = "Отчет.xlsx"
        writer = ExcelWriter(b_buf, engine='xlsxwriter')
        data_slice.to_excel(writer, sheet_name='Отчет')
        writer.close()

        b_buf.seek(0)

        # b_buf.write(data_slice.to_csv())
        # b_buf.close()
        return b_buf