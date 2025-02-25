""" An api I made to read and write to DBs using SQLite3 """
from typing import Any
import sqlite3
import os
import time


class MySQLiteApi:

    def __init__(self, db_path: str):
        self.db_path = db_path
        self.db_location = os.path.dirname( db_path )


    def add_data(self, data: list[dict[str, Any]], table: str):
        """ Given a list of dicts, add them to table in db """
        if len(data) == 0:
            return

        headers = tuple(data[0].keys())
        rows = [ tuple([ row[header] for header in headers ]) for row in data ]

        headers_str = ', '.join(headers)
        placeholders_str = ', '.join( ['?']*len(headers) )

        with sqlite3.connect(self.db_path) as conn:
            conn.executemany(
                f''' INSERT OR IGNORE INTO {table} ({headers_str}) VALUES ({placeholders_str}) ''',
                rows
            )



    def select(self, columns: list[str], table: str, quiet: bool=True) -> list[dict[str, Any]]:
        """ Select data from table. Get list of dicts. """
        columns_str = ", ".join(columns)
        if columns == []:
            columns_str = '*'

        start = time.time()

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(f'''
                SELECT {columns_str} FROM {table}
            ''')
            data = cursor.fetchall()
            if columns == []: # ??
                columns = [ description[0] for description in cursor.description ]
        results = [ { columns[i]: row[i] for i in range(len(columns)) } for row in data  ]

        if not quiet:
            print('Loaded {:_} results in {:.2f}s'.format(len(results), time.time()-start))
        return results



    def select_where(self, columns: list[str], table: str, where_condition: str, where_param: str) -> list[dict[str, Any]]:
        """ Select data from table with one where condition. Get list of dicts. """
        columns_str = ", ".join(columns)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(f'''
                SELECT {columns_str} FROM {table} 
                WHERE {where_condition} ?
            ''', (where_param,))
            data = cursor.fetchall()

        return [ { columns[i]: row[i] for i in range(len(columns)) } for row in data  ]

    

    def select_single_column(self, column_name: str, table: str) -> list[Any]:
        """ Get single column from table. """
        conn = sqlite3.connect(self.db_path)
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(f'''
                SELECT {column_name} FROM {table}
            ''')
            data = cursor.fetchall()

        return [ row[0] for row in data ]
    


    def update_row(self, update_dict: dict[str, Any], table: str, where_condition: str, where_param: str):
        """ Update row(s) with values from update_dict """
        col_strs = [ f"{col} = COALESCE(?, {col})" for col in update_dict.keys() ]
        set_string = "{}".format( ', '.join(col_strs) )

        data_array = list(update_dict.values())
        data_array.append(where_param)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            try:
                cursor.execute(f'''
                    UPDATE {table}
                    SET {set_string}
                    WHERE {where_condition} ?
                ''', data_array)
                conn.commit()
            except Exception as e:
                print("[ERROR] MySqlApi.update_row()")
                print(e)
    


    def delete_row(self, table: str, column_name: str, param: str):
        """  """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(f'''
                DELETE FROM {table}
                WHERE {column_name} = ?
            ''', (param,))
            conn.commit()
            return True



    # TODO: Update / remove
    def create_tables(self):
        """  """
        if not os.path.exists(self.db_location):
            print("Creating directory for db:", self.db_location)
            os.makedirs(self.db_location)
            
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS videos
            (
                video_id INTEGER PRIMARY KEY,
                hash TEXT UNIQUE,
                path TEXT UNIQUE,
                filename TEXT,
                sort_performer TEXT,
                studio TEXT,
                line TEXT,
                scene_title TEXT,
                duration TEXT,
                duration_seconds REAL,
                resolution INT,
                bitrate INT,
                filesize_mb REAL,
                fps REAL,
                suffix TEXT NOT NULL,
                date_downloaded TEXT,
                release_date TEXT,
                year INT,
                mention_performer TEXT,
                other_info TEXT,
                scene_id TEXT,
                path_url TEXT UNIQUE,
                filedir TEXT,
                preview_url TEXT UNIQUE,
                data18_url TEXT,
                FOREIGN KEY(scene_id) REFERENCES scenes(scene_id)
            )
        ''')
        conn.commit()
        cursor.close()
        conn.close()



