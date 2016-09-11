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
        requested = set(json.loads(conv.get_remote('requested-notebooks',
                                                   '[]')))
        registered = set(conv.get_local('registered-notebooks', []))
        unregistered = requested - registered
        if unregistered:
            conv.set_local('unregistered-notebooks', list(unregistered))
            conv.set_state('{relation_name}.notebook.registered')

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

    def remove_notebook(self, notebook):
        """
        Acknowledge that the given registered notebook has been removed.
        """
        notebook_md5 = hashlib.md5(notebook.encode('utf8')).hexdigest()
        for conv in self.conversations():
            registered = set(conv.get_local('registered-notebooks', []))
            registered.discard(notebook_md5)
            conv.set_local('registered-notebooks', list(registered))
