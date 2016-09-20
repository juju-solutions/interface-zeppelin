# Overview

This interface layer handles the communication between the Apache Zeppelin
charm and other charms wishing to register a notebook with Zeppelin.


# Usage

## Charms Registering a Notebook

Charms that wish to register a notebook with Zeppelin should `require` this
interface.  The interface layer will set the following state when appropriate:

  * `{relation_name}.joined` indicates that Apache Zeppelin is present,
    and thus a notebook can be registered with the `register_notebook` method,
    or interpreter properties can be modified.

  * `{relation_name}.notebook.accepted` indicates that Apache Zeppelin has
    accepted one or more of the requested notebooks.  You can get a list of
    the accepted notebook filenames with the `accepted_notebooks` method.

  * `{relation_name}.notebook.rejected` indicates that Apache Zeppelin has
    rejected one or more of the requested notebooks.  You can get a list of
    the rejected notebook filenames with the `rejected_notebooks` method.

  * `{relation_name}.interpreter.changes.accepted` indicates that Apache Zeppelin
    has accepted one or more of the requested interpreter property changes.  You
    can get a list of the accepted changes with the `accepted_interpreter_changes` method.

  * `{relation_name}.interpreter.changes.rejected` indicates that Apache Zeppelin has
    rejected one or more of the requested interpreter property changes.  You can get
    a list of the rejected changes with the `rejected_interpreter_changes` method.

The `register_notebook` method can be passed either a `filename` or a `contents`
string.

The `modify_interpreter` method must be passed the name of the interpreter (group) to
modify, as well as a dict mapping property names to values.

An example of how a charm would use this interface would be:

```python
@when('zeppelin.joined')
def register_notebook(zeppelin):
    zeppelin.register_notebook(filename='files/notebook.json')


@when('zeppelin.notebook.rejected')
def report_rejected_notebook(zeppelin):
    status_set('blocked', 'Zeppelin rejected our notebook')
```


## Zeppelin

The Zeppelin charm should `provide` this interface.  The interface layer will
set the following states when appropriate:

  * `{relation_name}.notebook.registered` indicates that a client has
    registered a notebook.  The charm would then iterate over the
    `unregistered_notebooks`, handle them, and use either `accept_notebook`
    or `reject_notebook` methods to acknowledge them.

  * `{relation_name}.notebook.removed` indicates that a client has
    disconnected and so its notebooks should be removed.  The charm would
    then use the `unremoved_notebooks` method to iterate over the notebooks
    to be removed and call `remove_notebook` to acknowledge them.

  * `{relation_name}.interpreter.change` indicates that a client has
    requested changes to interpreter properties.  The charm would then
    iterate over the `interpreter_changes` method, handle them, and use
    either `accept_interpreter_change` or `reject_interpreter_change`
    methods to acknowledge them.

An example of how the Zeppelin charm would use this interface would be:

```python
@when('zeppelin.installed', 'client.notebook.registered')
def register_notebook(client):
    api = ZeppelinAPI()
    for notebook in client.unregistered_notebooks():
        if api.import_notebook(notebook):
            client.accept_notebook(notebook)
        else:
            client.reject_notebook(notebook)


@when('zeppelin.installed', 'client.notebook.removed')
def remove_notebook(client):
    api = ZeppelinAPI()
    for notebook in client.unremoved_notebooks():
        notebook_id = json.loads(notebook)['id']
        api.delete_notebook(notebook_id)
        client.remove_notebook(notebook)
```


# Contact Information

- <bigdata@lists.ubuntu.com>
