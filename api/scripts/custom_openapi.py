import yaml

from api.main import app


def transform_anyof(schema):
    """
    Recursively transforms OpenAPI anyOf constructs that contain {'type': 'null'}
    into type: ['T', 'null'] format, preserving all other schema properties.

    The reason for this transformation is that the swift-openapi-generator does not support the following OpenAPI schema:

    >>> anyOf:
    >>>    - $ref: '#/components/schemas/MyObject'
    >>>    - type: 'null'

    Where the swift-openapi-generator expects:

    >>> $ref: '#/components/schemas/MyObject'
    >>> type:
    >>>    - object
    >>>    - 'null'

    It seems that FastAPI, or rather Pydantic, generates the former schema with anyOf. This function transforms it into
    the latter schema. while preserving all other schema properties.

    Also, even the OpenAPI 3.1 does not really mention what's the correct use of declaring null:
    https://github.com/OAI/OpenAPI-Specification/issues/3148
    """
    if isinstance(schema, dict):
        if "anyOf" in schema:
            has_null = any(entry == {"type": "null"} for entry in schema["anyOf"])
            non_null_types = [
                entry for entry in schema["anyOf"] if entry != {"type": "null"}
            ]

            if has_null:
                schema.pop("anyOf")

                schema["type"] = []

                for single_type in non_null_types:
                    if "$ref" in single_type:
                        schema["type"].append("object")
                        schema.update(
                            {
                                **single_type,
                                "$ref": single_type["$ref"],
                                "type": schema["type"],
                            }
                        )
                    elif "items" in single_type and "type" in single_type:
                        schema["type"].append("array")
                        schema.update(
                            {
                                **single_type,
                                "items": single_type["items"],
                                "type": schema["type"],
                            }
                        )
                    elif "type" in single_type:
                        schema["type"].append(single_type["type"])
                        schema.update(
                            {
                                **single_type,
                                "type": schema["type"],
                            }
                        )
                schema["type"].append("null")

        # Recursively process all dictionary values
        for key, value in list(schema.items()):
            schema[key] = transform_anyof(value)

    elif isinstance(schema, list):
        return [transform_anyof(item) for item in schema]

    return schema


def remove_text_event_stream_from_json_response(schema):
    """
    Removes the 'text/event-stream' content type from responses that contain 'application/json' and 'text/event-stream'.
    """
    paths = schema["paths"]

    for path in paths.values():
        for method in path.values():
            for response in method["responses"].values():
                if (
                    "application/json" in response["content"]
                    and "text/event-stream" in response["content"]
                ):
                    response["content"].pop("text/event-stream")

    return schema


if __name__ == "__main__":
    openapi_schema = app.openapi()

    modified_schema = remove_text_event_stream_from_json_response(
        transform_anyof(openapi_schema)
    )

    print(yaml.dump(modified_schema))
