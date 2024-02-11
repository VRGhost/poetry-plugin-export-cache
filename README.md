# Poetry Package Exporter Plugin

## Introduction

The Poetry Package Exporter is a plugin for the [poetry](https://python-poetry.org/) package manager. It is designed to enhance the CI process by exporting project dependencies as separate pip-installable packages. By doing so, it allows you to leverage the existing Poetry cache, resulting in significantly shorter optimized build times.

## Features

- **Dependency Exportation**: Automatically exports your Poetry-managed dependencies into pip-installable packages.
- **Cache Re-utilization**: Leverages Poetry's cache system to avoid redundant downloads, speeding up the Docker build process.

## Installation

To install the Poetry Package Exporter plugin, run the following command in your terminal:

```sh
poetry plugin add poetry_plugin_export_packages
```

or

```sh
pip install poetry_plugin_export_packages
```

Ensure you have Poetry installed prior to adding this plugin. For instructions on installing Poetry, visit [Poetry's documentation](https://python-poetry.org/docs/).

## Usage

After installing the plugin, use the following command to export your dependencies:

```sh
poetry export-packages
```

This command will generate a set of pip-installable packages for your project's dependencies. You can then copy these packages into your Docker build context and use pip to install them during the Docker image build process.

## Configuration

The plugin supports several configuration options to customize the export process. 

```sh
$ poetry export-packages -h

Description:
  export python packages

Usage:
  export-packages [options]

Options:
  -o, --output-dir=OUTPUT-DIR          Directory to save packages to. [default: "export-packages"]
      --shebang=SHEBANG                Shebang to start the generated pip install script with [default: "#! /bin/sh"]
  -f, --output-script[=OUTPUT-SCRIPT]  Place to save output script to.
      --without=WITHOUT                The dependency groups to ignore. (multiple values allowed)
      --with=WITH                      The optional dependency groups to include. (multiple values allowed)
      --only=ONLY                      The only dependency groups to include. (multiple values allowed)
  -h, --help                           Display help for the given command. When no command is given display help for the list command.
  -q, --quiet                          Do not output any message.
  -V, --version                        Display this application version.
      --ansi                           Force ANSI output.
      --no-ansi                        Disable ANSI output.
  -n, --no-interaction                 Do not ask any interactive question.
      --no-plugins                     Disables plugins.
      --no-cache                       Disables Poetry source caches.
  -C, --directory=DIRECTORY            The working directory for the Poetry command (defaults to the current working directory).
  -v|vv|vvv, --verbose                 Increase the verbosity of messages: 1 for normal output, 2 for more verbose output and 3 for debug.

```


## Contributing

Contributions to the Poetry Dependency Exporter are welcome! 

## License

This project is licensed under the [MIT License](LICENSE). See the LICENSE file for more details.

