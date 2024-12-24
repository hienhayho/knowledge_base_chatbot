import sys
import polars as pl

from pathlib import Path
from thefuzz import process
from llama_index.core.tools import FunctionTool

sys.path.append(str(Path(__file__).parent.parent.parent))
from src.utils import get_formatted_logger

logger = get_formatted_logger(
    __file__, file_path="logs/llama_index_tools/product_search_tool.log"
)


def load_product_search_tool(
    file_product_path: str | Path, description: str = ""
) -> FunctionTool:
    assert Path(file_product_path).suffix == ".xlsx", "Only support xlsx file"

    # Only read sheet "product"
    df_product = pl.read_excel(file_product_path, sheet_name="product")

    product_list = df_product["name"].to_list()

    def product_search(product_name: str) -> str:
        logger.debug(f"Searching for product: {product_name}")

        list_product_name_by_fuzzy = process.extract(
            product_name, product_list, limit=3
        )

        result_str = f"Một số sản phẩm liên quan đến {product_name} gồm: \n"

        for index, product_name_by_fuzzy in enumerate(list_product_name_by_fuzzy):
            product_name_by_fuzzy = product_name_by_fuzzy[0]
            product_info = df_product.filter(
                df_product["name"] == product_name_by_fuzzy
            )

            if product_info.height > 0:
                name = product_info["name"].to_list()[0]
                price = product_info["price"].to_list()[0]
                description = product_info["description"].to_list()[0]
                url = product_info["url"].to_list()[0]
                image_urls = product_info["image_urls"].to_list()[0]
                code = product_info["code"].to_list()[0]

                result_str += f"{index+1}- Sản phẩm: {name}, Giá: {price}, Mô tả: {description}, Link sản phẩm: {url}, Mã sản phẩm: {code}, Hình ảnh: {image_urls}\n"

        logger.debug(f"Result: {result_str}")
        logger.debug(f"\n {'=' * 100} \n")

        return result_str

    return FunctionTool.from_defaults(
        fn=product_search,
        return_direct=True,
        description=description or "Useful tool for searching product",
    )
