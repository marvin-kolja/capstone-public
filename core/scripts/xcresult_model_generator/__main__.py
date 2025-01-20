"""
Generates Pydantic models from JSON schemas exported from xcresulttool.

In order to retrieve the JSON schemas from xcresulttool, run e.g. the following command:

```bash
xcresulttool get test-results summary --help
```

This will show you the JSON schema which you can then save to a file a JSON file in the `schemas` directory. The file
name of the json file should be the name of the schema using snake_case. E.g. `build_results.json` for the schema
`BuildResults`.

Before generating the models, the JSON schemas are restructured to a more standard JSON schema structure.
"""

import json
import logging
import pathlib

from datamodel_code_generator import InputFileType, generate
from datamodel_code_generator import DataModelType

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def restructure_schema(schema_title: str, input_schema: str) -> str:
    """
    The exported JSON schema from xcresulttool have a weird schema structure.

    This function restructures the schema to a more standard JSON schema structure.
    """

    input_data = json.loads(input_schema)

    new_schema = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "title": schema_title,
        "type": "object",
        "properties": {},
        "required": [],
        "$defs": {},
    }

    if schema_title not in input_data["schemas"]:
        raise KeyError(f"Schema {schema_title} not found in input data.")

    for schema_name, schema_details in input_data["schemas"].items():
        # Update internal $refs in each definition to point to $defs instead of schemas
        def update_refs(obj):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    if key == "$ref":
                        obj[key] = value.replace("#/schemas/", "#/$defs/")
                    else:
                        update_refs(value)
            elif isinstance(obj, list):
                for item in obj:
                    update_refs(item)

        update_refs(schema_details)

        if schema_name != schema_title:
            new_schema["$defs"][schema_name] = schema_details
        else:
            new_schema["properties"] = schema_details.get("properties", {})
            new_schema["required"] = schema_details.get("required", [])

    return json.dumps(new_schema, indent=4)


def generate_model(
    input_file: pathlib.Path,
    output_file: pathlib.Path,
):
    logger.info(f"Generating model for {input_file} to {output_file}")

    output_file.parent.mkdir(exist_ok=True, parents=True)
    logger.debug(f"Output directory created: {output_file.parent}")

    with open(input_file, "r") as file:
        json_schema = file.read()

        stem_parts = input_file.stem.split("_")
        schema_name = "".join([part.capitalize() for part in stem_parts])

        restructured_json_schema = restructure_schema(schema_name, json_schema)

        generate(
            restructured_json_schema,
            input_file_type=InputFileType.JsonSchema,
            input_filename=input_file.relative_to(
                pathlib.Path(__file__).parent.parent.parent.parent
            ).as_posix(),
            output=output_file,
            output_model_type=DataModelType.PydanticV2BaseModel,
            snake_case_field=True,
        )
        logger.info(f"Model generated: {output_file}")


def retrieve_json_files(path: pathlib.Path) -> list[pathlib.Path]:
    logger.info(f"Retrieving JSON files from {path}")
    files = list(path.rglob("*.json"))
    logger.info(f"Found {len(files)} JSON files")
    return files


def get_schemas_from_json_file(file: pathlib.Path) -> dict[str, dict]:
    logger.info(f"Retrieving JSON schemas from {file}")

    with open(file, "r") as f:
        data = json.load(f)
        schemas = data.get("schemas", {})
        logger.info(f"Found {len(schemas)} schemas in {file}")
        return schemas


def main():
    current_path = pathlib.Path(__file__).parent
    logger.info(f"Current path: {current_path}")
    input_directory = pathlib.Path(current_path, "schemas")
    output_directory = pathlib.Path(
        current_path, "..", "..", "core", "xc", "xcresult", "models"
    ).resolve()

    for schema_file in retrieve_json_files(input_directory):
        relative_schema_path = schema_file.relative_to(input_directory)
        output_file = output_directory / relative_schema_path.with_suffix(".py")
        try:
            generate_model(schema_file, output_file)
        except Exception as e:
            logger.error(f"Failed to generate model for {schema_file}: {e}")
            raise


if __name__ == "__main__":
    main()
