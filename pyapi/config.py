#
#    Copyright 2023 - Carlos A. <https://github.com/dealfonso>
#
#    Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.
#
import sys
from typing import Any, Union
from .debug import p_warning
import os
import yaml

def load(filenames: Union[str, list[str]], layered_configuration = False, *, configurable_variables: list[str] | None = None, current_config: Any = None, subkey: str = None) -> list[str]:
    """Loads the configuration from a list of yaml files (or a single yaml file) and puts it into the "current_config" object. The possible configuration variables
        are those variables in the "current_config" object that are not private, not callable and not modules. If the current_config is None, the configuration will be
        loaded into the current module (i.e. *this file*).

        If you want to use this mechanism for your own configuration module, please add a function like this to your module:
            def load(filenames):
                return pyapi.config.load(filenames=filenames, current_config=sys.modules[__name__])

        And the configuration will be loaded into your module, using the variables that are not private, not callable and not modules from your module.

        If the layered_configuration is True, the files will be loaded in reverse order (the last file will override the first one) and so the values in the first 
        file will have precedence. If it is False, the first file found will be used and the rest will be ignored.

    Args:
        filenames (Union[str, list[str]]): the list of files to load
        layered_configuration (bool, optional): wheter it is a layered configuration or not (i.e. read all possible files or only the first file found). Defaults to False.
        configurable_variables (list[str] | None, optional): list of variables to configure. If not provided, we'll get all the variables that are not private, not callable and not modules from the current_config. Defaults to None.
        current_config (Any, optional): the object to put the configuration into. If None, the current module will be used. Defaults to None.
        subkey (str, optional): the first key to read from the yaml file. Defaults to None.

    Returns:
        list[str]: the list of files that were used to load the configuration in the order that they were used
    """
    if filenames is None:
        raise Exception("filenames must be a list of strings")
    if isinstance(filenames, str):
        filenames = [ filenames ]
    if not isinstance(filenames, list):
        raise Exception("filenames must be a list of strings")

    # If the current_config is None, we use the current module to hold the configuration
    if current_config is None:
        current_config = sys.modules[__name__]

    # If there are no variables to configure, we use all the variables that are not private, not callable and not modules
    if configurable_variables is None:
        configurable_variables = [variable_name for variable_name in dir(current_config) if not variable_name.startswith("_") and not callable(getattr(current_config, variable_name)) and not type(getattr(current_config, variable_name)) == type(sys) ]

    # Now we'll create a new configuration object and load the configuration from the files
    config = Config.from_object(current_config, configurable_variables)
    
    files_used = config.load(filenames, layered_configuration, subkey)

    possible_variables = None
    if isinstance(current_config, dict):
        possible_variables = current_config.keys()
    else:
        possible_variables = dir(current_config)

    for variable_name in configurable_variables:
        is_config = False
        if variable_name in possible_variables:
            is_config = isinstance(getattr(current_config, variable_name), Config)
        
        if is_config:
            getattr(current_config, variable_name).read_from_object(getattr(config, variable_name))
        else:
            setattr(current_config, variable_name, getattr(config, variable_name))

    return files_used

