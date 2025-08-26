Getting Started
===============

Installation
------------

.. code-block:: bash

   pip install ra2ce

5 Minute Quickstart
-------------------

Here’s a minimal example:

.. code-block:: python

   from ra2ce.network import OsmNetworkWrapper
   net = OsmNetworkWrapper("Yangon, Myanmar").build()

   from ra2ce.analysis import AnalysisRunner
   AnalysisRunner(net).run("damages")
