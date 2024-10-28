import sqlite3

class Datastore():
    
    def __init__(self):
        """
        Connect to the database
        """
        
        db_file = "TableTopGamers.db"
        
        self.conn = sqlite3.connect(db_file)
        self.cur = self.conn.cursor()
        
    def __del__(self):
        """
        saves cached data to databse upon close
        """
        self.conn.close()
        
    def display_all_games(self):
        self.cur.execute(
            """
            SELECT *
            FROM games
            """
        )
        
        return self.cur.fetchall()
        
        