class Config:
    """Class that holds a configuration with the following features:
        - each attribute of this class is a considered a configuration variable
        - the configuration variables can be loaded from a yaml file using the function load or load_files

        example:
            class MyConfig(Config):
                IP_ADDRESS = ""
    """

    def __init__(self, **kwargs) -> None:
        for key, value in kwargs.items():
            setattr(self, key, value)

    @staticmethod
    def from_object(object, variables_to_acquire: list[str] = None) -> "Config":
        """Creates a Config object from an object (or a dict)

        Args:
            object (Any): the object or dictionary to get the configuration from
            variables_to_acquire (list[str], optional): list of variables to acquire. If not provided, we'll get all the variables that are not private, not callable and not modules from the object. Defaults to None.

        Returns:
            Config: the Config object
        """
        result = Config()

        if variables_to_acquire is None:
            variables_to_acquire = [variable_name for variable_name in dir(object) if not variable_name.startswith("_") and not callable(getattr(object, variable_name)) and not type(getattr(object, variable_name)) == type(sys) ]

        for variable_name in variables_to_acquire:
            if variable_name in dir(object):
                setattr(result, variable_name, getattr(object, variable_name))
            elif variable_name.lower() in dir(object):
                setattr(result, variable_name, getattr(object, variable_name.lower()))

        return result

    def read_from_object(self, object: Any, variables_to_acquire: list[str] = None):
        """Reads a configuration from an object (or a dict). If (in the current object) a variable is a Config object, it will be read from the object too
            using the "load" function of the Config object.

        Args:
            object (Any): the object or dictionary to get the configuration from
            variables_to_acquire (list[str], optional): list of variables to read. If not provided, we'll get all the variables that are not private, not callable and not modules from the object. Defaults to None.
        """
        if variables_to_acquire is None:
            variables_to_acquire = [variable_name for variable_name in dir(self) if not variable_name.startswith("_") and not callable(getattr(self, variable_name)) and not type(getattr(self, variable_name)) == type(sys) ]

        object_attributes = None
        if isinstance(object, dict):
            object_attributes = object.keys()
        else:
            object_attributes = dir(object)

        for variable_name in variables_to_acquire:
            is_config = False
            if variable_name in dir(self):
                is_config = isinstance(getattr(self, variable_name), Config)

            if variable_name in object_attributes:
                if is_config:
                    getattr(self, variable_name).read_from_object(object[variable_name])
                else:
                    setattr(self, variable_name, object[variable_name])
            elif variable_name.lower() in object_attributes:
                if is_config:
                    getattr(self, variable_name).read_from_object(object[variable_name.lower()])
                else:
                    setattr(self, variable_name, object[variable_name.lower()])

    def load(self, filenames: list[str] | str, layered_configuration = False, subkey = None) -> list[str]:
        """Loads the configuration from a list of yaml files (or a single yaml file). If the layered_configuration is True, the files will 
            be loaded in reverse order (the last file will override the first one) and so the values in the first file will have precedence.
            If it is False, the first file found will be used and the rest will be ignored.

        Args:
            filenames (list[str] | str): the list of files to load
            layered_configuration (bool, optional): wheter it is a layered configuration or not (i.e. read all possible files or only the first
                file found). Defaults to False.
            subkey (string, optional): the first key to read from the yaml file. Defaults to None.
                If provided, the configuration will be read from the subkey of the yaml file. For example, if the yaml file is:
                    value1: 1
                    pyapi:
                        log_level: debug
                        log_file: /var/log/pyapi.log
                and the subkey is "pyapi", the configuration will be read from the "pyapi" key of the yaml file and "value" will be ignored.

        Raises:
            Exception: If an error happens

        Returns:
            list[str]: The list of files that were used to load the configuration in the order that they were used
        """

        if not isinstance(filenames, list):
            if not isinstance(filenames, str):
                raise Exception("filenames must be a list of strings")
            
            filenames = [ filenames ]

        if layered_configuration:
            filenames = filenames.reverse()

        used_files = []

        for filename in filenames:

            if not os.path.isfile(filename):
                continue

            used_files.append(filename)

            with open(filename, "r") as f:
                configuration = yaml.safe_load(f)

                if subkey is not None:
                    if subkey not in configuration:
                        p_warning(f"Error reading configuration file {filename}: key {subkey} not found")
                        continue
                    
                    configuration = configuration[subkey]

                self.read_from_object(configuration)

                if not layered_configuration:
                    break

        return used_files
    
    def toPlainObject(self) -> dict[str, Any]:
        """Converts the configuration to a plain object (i.e. a dict)
            (*) If a variable is a Config object, it will be converted to a plain object too

        Returns:
            dict[str, Any]: the plain object
        """
        result = {}
        for variable in dir(self):
            if variable.startswith("_") or callable(getattr(self, variable)) or type(getattr(self, variable)) == type(sys):
                continue

            result[variable] = getattr(self, variable)

            if isinstance(result[variable], Config):
                result[variable] = result[variable].toPlainObject()
        return result
    
    def __str__(self) -> str:
        """Dumps the object in YAML format

        Returns:
            str: the YAML representation of the object
        """
        return yaml.dump(self.toPlainObject(), default_flow_style=False)