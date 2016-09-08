# Overview

This interface layer handles the communication between the Apache Zeppelin
charm and other charms wishing to register a notebook with Zeppelin.


# Usage

## Charms Registering a Notebook

Charms that wish to register a notebook with Zeppelin should `require` this
interface.  The interface layer will set the following state when appropriate:

  * `{relation_name}.connected` indicates that Apache Zeppelin is present,
    and thus a notebook can be registered with the `register_notebook` method.

The `register_notebook` method can be passed either a `filename` or a `contents`
string.

An example of how a charm would use this interface would be:

```python
@when('zeppelin.connected')
def register_notebook(zeppelin):
    zeppelin.register_notebook(filename='files/notebook.json')
```


## Zeppelin

The Zeppelin charm should `provide` this interface.  The interface layer will
set the following states when appropriate:

  * `{relation_name}.notebook.registered` indicates that a client has
    registered a notebook.  The charm would then use the `notebook_files`
    method to iterate over the registered notebooks on disk.

An example of how the Zeppelin charm would use this interface would be:

```python
@when('zeppelin.installed', 'client.notebook.registered')
def register_notebook(client):
    notebooks = client.unregistered_notebooks()
    api = ZeppelinAPI()
    for notebook in notebooks:
        api.import_notebook(notebook)
    client.register_notebooks(notebooks)


@when('zeppelin.installed', 'client.notebook.removed')
def remove_notebook(client):
    notebooks = client.removed_notebooks()
    api = ZeppelinAPI()
    for notebook in notebooks:
        notebook_id = json.loads(notebook)['id']
        api.delete_notebook(notebook_id)
    client.remove_notebooks(notebooks)
```


# Contact Information

- <bigdata@lists.ubuntu.com>
