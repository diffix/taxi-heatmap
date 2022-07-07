import psycopg2
import sys


class PostgresDB:
    @staticmethod
    def print_psycopg2_exception(err):
        err_type, err_obj, traceback = sys.exc_info()
        line_num = traceback.tb_lineno
        print(f"------------------------------------------------------------\n",
              f"psycopg2 version: {psycopg2.__version__}\n",
              f"psycopg2 ERROR: {err} on line number: {line_num}\n",
              f"psycopg2 traceback: {traceback} -- type: {err_type}\n",
              f"psycopg2 extensions.Diagnostics: {err.diag}\n",
              f"psycopg2 pg_error: {err.pgerror} pg_code: {err.pgcode}\n",
              f"------------------------------------------------------------\n")

    _default_parameters = {
        'port': 5432,
        'user': 'postgres',
        'readonly': False,
    }
    _required_parameters = ['host', 'port', 'dbname', 'user', 'password', 'readonly']

    def __init__(self, parameters):
        self._parameters = PostgresDB._default_parameters.copy()
        for parameter, value in parameters.items():
            if parameter in self._required_parameters:
                self._parameters[parameter] = value
        for parameter in self._required_parameters:
            if parameter not in self._parameters:
                raise ValueError(f"Required parameter {parameter} not provided")
        self._connection = None

    def connect(self):
        if self.is_connected():
            raise ValueError("Cannot connect. Already connected.")
        try:
            self._connection = psycopg2.connect(host=self._parameters['host'],
                                                port=self._parameters['port'],
                                                dbname=self._parameters['dbname'],
                                                user=self._parameters['user'],
                                                password=self._parameters['password'])
        except psycopg2.Error as err:
            PostgresDB.print_psycopg2_exception(err)
            self._connection = None
            raise err

    def disconnect(self):
        if not self.is_connected():
            raise ValueError("Cannot disconnect. Not connected at present.")
        self._connection.close()
        self._connection = None

    def is_connected(self):
        if self._connection is None:
            return False
        if self._connection.closed != 0:
            return False
        return True

    @staticmethod
    def _matchesPrefix(prefix, sql):
        if len(sql) < len(prefix):
            return False
        return sql[:len(prefix)].lower() == prefix.lower()

    def execute_sql(self, sql):
        if not self.is_connected():
            raise ValueError("Cannot execute sql. Not connected at present.")
        if self._parameters['readonly']:
            if not PostgresDB._matchesPrefix('show', sql) and not PostgresDB._matchesPrefix('select', sql):
                raise ValueError("In readonly mode sql must start with show or select")
        try:
            cursor = self._connection.cursor()
            cursor.execute(sql)
            result = cursor.fetchall()
            cursor.close()
            if not self._parameters['readonly']:
                self._connection.commit()
            return result
        except psycopg2.Error as err:
            PostgresDB.print_psycopg2_exception(err)
            if not self._parameters['readonly']:
                self._connection.rollback()
            self.disconnect()
            raise err
