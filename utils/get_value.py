def get_value(data, key, default=None):
    if not data or not key:
        return default
    if not isinstance(data, dict) and not isinstance(data, list):
        return default
    if not isinstance(key, str):
        return default
    key = key.split('.')
    for k in key:
        if k in data and data[k] is not None:
            data = data[k]
        else:
            return default
    return data
