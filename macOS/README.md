# macOS Client

A SwiftUI macOS app that provides a graphical user interface to interact with the API. It allows users to add Xcode projects, build them from source, configure test plans, and execute them on physical iOS devices. The app also allows users to view the results of the tests and metrics collected in a basic UI. It also allows to access the raw data files generated and export test session data to a JSON file.

## Table of Contents

<!-- TOC -->

* [macOS Client](#macos-client)
    * [Table of Contents](#table-of-contents)
    * [Features](#features)
    * [Structure](#structure)
    * [Development](#development)
        * [Prerequisites](#prerequisites)
        * [Setup](#setup)
        * [Run Schemes](#run-schemes)
        * [Data Stores](#data-stores)
        * [Previews](#previews)
        * [Formatting](#formatting)
        * [Error handling](#error-handling)
        * [Tests](#tests)
    * [Distribution](#distribution)
        * [Archive](#archive)
        * [Export and create `.dmg` file](#export-and-create-dmg-file)
        * [Notarize](#notarize)
    * [Contact](#contact)

<!-- TOC -->

## Features

- ✅ Xcode projects window.
    - ✅ Add Xcode projects.
    - ✅ List Xcode projects.
- ✅ Xcode project specific window.
    - ✅ Xcode Builds
        - ✅ List builds
        - ✅ Build/Rebuild Xcode project
        - ✅ Get XCTest cases
    - ✅ Device management
        - ✅ List devices
        - ✅ Actions (pair, mount DDI, enable developer mode, establish trusted tunnel)
    - ✅ Test plans
        - ✅ Add test plan
        - ✅ List test plans
        - ✅ Edit test plan
        - ✅ Delete test plan
    - ✅ Test sessions
        - ✅ Execute test plan
        - ✅ Cancel test session
        - ✅ View Results
        - ✅ Process Results
        - ✅ Export Session Data to JSON
- 🚧 Error toasts

## Structure

```
/macos
|-- /Client
|   |-- /Client
|   |   |-- /Views                          # Main views of the app
|   |   |-- /Stores                         # Data stores to manage state throughout the app
|   |   |-- /Services                       # currently just APIClient
|   |   |-- /Modifier                       # Custom SwiftUI View modifiers
|   |   |-- /Model                          # Data models
|   |   |-- /Mocks                          # Mock APIClient and response data for previews and testing
|   |   |-- /Extensions                     # Swift extensions
|   |   |-- /Erros                          # Custom error types
|   |   |-- /DeviceModels.swift             # Mapping of device models to their respective device names
|   |   |-- /Components                     # SwiftUI Views that are used in multiple places
|   |   |-- /ClientApp.swift                # App entry point
|   |   |-- /openapi-generator-config.yaml  # OpenAPI generator configuration file
|   |   |-- /openapi.yaml                   # OpenAPI schema of the API
|   |
|   |-- /Scripts                            # Scripts to build app and generate device models mapping
```

## Development

### Prerequisites

| Prerequisite                                                 | Version | Description                                                                                          |
|--------------------------------------------------------------|---------|------------------------------------------------------------------------------------------------------|
| macOS                                                        | 14.0+   | Minimum supported version of app                                                                     |
| Xcode                                                        | 15.0+   | Required as min macOS version of app is 14 and Xcode 15 is the first to add support for that version |
| Swift                                                        | 5+      | Swift version used in project                                                                        |
| swift-format                                                 | -       | Required to install if not using Xcode 16 (which bundles swift-format)                               |
| ([`create-dmg`](https://github.com/sindresorhus/create-dmg)) | -       | Only required to create `.dmg` file for [distribution](#Distribution).                               |

### Setup

> [!WARNING]
> **Unique Bundle Identifier & Team**
> If you're not part of the developer team specified in the projects' `Signing & Capabilities` settings, you'll need to change the `Bundle Identifier` and `Team` of the targets.

1. Open the `macos/Client/Client.xcodeproj` file in Xcode.
2. Make sure that the package dependencies are installed by checking "Package Dependencies" tab in the Xcode project settings.
3. Build the application `Cmd + B`. This will generate an openapi client and data structs from the `openapi.yaml` file. *Every time you change the openapi.yaml file, you need to build the app again.*

### Run Schemes

There are two schemes in the project that you can use to build the app.

| Scheme      | Description                                                                                                                                                                                                                                           |
|-------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Development | This scheme will build the app and use a Mock API client to simulate API responses. This is useful if you want to test the app without running the API server.                                                                                        |
| Production  | This scheme will build the app and use the actual API client to interact with the API server. This is useful when you want to test the app with the actual API server. *Please refer to the [API README](../api/README.md) on how to run the server.* |

### Data Stores

The app uses stores to manage the data heavy state of the app. The stores are injected into the views using the `@EnvironmentObject` property wrapper. Stores can contain any data, nonetheless, as the app is data heavy most stores contain loading states, data, and errors and methods to fetch data from the API.

The `APIClient` is injected into the stores that need to interact with the API. This allows us to pass the `MockAPIClient` for testing purposes.

### Previews

Xcode Previews allow you to see how a specific view looks like with different data. As the stores of this application get the api client injected, you should pass the mocked api client to the stores in the previews.

### Formatting

The project uses `swift-format` to format the code. To format the code, run the following command in the Client directory:

```sh
swift-format --recursive -i --configuration .swift-format .
```

> [!TIP]
> If you're using Xcode 16, you can use the `Editor > Structure > Format File with 'swift-format''` menu to format the code (default shortcut: `Control + Shift + i`). You can also select multiple files or a directory to format multiple files at once.

### Error handling

The app uses a custom error type `AppError` that takes a `LocalizedError`. This should be used to propagate errors as we can use those errors to show error toasts in the app.

> Showing error toast is not implemented yet. Though if we keep using `AppError` for error handling, it will be easy to implement error toasts in the future.

### Tests

For now there are no tests implemented in the app. Previews are used to test the views and their behaviour during development.

As there are already a mocked API client and mocked data, it should be easy to implement tests in the future.

## Distribution

> [!NOTE]
> In the future GitHub Actions will be used to do the following and upload the `.dmg` file to GitHub artifacts.

There are three scripts that help you to archive, build a `.dmg` file, and notarize the app for distribution.

### Archive

> [!WARNING]
> Change the `teamID` in the [`ExportOptions.plist`](Client/Client/ExportOptions.plist) file to your own team ID.

The build an archive of the app, run the following command in the `macos/Client` directory:

```sh
sh ./Scripts/archive.sh
```

This will automatically sign the app and create an archive of the app in the `macos/Client/dist` directory.

### Export and create `.dmg` file

> [!WARNING]
> This uses the [`create-dmg`](https://github.com/sindresorhus/create-dmg) tool to create the `.dmg` file. You need to have the tool installed on your system.

To create a `.dmg` file of the app, run the following command in the `macos/Client` directory:

```sh
sh ./Scripts/create_dmg.sh
```

This will export from the archive and create a `.dmg` file in the `macos/Client/dist` directory.

### Notarize

> [!WARNING]
> You need to have a paid Apple Developer account and a Developer ID Application certificate to notarize the app.

The following script uses an [app-specific password](https://support.apple.com/en-gb/102654) to notarize the app. You can create an app-specific password in your Apple ID settings.

To notarize the app, run the following command in the `macos/Client` directory:

```sh
NOTARY_PASSWORD=<your_app_specific_password> sh ./Scripts/notarize.sh
```

This will upload the `.dmg` file to Apple's notarization service which will check the app. This process is important as it allows Gatekeeper to know the app was checked by Apple and is safe to run on macOS. Read more [here](https://developer.apple.com/documentation/security/notarizing-macos-software-before-distribution). *We could also staple the notarization ticket to the `.dmg` file after this step and allow execution of the app even if the user is offline. This is a future improvement.*

## Contact

Marvin Kolja Willms - [marvin.willms@code.berlin](mailto:marvin.willms@code.berlin)
