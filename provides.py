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

import json

from charmhelpers.core import hookenv
from charms.reactive import hook
from charms.reactive import RelationBase
from charms.reactive import scopes


class ZeppelinProvides(RelationBase):
    scope = scopes.SERVICE

    @hook('{provides:zeppelin}-relation-changed')
    def changed(self):
        conv = self.conversation()
        notebooks = self._notebooks()
        # get all notebooks set by the current remote unit
        # (we have to use low-level relation API because relation data keys
        # are not known ahead of time and reactive API doesn't support this)
        notebooks = {key.split('-', 1)[1]
                     for key in hookenv.relation_get().keys()
                     if key.startswith('notebook-')}
        registered = set(conv.get_local('registered', []))
        unregistered = notebooks - registered
        if unregistered:
            conv.set_local('unregistered', list(unregistered))
            conv.set_state('{relation_name}.notebook.registered')

    @hook('{provides:zeppelin}-relation-departed')
    def departed(self):
        conv = self.conversation()
        if len(conv.units) == 1:  # last unit leaving
            # get all notebooks set by the current remote unit
            # (we have to use the low-level relation API here because
            # relation data keys are not known ahead of time and reactive
            # API doesn't support this)
            notebooks = {key.split('-', 1)[1]
                         for key in hookenv.relation_get().keys()
                         if key.startswith('notebook-')}
            # remove all notebooks for this service
            removed = set(conv.get_local('removed-notebooks', [])) & notebooks
            conv.set_local('removed-notebooks', list(removed))
            conv.set_state('{relation_name}.notebook.removed')

    def _notebooks(self, key):
        notebooks = []
        for conv in self.conversations():
            batch = conv.get_local(key, [])
            notebooks.extend(conv.get_remote('notebook-{}'.format(notebook_id))
                             for notebook_id in batch)
        return notebooks

    def registered_notebooks(self):
        """
        Returns a list containing all of the registered notebooks, as JSON
        strings.
        """
        return self._notebooks('registered-notebooks')

    def unregistered_notebooks(self):
        """
        Returns a list containing all of the registered notebooks, as JSON
        strings.
        """
        self._notebooks('unregistered-notebooks')

    def removed_notebooks(self):
        """
        Returns a list containing all of the registered notebooks, as JSON
        strings.
        """
        self._notebooks('removed-notebooks')

    def register_notebooks(self, notebooks):
        """
        Acknowledge that the given notebooks have been registered.
        """
        notebook_ids = {json.loads(notebook)['id']
                        for notebook in notebooks}
        for conv in self.conversations():
            registered = set(conv.get_local('registered-notebooks', []))
            registered.update(notebooks)
            conv.set_local('registered-notebooks', list(registered))
            unregistered = set(conv.get_local('unregistered-notebooks', []))
            unregistered.difference_update(notebook_ids)
            conv.set_local('unregistered-notebooks', list(unregistered))

    def remove_notebooks(self, notebooks):
        """
        Acknowledge that the given notebooks have been removed.
        """
        notebook_ids = {json.loads(notebook)['id']
                        for notebook in notebooks}
        for conv in self.conversations():
            registered = set(conv.get_local('registered-notebooks', []))
            registered.difference_update(notebook_ids)
            conv.set_local('registered-notebooks', registered)

            removed = set(conv.get_local('removed-notebooks', []))
            removed.difference_update(notebook_ids)
            conv.set_local('removed-notebooks', removed)
