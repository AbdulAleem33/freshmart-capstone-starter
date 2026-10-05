"""Load and validate the four FreshMart files."""
from pathlib import Path
import pandas as pd
REQUIRED = {
    "sales_2025.csv": ["receipt_id", "store_id", "product_id", "sale_date", "qty", "unit_price", "discount_pct"],
    "products.csv": ["product_id", "product_name", "category", "unit_price", "cost_price", "is_perishable"],
    "stores.csv": ["store_id", "store_name", "city", "opened_on", "floor_area_sqft"],
    "promotions.csv": ["promo_id", "product_id", "store_id", "start_date", "end_date", "discount_pct"],
}
class DataFileError(Exception):
    """A required file is missing or unreadable."""
class SchemaError(Exception):
    """A file is missing required columns."""
class SalesLoader:
    """Reads the four CSVs from a folder and validates their columns."""
    def __init__(self, folder):
        self.folder = Path(folder)
        # TODO: raise DataFileError if the folder does not exist
        if not self.folder.exists():
            raise DataFileError(
                f"Data folder does not exist: {self.folder}"
            )
        # Check whether path is actually a directory
        if not self.folder.is_dir():
            raise DataFileError(
                f"Data path is not a folder: {self.folder}"
            )
    def _read(self, name):
        # TODO: raise DataFileError if the file is missing
        df = pd.read_csv(self.folder / name)
        path = self.folder / name
        # TODO: raise SchemaError listing any missing REQUIRED columns
        if not path.exists():
            raise DataFileError(
                f"Required file is missing: {path}"
            )
        # Check file can be read
        try:
            df = pd.read_csv(path)
        except Exception as exc:
            raise DataFileError(
                f"Could not read file: {path}"
            ) from exc
        # Check required columns
        required_columns = REQUIRED[name]
        missing_columns = [
            column
            for column in required_columns
            if column not in df.columns
        ]
        if missing_columns:
            raise SchemaError(
                f"{name} is missing required columns: "
                f"{missing_columns}"
            )
        return df
    def load_all(self):
        return {name.split(".")[0].replace("_2025", ""): self._read(name) for name in REQUIRED}
    def stream_sales(self, chunksize=5000):
        """Generator: yield the sales file chunk by chunk (pd.read_csv(..., chunksize=))."""
        # TODO
        path = self.folder / "sales_2025.csv"
        if not path.exists():
            raise DataFileError(
                f"Required file is missing: {path}"
            )
        try:
            # Validate the header first
            header = pd.read_csv(
                path,
                nrows=0
            )
            missing_columns = [
                column
                for column in REQUIRED["sales_2025.csv"]
                if column not in header.columns
            ]
            if missing_columns:
                raise SchemaError(
                    "sales_2025.csv is missing required columns: "
                    f"{missing_columns}"
                )
            # Yield chunks
            for chunk in pd.read_csv(
                path,
                chunksize=chunksize
            ):
                yield chunk
        except (SchemaError, DataFileError):
            raise
        except Exception as exc:
            raise DataFileError(
                f"Could not read sales file: {path}"
            ) from exc
        
