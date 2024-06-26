# AvgSpeed

In this subpackage all logic is found regarding calculation, reading and writing of average speeds on a NetworkX network.

The average speed per road type is calculated from the `maxspeed` of all edges in a graph. The result of assigning these speeds to a network is that each edge has a valid value for attributes `length`, `avgspeed` and `time`.
This needs to be done after simplification, to avoid the new attributes to be merged into a list.