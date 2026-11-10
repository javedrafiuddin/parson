"""DuckDB access to the four point-in-time tables (Section 8.1). Views over Parquet shards."""
import duckdb
from .config import PIT, PRICES, DERIVED


def connect():
    c = duckdb.connect()
    c.execute("PRAGMA threads=4; PRAGMA memory_limit='10GB'")
    v = {
        "prices": f"read_parquet('{PRICES}/*/part-*.parquet', union_by_name=true)",
        "splits": f"read_parquet('{PRICES}/*/splits-*.parquet', union_by_name=true)",
        "price_meta": f"read_parquet('{PRICES}/*/meta-*.parquet', union_by_name=true)",
        "facts": f"read_parquet('{PIT}/facts/*.parquet')",
        "filings": f"read_parquet('{PIT}/filings/*.parquet')",
        "entities": f"read_parquet('{PIT}/entities/*.parquet')",
    }
    for k, q in v.items():
        try:
            c.execute(f"CREATE VIEW {k} AS SELECT * FROM {q}")
        except Exception as e:  # table not built yet
            pass
    for name in ("instrument_terms", "catalyst_calendar"):
        f = DERIVED / f"{name}.parquet"
        if f.exists():
            c.execute(f"CREATE VIEW {name} AS SELECT * FROM '{f}'")
    return c
