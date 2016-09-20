# Licensed under the Apache License, Version 2.0 (the "License");
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


class ZeppelinProvides(RelationBase):
    scope = scopes.SERVICE

    @hook('{provides:zeppelin}-relation-changed')
    def changed(self):
        conv = self.conversation()
        requested = set(json.loads(conv.get_remote('requested-notebooks', '[]')))
        registered = set(conv.get_local('registered-notebooks', []))
        unregistered = requested - registered
        if unregistered:
            conv.set_local('unregistered-notebooks', list(unregistered))
            conv.set_state('{relation_name}.notebook.registered')

        changes = set(json.loads(conv.get_remote('requested-interpreter-changes', '[]')))
        processed = set(conv.get_local('processed-interpreter-changes', []))
        pending = changes - processed
        if unregistered:
            conv.set_local('pending-interpreter-changes', list(pending))
            conv.set_state('{relation_name}.interpreter.change')

    @hook('{provides:zeppelin}-relation-departed')
    def departed(self):
        conv = self.conversation()
        if len(conv.units) == 1:  # last unit leaving
            # get all notebooks set by the current remote unit
            # remove all notebooks for this service
            registered = set(conv.get_local('registered-notebooks', []))
            removed = set(conv.get_local('removed-notebooks', [])) & registered
            conv.set_local('removed-notebooks', list(removed))
            conv.set_state('{relation_name}.notebook.removed')

    def _notebooks(self, key):
        notebooks = []
        for conv in self.conversations():
            batch = conv.get_local(key, [])
            notebooks.extend(conv.get_remote('notebook-{}'.format(notebook))
                             for notebook in batch)
        return notebooks

    def unregistered_notebooks(self):
        """
        Returns a list containing all of the notebooks pending registration,
        as JSON strings.
        """
        return self._notebooks('unregistered-notebooks')

    def unremoved_notebooks(self):
        """
        Returns a list containing all of the notebooks pending removal,
        as JSON strings.
        """
        return self._notebooks('removed-notebooks')

    def accept_notebook(self, notebook):
        """
        Acknowledge that the given pending notebook has been registered.
        """
        notebook_md5 = hashlib.md5(notebook.encode('utf8')).hexdigest()
        for conv in self.conversations():
            registered = set(conv.get_local('registered-notebooks', []))
            unregistered = set(conv.get_local('unregistered-notebooks', []))
            if notebook_md5 in unregistered:
                registered.add(notebook_md5)
                conv.set_local('registered-notebooks', list(registered))
                conv.set_remote('accepted-notebooks',
                                json.dumps(list(registered)))

                unregistered.discard(notebook_md5)
                conv.set_local('unregistered-notebooks', list(unregistered))
                if not unregistered:
                    conv.remove_state('{relation_name}.notebook.registered')

    def reject_notebook(self, notebook):
        """
        Inform the client that the given pending notebook has been rejected.
        """
        notebook_md5 = hashlib.md5(notebook.encode('utf8')).hexdigest()
        for conv in self.conversations():
            rejected = set(conv.get_local('rejected-notebooks', []))
            unregistered = set(conv.get_local('unregistered-notebooks', []))
            if notebook_md5 in unregistered:
                rejected.add(notebook_md5)
                conv.set_local('rejected-notebooks', list(rejected))
                conv.set_remote('rejected-notebooks',
                                json.dumps(list(rejected)))

                unregistered.discard(notebook_md5)
                conv.set_local('unregistered-notebooks', list(unregistered))
                if not unregistered:
                    conv.remove_state('{relation_name}.notebook.registered')

    def remove_notebook(self, notebook):
        """
        Acknowledge that the given registered notebook has been removed.
        """
        notebook_md5 = hashlib.md5(notebook.encode('utf8')).hexdigest()
        for conv in self.conversations():
            registered = set(conv.get_local('registered-notebooks', []))
            registered.discard(notebook_md5)
            conv.set_local('registered-notebooks', list(registered))

    def interpreter_changes(self):
        """
        Returns a list containing all of the pending interpreter change requests.

        Each change request will be a dict with the keys: name, properties.
        The properties will be a dict mapping keys to values.
        """
        changes = []
        for conv in self.conversations():
            batch = conv.get_local('pending-interpreter-changes', [])
            for change_id in batch:
                change = json.loads(conv.get_remote('interpreter-change-{}'.format(change_id)))
                changes.append({
                    'name': change['name'],
                    'properties': change.get('properties') or {},
                })
        return changes

    def accept_interpreter_change(self, change):
        """
        Acknowledge that the given pending interpreter change has been processed.
        """
        change_md5 = hashlib.md5(json.dumps(change).encode('utf8')).hexdigest()
        for conv in self.conversations():
            processed = set(conv.get_local('processed-interpreter-changes', []))
            pending = set(conv.get_local('pending-interpreter-changes', []))
            if change_md5 in pending:
                processed.add(change_md5)
                conv.set_local('processed-interpreter-changes', list(registered))
                conv.set_remote('accepted-interpreter-changes',
                                json.dumps(list(processed)))

                pending.discard(change_md5)
                conv.set_local('pending-interpreter-changes', list(pending))
                if not pending:
                    conv.remove_state('{relation_name}.interpreter.change')

    def reject_interpreter_change(self, change):
        """
        Inform the client that the given pending interpreter change has been rejected.
        """
        change_md5 = hashlib.md5(json.dumps(change).encode('utf8')).hexdigest()
        for conv in self.conversations():
            rejected = set(conv.get_local('rejected-interpreter-changes', []))
            pending = set(conv.get_local('pending-interpreter-changes', []))
            if change_md5 in unregistered:
                rejected.add(change_md5)
                conv.set_local('rejected-interpreter-changes', list(rejected))
                conv.set_remote('rejected-interpreter-changes',
                                json.dumps(list(rejected)))

                pending.discard(change_md5)
                conv.set_local('pending-interpreter-changes', list(unregistered))
                if not pending:
                    conv.remove_state('{relation_name}.interpreter.change')
