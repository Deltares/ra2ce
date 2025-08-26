.. _contributing:

Contributing
============

Contributions are welcome, and they are greatly appreciated! Every little bit
helps, and credit will always be given.

In addition to the content of this file, please check our :ref:`design_principles` subchapter.


Guidelines
-----------------------

Please follow these guidelines to make contributing to this project easier:

1. Please report to us if you wish to collaborate via creating an issue at https://github.com/Deltares/ra2ce/issues.
2. Use both black and isort (included in the development dependencies) for code formatting.
3. Use google docstrings format for documenting your methods and classes.
4. New code should come along with new tests verifying its functionality (see more in :ref:`Writing tests`.)
5. New additions (bug fixes, features, etc) can be done through Pull Requests. Before merging they will be subject to the Continuous Integration builds as well as a code review.


Types of Contributions
----------------------

Report Bugs
~~~~~~~~~~~

Report bugs at https://github.com/Deltares/ra2ce/issues.

If you are reporting a bug, please include:

* Your operating system name and version.
* Any details about your local setup that might be helpful in troubleshooting.
* Detailed steps to reproduce the bug.

Fix Bugs
~~~~~~~~

Look through the GitHub issues for bugs. Anything tagged with "bug" and "help
wanted" is open to whoever wants to implement it.

Implement Features
~~~~~~~~~~~~~~~~~~

Look through the GitHub issues for features. Anything tagged with "enhancement"
and "help wanted" is open to whoever wants to implement it.

.. _Writing tests:

Writing tests
~~~~~~~~~~~~~~~~~~~
Tests will be written in the `tests` module, mirroring the file structure of the `ra2ce` module. Each file will have its own test file wrapped in a test class, for instance given the following method in a file named `dummy_calculations.py`:

.. code-block:: python

    def function_a_b_addition(a: float, b: float) -> float:
        """
        Given a and b, make the addition of both values.

        Args:
            a (float): First argument.
            b (float): Second argument.

        Returns:
            float: Result of first and second argument's addition.
        """
        if not a or not b:
            raise ValueError("Not all arguments were given.")
        return a + b

We will have a test file named `test_dummy_calculations.py` covering as many paradigms as possible:

.. code-block:: python

    @pytest.mark.parametrize(
        "a, b",
        [
            pytest.param(None, -1, id="a is not valid"),
            pytest.param(-1, None, id="b is not valid"),
        ],
    )
    def test_function_a_b_addition_with_invalid_args_raises(a: float, b: float):
        with pytest.raises(ValueError) as exc_err:
            function_a_b_addition(a, b)
        assert str(exc_err.value) == "Not all arguments were given"


    def test_function_a_b_addition_returns_expected_value(self):
        # 1. Given
        a = 42
        b = 24

        # 2. When
        c = function_a_b_addition(a, b)

        # 3. Then.
        assert c == 66


Acceptance tests
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Our test fixtures are ready to collect and run large models for manual validation. 
To do so, you will have to place your model under our `Deltares SVN Repository <https://repos.deltares.nl/repos/GFS_incubator/branches/ra2ce_test_data>`_.
Our `TeamCity configuration <https://dpcbuild.deltares.nl/buildConfiguration/Ra2ce_Ra2ceContinuousIntegrationBuild_RunExternalTests?mode=builds>`_ will then be able to run the models there located so long as they follow the conventions described in said repository.


Write Documentation
~~~~~~~~~~~~~~~~~~~

Please, write documentation on each "public" class or method you create using `google docstrings` formatting, for example:

.. code-block:: python

    def function_a_b_addition(a: float, b: float) -> float:
        """
        Given a and b, make the addition of both values.

        Args:
            a (float): First argument.
            b (float): Second argument.

        Returns:
            float: Result of first and second argument's addition.
        """


In addition, we encourage you to extend our current documentation and examples to better describe the functionality you added.

To locally validate your documentation changes, simply run :code:`poetry run docs\\make html`, 
you may then navigate to :code:`docs\\build\\html` and open the :code:`index.html` file in your preferred internet browser.

.. tip:: 
    Risk Assessment and Adaptation for Critical infrastructurE could always use more documentation, whether as part of the
    official Risk Assessment and Adaptation for Critical infrastructurE docs, in docstrings, or even on the web in blog posts,
    articles, and such.

Submit Feedback
~~~~~~~~~~~~~~~

The best way to send feedback is to file an issue at https://github.com/Deltares/ra2ce/issues.

If you are proposing a feature:

* Explain in detail how it would work.
* Keep the scope as narrow as possible, to make it easier to implement.
* Remember that this is a volunteer-driven project, and that contributions
  are welcome :)

..
  The following table of contents is hidden as we don't need to display it.
  However, it will bind those items to this one in the "section menu".

.. toctree::
   :caption: Table of Contents
   :maxdepth: 1
   :hidden:

   design_principles
   implementation_decisions