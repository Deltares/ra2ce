.. _implementation_decisions:

Implementation decisions
========================

Some concrete cases require to be highlighted to avoid creating related issues and specifying the concrete direction we want to go on as a team.

Replacing Geopy with Geopandas
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
We tried replacing `geopy <https://geopy.readthedocs.io/en/stable/>`_ with similar functionality of `Geopandas <https://geopandas.org/en/stable/>`_. 
However, this did not seem to be a valid alternative as the accuracy and simplicity of geopy outweights the benefit of replacing it with similar extensive logic as can be seen in this `example <https://autogis-site.readthedocs.io/en/2019/notebooks/L2/calculating-distances.html>`_. 

.. tip:: 
    This topic was handled in issue `188 <https://github.com/Deltares/ra2ce/issues/188>`_