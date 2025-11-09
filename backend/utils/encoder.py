# -*- coding:utf-8 -*-
from backend.models.base_model import Model
import json
from datetime import date, datetime
from decimal import Decimal


def custom_json_default(obj):
    if isinstance(obj, Model):
        dikt = {}
        for attr in obj.openapi_types:
            value = getattr(obj, attr)
            if value is None and not getattr(custom_json_default, 'include_nulls', False):
                continue
            attr = obj.attribute_map[attr]
            dikt[attr] = value
        return dikt
    elif isinstance(obj, (datetime, date)):
        return obj.isoformat()
    elif isinstance(obj, Decimal):
        return float(obj)
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")


# 可选：封装一个 dumps 函数
def dumps(obj, **kwargs):
    return json.dumps(obj, default=custom_json_default, **kwargs)