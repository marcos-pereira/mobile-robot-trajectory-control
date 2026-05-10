"""This codes implements a class that reads data from yaml files.
The goal is to read the parameters from yaml
files.

Contributors
- Marcos S. Pereira (marcos.si.pereira@gmail.com)
"""

# Import type hinting from future versions of Python
# if you are running older Python versions
from __future__ import annotations

import yaml
from typing import Any
import os


class YamlDatafile:

    @staticmethod
    def read_yaml_file(path_to_file) -> dict[str, dict[str, Any]]:
        """Return the data from the yaml file.

        Args:
            path_to_file (string): the path to the yaml file.

        Returns:
            dict: the data from the yaml file.
        """

        # Check if the file exists and print the directory of the file
        try:
            with open(path_to_file, "r") as yaml_file:
                data = yaml.safe_load(yaml_file)
        except FileNotFoundError:
            print(f"File not found: {path_to_file}")
            print(f"Current directory: {os.getcwd()}")
            raise

        return data

    @classmethod
    def get_parameter_from_yaml_file(
        cls, parameter_name, path_to_file
    ) -> dict[str, Any]:
        """Return parameter from the yaml file.

        Args:
            parameter_name (string): the name of the parameter inside the yaml file.
            path_to_file (string): the path to the yaml file.

        Returns:
            dict: a dict in which each element is one of the parameter properties in the yaml file.
        """

        parameter_data = cls.read_yaml_file(path_to_file)

        return parameter_data[parameter_name]

    @classmethod
    def get_all_parameters_from_yaml_file(
        cls, path_to_file
    ) -> dict[str, dict[str, Any]]:
        """Return parameters from the yaml file.

        Args:
            path_to_file (string): the path to the yaml file.

        Returns:
            dict: a dict in which each element is one of the parameters in the yaml file, each one
            with their own constraint properties.
        """
        parameters_data = cls.read_yaml_file(path_to_file)

        return parameters_data

    @classmethod
    def save_dict_to_yaml_file(cls, data: dict[str, str], path_to_file: str) -> None:
        """Save data to a yaml file.

        Args:
            data (dict): the data to be saved in the yaml file.
            path_to_file (string): the path to the yaml file.
        """
        # Write the dict of strings to a yaml file as a dict of strings to strings
        with open(path_to_file, "w") as yaml_file:
            yaml.dump(data, yaml_file, allow_unicode=True, sort_keys=False)
