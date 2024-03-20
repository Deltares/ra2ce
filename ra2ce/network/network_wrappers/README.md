# Network wrappers

In this package we define wrappers for reading a ra2ce network (`tuple[MultiGraph, GeoDataFrame]`). Each different class defines how a network will be created and cleaned.
Network wrappers need to instantiate the `NetworkWrapperProtocol`.

An instance of the `NetworkWrapperProtocol` defines the `get_network` method, which will return the aforementioend ra2ce network.

Any network wrapper can be created with the use of a `NetworkConfigData` instance. At the same time, if the user does not know which wrapper to use, the `NetworkWrapperFactory` will resolve this for us.

## Future work


### Encapsulate `NetworkWrapperProtocol` output

([Issue #373](https://github.com/Deltares/ra2ce/issues/373))
We expect to encapsulate the output of a `NetworkWrapperProtocol` into our own `Ra2ceNetwork` object (or else) so that it is easier to represent and refer to which object do we internally handle as a network.