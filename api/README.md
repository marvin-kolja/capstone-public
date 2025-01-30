# API

A FastAPI server that provides a RESTful API to interact with the [Core](../core/README.md). As the Core does not have data persistence for parsed data, the server stores data in a SQLite database. This retains data across restarts and allows to access all data from previous operations.

## Table of Contents

<!-- TOC -->
* [API](#api)
  * [Table of Contents](#table-of-contents)
  * [Technologies](#technologies)
    * [Server](#server)
    * [Database](#database)
    * [Async](#async)
  * [Features](#features)
  * [Structure](#structure)
  * [Development](#development)
    * [Prerequisites](#prerequisites)
    * [Quick Start](#quick-start)
    * [Tests & Coverage](#tests--coverage)
      * [Run tests](#run-tests)
      * [Coverage](#coverage)
    * [Migrations](#migrations)
      * [Create Database migration scripts](#create-database-migration-scripts)
      * [Migrate Database](#migrate-database)
    * [Formatting](#formatting)
    * [Logging](#logging)
    * [Generate OpenAPI schema](#generate-openapi-schema)
  * [Contact](#contact)
<!-- TOC -->

## Technologies

There are a few aspects to focus on when looking at the technologies used in the API server.

### Server

`FastAPI` was used as a framework to build a RESTful API and `uvicorn` is used to run the server.

### Database

`SQLModel` is by the same author as `FastAPI` and integrates well with it. It's built on top of `SQLAlchemy` which is used for the database interaction. `Alembic` is used for database migrations.

### Async

`FastAPI` is built on top of the async server framework `Starlette`. Thus, routes and all database sessions are async. Note that currently, the server uses a single worker for handling requests as this server doesn't expect a high load. However, the server would support multiple workers if needed.

> [!NOTE]
> Alembic migrations use a synchronous database connection, thus, we have two different database URLs in the `config.py` file. One for the async database connection and one for the synchronous database connection.

## Features

- ✅ Check Server Status (DB connection and tunnel connect server status)
- ✅ Interact with iOS devices
- ✅ Add Xcode Projects
    - ✅ Build Xcode Projects
        - ✅ Listen for build updates
        - ✅ Get Test Cases
- ✅ Create Test Plans
    - ✅ Add Test Steps
- ✅ Execute Test Plans
    - ✅ Listen for execution updates
    - ✅ Process Trace Results
    - 🚧 Listen for processing updates
- ✅ Data persistence (SQLite)

## Structure

```
/api
|-- /api
|   |-- /alembic            # Migration scripts using Alembic
|   |-- /routes             # FastAPI routes
|   |-- /services           # Main business logic (Interaction with DB and Core)
|   |-- async_jobs.py       # Async background jobs
|   |-- config.py           # Server settings (parses .env)
|   |-- custom_responses.py # Custom responses for FastAPI
|   |-- db.py               # Database engine and session maker
|   |-- depends.py          # Dependency injection for FastAPI routes
|   |-- log_config.py       # Logging configuration
|   |-- main.py             # Server entry point
|   |-- models.py           # SQLModel models (DB) and request/response models
|
|-- /scripts/               # Scripts (for migration, running the server, testing and openapi generation) 
|-- /tests/                 # Tests for the API server (pytest)
```

## Development

### Prerequisites

| Technology | Version | Description                   |
|------------|---------|-------------------------------|
| Poetry     | 1.8     | Dependency management.        |
| Python     | 3.13+   | API was developed using 3.13. |

> [!CAUTION]
> Check out the [Core README](../core/README.md#prerequisites) for its prerequisites

### Quick Start

1. Creat environment:
   ```sh
   poetry env use python3.13
   ```

2. Activate environment:
   ```sh
    poetry shell
    ```

3. Install dependencies:
    ```sh
    poetry install
    ```

4. Create .env

Create a `.env` file in the root directory of the API server with the following environment variables (replace as needed):

    ```env
    PROJECT_NAME=CORE API
    TUNNEL_CONNECT_PORT=49151
    API_PORT=8000
    ENVIRONMENT=production
    SQLITE_PATH=db.sqlite3
    BUILD_DIR=<path_to_store_xcode_builds>
    TEST_SESSIONS_DIR=<path_to_store_test_session_data>
    ```

5. Run the server

```sh
sh scripts/run.sh
```

6. Run tunnel connect server

```sh
sudo python3 -m core.tunnel.server_executable --port <port> # Use port as specified in .env (TUNNEL_CONNECT_PORT)
```

8. Get health status

```bash
curl http://127.0.0.1:8000/health # Use port as specified in .env (API_PORT)
# {"status":"ok","db":"ok","tunnel_connect":"ok"}
```

### Tests & Coverage

The api server uses `pytest` for testing and `coverage` for code coverage.

#### Run tests

The test script creates a new SQLite database (`test.db.sqlite3`), runs migrations and then runs tests. If tests fail the database is not deleted, allowing you to inspect the database for debugging purposes.

```sh
sh scripts/test.sh
```

**Options:**

- Any pytest options can be passed to the script (e.g. `sh scripts/test.sh -k test_name` to run tests with `test_name` in the name).

#### Coverage

To generate a coverage report, run the following command:

```sh
coverage report -m
```

### Migrations

#### Create Database migration scripts

Whenever database models are changed, there needs to be a new migration script created. To create a new migration script, run the following command:

```sh
sh scripts/gen_migration.sh "Name of migration"
```

This will create a new migration script in the `api/alembic/versions` directory. The script will be named with the current timestamp and the name provided.

#### Migrate Database

> [!IMPORTANT]
> The server and tests automatically migrate the database to the latest version. If you need to manually migrate the database, run the following command.

```sh
SQLITE_PATH="path_to_db.sqlite3" sh scripts/migrate.sh
```

### Formatting

The api server uses `black` for code formatting. Simply run the following command to format the code:

```sh
black .
```

### Logging

The api server uses the `logging` module for logging and configures the logger in `log_config.py`. It logs uvicorn logs to stdout and to files. All other logs are currently only logged to stdout.

To log messages, use the following code snippet:

```python
import logging

logger = logging.getLogger(__name__)

logger.debug("Debug message")
```

### Generate OpenAPI schema

In order to generate an OpenAPI schema for the macOS app to use to generate an API client, run the following command:

```sh
sh scripts/gen_openapi.sh
```

> [!TIP]
> If you don't want to generate for the macOS app, you can call `python3 scripts/custom_openapi.py` to generate and print it to stdout.

## Contact

Marvin Kolja Willms - [marvin.willms@code.berlin](mailto:marvin.willms@code.berlin)
