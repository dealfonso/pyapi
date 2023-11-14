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
import json
import os
from .utils import remove_nones

class JsonDB:
    """ This is a basic class that implements a in-memory database that is backed by a JSON file

        This class is an skeleton for the implementation of the database. The derived class must implement
        - _unserialize: this function is called when the database is loaded from a JSON file. It must
            translate the parsed content into the internal data structures
        - _serialize: this function must return the JSON representation of the database (to be saved to disk)

    """
    triggerAutosave = False
    _filename = None
    
    def _unserialize(self, parsed_content):
        """Function that translates the parsed content into the internal data structures

        Args:
            parsed_content (object): the dict that results from json.loads
        """
        raise Exception('_unserialize not implemented')

    def loadFromJsonFile(self, filename):
        """Loads the database from a JSON file

        Args:
            filename (string): The name of the file to load

        Raises:
            Exception: if the content is not valid
        """
        if not os.path.isfile(filename):
            raise Exception(f'file {filename} is not a file')
        
        with open(filename) as file:
            file_contents = file.read()

        try:
            parsed_content = json.loads(file_contents)
            
            if not self._unserialize(parsed_content):
                raise Exception('invalid JSON content')

            self._filename = filename
        except Exception as e:
            raise Exception(f'invalid JSON file: {e}')
        
    def wipe(self):
        """Wipes the internal values
        """
        pass

    def _serialize(self):
        """Returns the JSON representation of the database

        Returns:
            string: the JSON representation of the database

        Raises:
            Exception: if the _serialize function is not implemented in the derived class
        """
        raise Exception('_serialize not implemented')

    def __init__(self, filename = None, autosave = False) -> None:
        self.autosave = autosave
        self._filename = filename
        self._tokens = {}
        self._redirections = {}
        self._deleted_redirections = {}
        self.wipe()

    def save(self):
        """Writes the DB to the file

        Raises:
            Exception: raised if the filename is not set
        """
        if self._filename == None:
            raise Exception('filename is not set')
        
        content = json.dumps(remove_nones(self._objectToSave()), indent=2)
        with open(self._filename, 'w') as file:
            file.write(content)

    def triggerAutosave(self):
        """Forces triggering the autosave function (i.e. if autosave is set, the DB will be saved)
        """
        if self.autosave and self._filename is not None:
            self.save()

    def __str__(self) -> str:
        return json.dumps(self._serialize(), indent=2)
    
    def asObject(self) -> object:
        """Returns the object that is being serialized to the disk

        Returns:
            object: the object that is being saved
        """
        return self._serialize()
    
class EmptyJsonDB(JsonDB):
    """
        A class for simple DB that does not store anythin
            (*) this is intended for debugging purposes
            (*) this class still needs a file
    """
    def _unserialize(self, parsed_content):
        return True
    def _serialize(self):
        return {
            "message": "Empty Dummy DB"
        }
