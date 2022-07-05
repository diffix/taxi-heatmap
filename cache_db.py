import hashlib
import os
import pickle
import shutil
from postgres_db import PostgresDB


class CacheDB:
    _default_parameters = {
        'mem_cache': True,
        'disk_cache': True,
        'disk_cache_dir_path': '_cache',
    }
    _required_parameters = ['host', 'port', 'dbname', 'user', 'mem_cache', 'disk_cache', 'disk_cache_dir_path']

    def __init__(self, parameters):
        self._parameters = CacheDB._default_parameters.copy()
        for parameter, value in parameters.items():
            if parameter in self._required_parameters:
                self._parameters[parameter] = value
        for parameter in self._required_parameters:
            if parameter not in self._parameters:
                raise ValueError(f"Required parameter {parameter} not provided")
        self._postgres_db = PostgresDB(parameters)
        self._mem_cache = dict()
        self._cache_dir = os.path.join(self._parameters['disk_cache_dir_path'], f"{self._parameters['host']}." +
                                                                                f"{self._parameters['port']}." +
                                                                                f"{self._parameters['dbname']}" +
                                                                                f"{self._parameters['user']}")

    def mem_cache_put(self, hash_key, dict_value):
        if not self._parameters['mem_cache']:
            return
        self._mem_cache[hash_key] = dict_value

    def mem_cache_get(self, hash_key):
        if not self._parameters['mem_cache']:
            return None
        if hash_key not in self._mem_cache:
            return None
        return self._mem_cache[hash_key]

    def mem_cache_flush(self):
        if not self._parameters['mem_cache']:
            if self._mem_cache:
                print(f"CacheDB WARNING: flush() called on disabled mem_cache with actual cache content.")
            return
        self._mem_cache.clear()

    def disk_cache_put(self, hash_key, dict_value):
        if not self._parameters['disk_cache']:
            return
        if not os.path.isdir(self._cache_dir):
            os.makedirs(self._cache_dir)
        cache_file_path = os.path.join(self._cache_dir, f"{hash_key}.pickle")
        with open(cache_file_path, 'wb') as out_file:
            out_file.truncate()
            pickle.dump(dict_value, out_file)

    def disk_cache_get(self, hash_key):
        if not self._parameters['disk_cache']:
            return None
        cache_file_path = os.path.join(self._cache_dir, f"{hash_key}.pickle")
        if not os.path.isfile(cache_file_path):
            return None
        with open(cache_file_path, 'rb') as in_file:
            return pickle.load(in_file)

    def disk_cache_flush(self):
        if not self._parameters['disk_cache']:
            if os.path.isdir(self._cache_dir) and \
                    os.listdir(self._cache_dir):
                print(f"CacheDB WARNING: flush() called on disabled disk_cache with actual cache content.")
            return
        if os.path.isdir(self._cache_dir):
            shutil.rmtree(self._cache_dir)

    def cache_put(self, sql, result):
        hash_key = hashlib.sha1(sql.encode('utf-8')).hexdigest()
        dict_value = {
            'sql': sql,
            'result': result
        }
        self.mem_cache_put(hash_key, dict_value)
        self.disk_cache_put(hash_key, dict_value)

    def cache_get(self, sql):
        hash_key = hashlib.sha1(sql.encode('utf-8')).hexdigest()
        dict_value = self.mem_cache_get(hash_key)
        if dict_value is None:
            dict_value = self.disk_cache_get(hash_key)
            if dict_value is not None:
                self.mem_cache_put(hash_key, dict_value)
        if dict_value is None:
            return None
        if 'sql' not in dict_value or 'result' not in dict_value:
            raise ValueError("Cached values should always contain keys sql and result.")
        if dict_value['sql'] != sql:
            raise ValueError(f"There should be no hash collision between >>{dict_value['sql']}<< and >>{sql}<<.")
        return dict_value['result']

    def cache_flush(self):
        self.mem_cache_flush()
        self.disk_cache_flush()

    def connect(self):
        self._postgres_db.connect()

    def disconnect(self):
        self._postgres_db.disconnect()

    def is_connected(self):
        return self._postgres_db.is_connected()

    def execute_sql(self, sql, prevent_caching=False):
        result = None
        if not prevent_caching:
            result = self.cache_get(sql)
        if result is not None:
            return result
        if not self.is_connected():
            self.connect()
        result = self._postgres_db.execute_sql(sql)
        if not prevent_caching:
            self.cache_put(sql, result)
        return result
