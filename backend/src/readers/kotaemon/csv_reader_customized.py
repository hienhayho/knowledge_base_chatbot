import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent))
from typing import Any, Dict, List, Optional

import pandas as pd
from fsspec import AbstractFileSystem
from llama_index.core.readers.base import BaseReader
from llama_index.core.schema import Document

from src.utils import get_formatted_logger

logger = get_formatted_logger(__file__)


class CSVReaderCustomised(BaseReader):
    """CSV parser.

    Args:
        concat_rows (bool): whether to concatenate all rows into one document.
            If set to False, a Document will be created for each row.
            True by default.

    """

    def __init__(self, *args: Any, concat_rows: bool = True, **kwargs: Any) -> None:
        """Init params."""
        super().__init__(*args, **kwargs)
        self._concat_rows = concat_rows

    def load_data(
        self, file: Path, extra_info: Optional[Dict] = None
    ) -> List[Document]:
        """Parse file.

        Returns:
            Union[str, List[str]]: a string or a List of strings.

        """
        try:
            import csv
        except ImportError:
            raise ImportError("csv module is required to read CSV files.")
        text_list = []
        with open(file) as fp:
            csv_reader = csv.reader(fp)
            for row in csv_reader:
                text_list.append(", ".join(row))

        metadata = {"filename": file.name, "extension": file.suffix}
        if extra_info:
            metadata = {**metadata, **extra_info}

        if self._concat_rows:
            return [Document(text="\n".join(text_list), metadata=metadata)]
        else:
            return [Document(text=text, metadata=metadata) for text in text_list]


class PandasCSVReaderCustomised(BaseReader):
    r"""Pandas-based CSV parser.

    Parses CSVs using the separator detection from Pandas `read_csv`function.
    If special parameters are required, use the `pandas_config` dict.

    Args:
        concat_rows (bool): whether to concatenate all rows into one document.
            If set to False, a Document will be created for each row.
            True by default.

        col_joiner (str): Separator to use for joining cols per row.
            Set to ", " by default.

        row_joiner (str): Separator to use for joining each row.
            Only used when `concat_rows=True`.
            Set to "\n" by default.

        pandas_config (dict): Options for the `pandas.read_csv` function call.
            Refer to https://pandas.pydata.org/docs/reference/api/pandas.read_csv.html
            for more information.
            Set to empty dict by default, this means pandas will try to figure
            out the separators, table head, etc. on its own.

    """

    def __init__(
        self,
        *args: Any,
        top_k: int = 100,
        concat_rows: bool = False,
        col_joiner: str = ", ",
        row_joiner: str = "\n",
        pandas_config: dict = {},
        **kwargs: Any,
    ) -> None:
        """Init params."""
        super().__init__(*args, **kwargs)
        self._concat_rows = concat_rows
        self._col_joiner = col_joiner
        self._row_joiner = row_joiner
        self._pandas_config = pandas_config
        self._top_k = top_k

    def load_data(
        self,
        file: Path,
        extra_info: Optional[Dict] = None,
        fs: Optional[AbstractFileSystem] = None,
    ) -> List[Document]:
        """Parse file."""
        if fs:
            with fs.open(file) as f:
                df = pd.read_csv(f, **self._pandas_config)
        else:
            df = pd.read_csv(file, **self._pandas_config)

        # Chuyển toàn bộ hàng thành danh sách văn bản
        text_list = df.apply(
            lambda row: " ".join([f"{k}: {v}" for k, v in row.to_dict().items()]),
            axis=1,
        ).tolist()

        # Chia danh sách các hàng thành các nhóm con theo top_k
        def chunk_list(lst, k):
            """Chia danh sách lst thành các nhóm nhỏ mỗi nhóm có tối đa k phần tử."""
            return [lst[i : i + k] for i in range(0, len(lst), k)]

        text_list = chunk_list(text_list, self._top_k or len(text_list))
        logger.info(
            f"Chunked {file} with shape {df.shape} into {len(text_list)} parts. with top_k={self._top_k}"
        )

        result = [
            Document(text=(self._row_joiner).join(sub_list), metadata=extra_info or {})
            for sub_list in text_list
        ]
        print(result)
        logger.info(f"Length of result: {len(result)}")
        return result
        # Kết quả: nếu self._concat_rows=True thì join tất cả nhóm lại
        # if self._concat_rows:
        #     result = [
        #         Document(
        #             text=(self._row_joiner).join(
        #                 [item for sublist in text_list for item in sublist]
        #             ),
        #             metadata=extra_info or {},
        #         )
        #     ]
        #     logger.info(f"Length of result: {len(result)}")
        #     return result
        # else:
        #     return [
        #         Document(text=text, metadata=extra_info or {})
        #         for sublist in text_list
        #         for text in sublist
        #     ]
