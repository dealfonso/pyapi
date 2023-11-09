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
from random import randint

def rand_string(length: int):
    alphabet = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    result = ""
    for i in range(length):
        result += alphabet[randint(0, len(alphabet)-1)]
    return result

def seconds_to_human(seconds):
    """Converts a number of seconds to a human readable string

    Args:
        seconds (float): The number of seconds

    Returns:
        string: the human readable string
    """
    units = {
        "week":   7*24*3600,
        "day":    24*3600,
        "hour":      3600,
        "minute":        60,
        "second":         1,
    }

    # specifically handle zero
    if seconds == 0:
        return "0 seconds"

    s = ""
    for name, divisor in units.items():
        quot = int(seconds / divisor)
        if quot:
            s += f"{quot} {name}"
            s += ("s" if abs(quot) > 1 else "") + ", "
            seconds -= quot * divisor

    return s[:-2]

def remove_nones(obj):
    """Removes the elements that are None from a dict (recursive)

    Args:
        obj (stdClass): the object to clean

    Returns:
        stdClass: the cleaned object (same object)
    """
    if obj is None:
        return None
    
    # If obj is not an object return it
    if not isinstance(obj, dict):
        return obj

    keys_to_delete = []
    for key, value in obj.items():
        if value == None:
            keys_to_delete.append(key)
        elif isinstance(value, dict):
            value = remove_nones(value)
        elif isinstance(value, list):
            value = [remove_nones(item) for item in value if item != None]
    for key in keys_to_delete:
        del obj[key]
    return obj