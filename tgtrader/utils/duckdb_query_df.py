# encoding: utf-8

import duckdb
import pandas as pd
from typing import List, Optional, Union, Dict

class DuckDBQueryDF:
    """
    A utility class for querying pandas DataFrames using DuckDB.
    
    This class provides methods to execute SQL queries against pandas DataFrames
    using DuckDB as the query engine. It supports both single DataFrame queries
    and queries involving multiple DataFrames.
    """
    
    def __init__(self, dfs: Optional[Dict[str, pd.DataFrame]] = None) -> None:
        """
        Initialize a new DuckDB connection for DataFrame querying.
        
        Args:
            dfs: Optional dictionary of pandas DataFrames to query. The keys will be used as table names.
        """
        self.con = duckdb.connect(database=':memory:')
        if dfs is not None:
            self.register_multiple(dfs)
    
    def register_multiple(self, dfs: Dict[str, pd.DataFrame]) -> None:
        """
        Register multiple DataFrames as tables for querying.
        
        Args:
            dfs: A dictionary where keys are table names and values are pandas DataFrames.
        """
        for name, df in dfs.items():
            self.con.register(name, df)
    
    def query(self, sql: str) -> pd.DataFrame:
        """
        Execute a SQL query against the registered DataFrame.
        
        Args:
            sql: SQL query string to execute
            
        Returns:
            pd.DataFrame: Result of the SQL query as a pandas DataFrame
            
        Examples:
            >>> df = pd.DataFrame({'a': [1, 2, 3], 'b': ['x', 'y', 'z']})
            >>> dq = DuckDBQueryDF(df)
            >>> result = dq.query("SELECT * FROM df WHERE a > 1")
        """
        return self.con.execute(sql).df()
    
    def close(self) -> None:
        """
        Close the DuckDB connection.
        """
        self.con.close()
    
    def __enter__(self) -> 'DuckDBQueryDF':
        """
        Context manager entry point.
        
        Returns:
            DuckDBQueryDF: Self reference for use in context manager
        """
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """
        Context manager exit point.
        
        Args:
            exc_type: Exception type if an exception occurred
            exc_val: Exception value if an exception occurred
            exc_tb: Exception traceback if an exception occurred
        """
        self.close()
