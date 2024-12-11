import polars as pl

from pathlib import Path
from thefuzz import process
from llama_index.core.tools import FunctionTool


def load_product_search_tool(
    file_product_path: str | Path, description: str = ""
) -> FunctionTool:
    print(Path(file_product_path).suffix)
    assert Path(file_product_path).suffix == ".xlsx", "Only support xlsx file"
    df_product = pl.read_excel(file_product_path, sheet_name="product")

    product_list = df_product["name"].to_list()

    def product_search(product_name: str) -> str:
        list_product_name_by_fuzzy = process.extract(
            product_name, product_list, limit=3
        )  # [(str, int)]

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

                result_str += f"{index+1}- Sản phẩm: {name}, Giá: {price}, Mô tả: {description}, Link sản phẩm: {url} \n"

        return result_str

    return FunctionTool.from_defaults(
        fn=product_search,
        return_direct=True,
        description=description or "Useful tool for searching product",
    )
