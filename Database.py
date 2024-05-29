import mysql.connector

class Database:
    instance = None

    @staticmethod
    def get_instance():
        if Database.instance is None:
            Database.instance = Database()
        return Database.instance

    def __init__(self):
        try:
            self.connection = mysql.connector.connect(
                host="localhost",
                user="root",
                password="",
                database="smart_parking"
            )
            print("Connected to database.")
        except mysql.connector.Error as e:
            print(f"Error connecting to database: {e}")
            exit(1)
        self.cursor = self.connection.cursor(dictionary=True)

    def query(self, sql, params=None, fetch_results=True):
        result = None
        try:
            self.cursor.execute(sql, params)
            if fetch_results:
                result = self.cursor.fetchall()
            self.connection.commit()
        except Exception as e:
            print(f"Error executing query: {e}")
            result = None
        return result

    def __del__(self):
        self.connection.close()
