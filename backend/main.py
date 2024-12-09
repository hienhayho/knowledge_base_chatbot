import pandas as pd
from src.readers import (
    PandasCSVReaderCustomised,
)  # noqa


parser = (
    PandasCSVReaderCustomised(
        pandas_config=dict(on_bad_lines="skip"), concat_rows=True, top_k=100
    ),
)

df = pd.read_csv("/Users/hienht/Downloads/quangnhatexcel.csv")
print(df)


# print(parser[0].load_data("/Users/hienht/Downloads/quangnhatexcel.csv"))
