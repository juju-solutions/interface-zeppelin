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

from charms.reactive import hook
from charms.reactive import RelationBase
from charms.reactive import scopes


class ZeppelinRequires(RelationBase):
    scope = scopes.GLOBAL

    @hook('{requires:zeppelin}-relation-joined')
    def joined(self):
        self.set_state('{relation_name}.joined')

    @hook('{requires:zeppelin}-relation-departed')
    def departed(self):
        self.remove_state('{relation_name}.joined')

    def register_notebook(self, filename=None, contents=None):
        """
        Register a notebook with Apache Zeppelin.

        If a filename is passed in, the contents of the notebook will
        be read from that file.  Otherwise, the `contents` parameter
        will be used.
        """
        if filename:
            with open(filename) as fd:
                contents = fd.read()
        notebook_md5 = hashlib.md5(contents).hexdigest()
        self.set_remote('notebook-{}'.format(notebook_md5), contents)
