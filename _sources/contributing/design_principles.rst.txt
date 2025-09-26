.. _design_principles:

Design principles
=================

Throughout RA2CE different design choices are made to achieve a software as easy as possible to understand whilst hosting the domain knowledge of our experts. 

Code standards
---------------

In general, we adhere to the `Zen of Python <https://peps.python.org/pep-0020/#id3>`_ and we use the `Google convention <https://google.github.io/styleguide/pyguide.html>`_ as a base for our coding standards. 
Those points where we differ from the `Google convention` are documented below. We consider this document to be a living document, so it is subject to discussion and potential changes.

When we talk about normalization we refer to standardizing how we name, describe, reference and use the following items:

- a package (folder),
- a module (file),
- a class,
- a method,
- a parameter,
- a property,
- a variable,

Code formatting happens in its majority with a Github workflow which is enforced after each succesful pull-request merge to main. This can be at any time locally done running the line:

.. code-block:: python
    
    poetry run isort . && poetry run black .

Naming conventions
^^^^^^^^^^^^^^^^^^
In general we use the following standards:

- `PascalCase <https://en.wiktionary.org/wiki/Pascal_case#English>`_, for class names.
- `snake_case <https://en.wikipedia.org/wiki/Snake_case>`_, for the rest.


Although in Python 'private' and 'public' is a vague definition, we often use the underscore symbol `_` to refer to objects that are not meant to be used outside the context where they were defined. For instance:

- We underscore method's names when they are not meant to be used outisde their container class.
- In addition, we underscore the variables defined within a method to (visually) differenciate them from the input arguments (parameters):

.. code-block:: python

    def example_method(param_a: float, param_b: float) -> float:
        _sum = param_a + param_b
        return _sum


Module (file) content
^^^^^^^^^^^^^^^^^^^^^

In general:

- One file consists of one (and only one) class.
- The file containing a class will have the same name (snake case for the file, upper camel case for the class).

Some exceptions:

- An auxiliar dataclass might be eventually defined in the same file as the only class using (and referencing) it.
- Test classes may contain mock classes when they are only to be used within said test-file.


Describing an item
^^^^^^^^^^^^^^^^^^

- Packages can be further describe with `README.md` files.
- Modules are described with docstrings using the `google docstring convention <https://gist.github.com/redlotus/3bc387c2591e3e908c9b63b97b11d24e>`_
- We prefer explicit over implicit declaration.
    - Use of `type hinting <https://docs.python.org/3/library/typing.html>`_.
- Classes are described with docstrings when required, its properties also have descriptive names and have explicit types using `type hints <https://docs.python.org/3/library/typing.html>`_.
- Methods contain a clear descriptive name, its arguments (parameters) contain `type hints <https://docs.python.org/3/library/typing.html>`_ and in case it is a 'public' method its signature has a description following the `google docstrings <https://google.github.io/styleguide/pyguide.html>`_ formatting.


Protocols over Base classes.
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

We prefer using `protocols <https://docs.python.org/3/library/typing.html#typing.Protocol>`_ over `base classes <https://docs.python.org/3/library/abc.html>`_ (abstract class) to enforce the `Single Responsibility Principle <https://en.wikipedia.org/wiki/Single_responsibility_principle>`_ as much as possible.