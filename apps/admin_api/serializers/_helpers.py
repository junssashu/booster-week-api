def _map_camel_to_snake(data, field_map):
    """Accept camelCase keys from the client and map them to snake_case."""
    mapped = {}
    for key, value in data.items():
        mapped[field_map.get(key, key)] = value
    return mapped
