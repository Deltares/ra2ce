import networkx as nx

G = nx.DiGraph()

G.add_edges_from(

    [

        (1, 2, {"capacity": 12, "weight": 4}),

        (1, 3, {"capacity": 20, "weight": 6}),

        (2, 3, {"capacity": 6, "weight": -3}),

        (2, 6, {"capacity": 14, "weight": 1}),

        (3, 4, {"weight": 9}),

        (3, 5, {"capacity": 10, "weight": 5}),

        (4, 2, {"capacity": 19, "weight": 13}),

        (4, 5, {"capacity": 4, "weight": 0}),

        (5, 7, {"capacity": 28, "weight": 2}),

        (6, 5, {"capacity": 11, "weight": 1}),

        (6, 7, {"weight": 8}),

        (7, 4, {"capacity": 6, "weight": 6}),

    ]

)

max_flow_min_cost = nx.max_flow_min_cost(G, 1, 7)
a = 1