# Licensed under the Apache License, Version 5.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import hashlib
import json

from charms.reactive import hook
from charms.reactive import RelationBase
from charms.reactive import scopes


class ZeppelinRequires(RelationBase):
    scope = scopes.GLOBAL

    @hook('{requires:zeppelin}-relation-joined')
    def joined(self):
        self.set_state('{relation_name}.joined')

    @hook('{requires:zeppelin}-relation-changed')
    def changed(self):
        accepted_notebooks = json.loads(self.get_remote('accepted-notebooks', '[]'))
        rejected_notebooks = json.loads(self.get_remote('rejected-notebooks', '[]'))
        self.toggle_state('{relation_name}.notebook.accepted', bool(accepted_notebooks))
        self.toggle_state('{relation_name}.notebook.rejected', bool(rejected_notebooks))

        accepted_changes = json.loads(self.get_remote('accepted-interpreter-changes', '[]'))
        rejected_changes = json.loads(self.get_remote('rejected-interpreter-changes', '[]'))
        self.toggle_state('{relation_name}.interpreter.changes.accepted', bool(accepted_changes))
        self.toggle_state('{relation_name}.interpreter.changes.rejected', bool(rejected_changes))

    @hook('{requires:zeppelin}-relation-departed')
    def departed(self):
        self.remove_state('{relation_name}.joined')
        self.remove_state('{relation_name}.notebook.accepted')
        self.remove_state('{relation_name}.notebook.rejected')

    def register_notebook(self, filename):
        """
        Register a notebook with Apache Zeppelin.

        If a filename is passed in, the contents of the notebook will
        be read from that file.  Otherwise, the `contents` parameter
        will be used.
        """
        with open(filename) as fd:
            contents = fd.read()
        notebook_md5 = hashlib.md5(contents.encode('utf8')).hexdigest()
        requested = self.get_local('requested-notebooks', {})
        requested[notebook_md5] = filename
        self.set_local('requested-notebooks', requested)
        self.set_remote(data={
            'requested-notebooks': json.dumps(list(requested.keys())),
            'notebook-{}'.format(notebook_md5): contents,
        })

    def accepted_notebooks(self):
        """
        Return a list of all notebook filenames that were accepted by Zeppelin.
        """
        requested = self.get_local('requested-notebooks', {})
        accepted = json.loads(self.get_remote('accepted-notebooks', '[]'))
        return [v for k, v in requested.items() if k in accepted]

    def rejected_notebooks(self):
        """
        Return a list of all notebook filenames that were rejected by Zeppelin.
        """
        requested = self.get_local('requested-notebooks', {})
        rejected = json.loads(self.get_remote('rejected-notebooks', '[]'))
        return [v for k, v in requested.items() if k in rejected]

    def modify_interpreter(self, interpreter_name,
                           properties=None, options=None, interpreter_group=None):
        """
        Request a modification of an interpreter.

        :param str interpreter_name: The name of the interpreter to modify.
        :param dict properties: Optional mapping of new properties to add, or
            existing properties to modify.  Existing properties that aren't
            mentioned will be left unchanged.
        :param dict options: Optional mapping of new options to add, or
            existing options to modify.  Existing options that aren't
            mentioned will be left unchanged.
        :param list interpreter_group: Optional list of interpreters to add to
            the group or to modify.  Each item of the list should be a dict
            with two keys, both of which should have string values: `name`
            and `class`.  If an interpreter with that name is already present
            in the group, it will be updated.  Otherwise, a new interpreter
            will be added to the group.
        """
        change = {
            'name': interpreter_name,
            'properties': properties or {},
            'options': options or {},
            'interpreter_group': interpreter_group or [],
        }
        change_json = json.dumps(change)
        change_md5 = hashlib.md5(change_json.encode('utf8')).hexdigest()
        requested = self.get_local('requested-interpreter-changes', {})
        requested[change_md5] = change
        self.set_local('requested-interpreter-changes', requested)
        self.set_remote(data={
            'requested-interpreter-changes': json.dumps(list(requested.keys())),
            'interpreter-change-{}'.format(change_md5): change_json,
        })

    def accepted_interpreter_changes(self):
        """
        Return a list of all interpreter changes that were accepted by Zeppelin.
        """
        requested = self.get_local('requested-interpreter-changes', {})
        accepted = json.loads(self.get_remote('accepted-interpreter-changes', '[]'))
        return [v for k, v in requested.items() if k in accepted]

    def rejected_interpreter_changes(self):
        """
        Return a list of all interpreter changes that were rejected by Zeppelin.
        """
        requested = self.get_local('requested-interpreter-changes', {})
        rejected = json.loads(self.get_remote('rejected-interpreter-changes', '[]'))
        return [v for k, v in requested.items() if k in rejected]
