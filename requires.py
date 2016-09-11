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
        accepted = json.loads(self.get_remote('accepted-notebooks', '[]'))
        rejected = json.loads(self.get_remote('rejected-notebooks', '[]'))
        self.toggle_state('{relation_name}.notebook.accepted', bool(accepted))
        self.toggle_state('{relation_name}.notebook.rejected', bool(rejected))

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
