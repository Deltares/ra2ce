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

Replacing NetworkX with igraph
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Currently NetworkX is used as graph framework `NetworkX <https://networkx.org/>`_.
A downside of this framework is the known poor performance.
For this reason igraph `igraph <https://igraph.org/python/>`_ has been assessed as possible replacement of NetworkX.

.. tip:: 
    This topic was handled in issue `222 <https://github.com/Deltares/ra2ce/issues/222>`_

Characteristics NetworkX
""""""""""""""""""""""""
- works well together with `geopandas`,
- has different classes for graphs, multigraphs and directed (multi-)graphs,
- offers many functions for graph manipulation and analysis.

Characteristics igraph
""""""""""""""""""""""
- has a better performance than NetworkX,
- less intuitive to use with Python and geopandas (e.g. working with coordinate systems is less straightforward),
- less suited for dynamic graphs (indexing needs to be redone on extension and reduction of the graph).

Conclusion
""""""""""
NetworkX is used on many places in the code.
This, together with the differences in implementation, will require a thorough refactoring of the application for the benefit of a significant performance improvement.
Therefore, for now, it was chosen not to work on replacing NetworkX with igraph.
