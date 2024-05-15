import datetime
import json

from sqlalchemy import Row


class JSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Row):
            return list(o)
        if isinstance(o, datetime.date):
            return o.isoformat()
        return json.JSONEncoder.default(self, o)
