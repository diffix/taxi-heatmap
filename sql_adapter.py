from cache_db import CacheDB


class SQLAdapter:
    _default_parameters = {
        'anonDB': None,
        'rawDB': None,
    }
    _required_parameters = ['anonDB', 'rawDB']

    def __init__(self, parameters):
        self._parameters = SQLAdapter._default_parameters.copy()
        for parameter, value in parameters.items():
            if parameter in self._required_parameters:
                self._parameters[parameter] = value
        for parameter in self._required_parameters:
            if parameter not in self._parameters:
                raise ValueError(f"Required parameter {parameter} not provided")
        self._anon_db = CacheDB(parameters['anonDB']) if parameters['anonDB'] is not None else None
        self._raw_db = CacheDB(parameters['rawDB']) if parameters['rawDB'] is not None else None

    def queryRaw(self, sql):
        if self._raw_db is None:
            raise ValueError("RawDB not configured")
        return self._raw_db.execute_sql(sql)

    def queryDiffix(self, sql):
        if self._anon_db is None:
            raise ValueError("AnonDB not configured")
        return self._anon_db.execute_sql(sql)

    def disconnect(self):
        if self._raw_db is not None and self._raw_db.is_connected():
            self._raw_db.disconnect()
        if self._anon_db is not None and self._anon_db.is_connected():
            self._anon_db.disconnect()
