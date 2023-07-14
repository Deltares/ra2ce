from pathlib import Path
import numpy as np
import pandas as pd
import geopandas as gpd


class EquityAnalysis:
    def _get_values_prioritarian(
        self, equity_data: pd.DataFrame, od_table_data: gpd.GeoDataFrame
    ) -> np.array:
        prioritarian_mapping = dict(zip(equity_data["region"], equity_data["weight"]))
        prioritarian_mapping.update({"Not assigned": 1})
        return (
            od_table_data["region"].map(prioritarian_mapping) * od_table_data["values"]
        )

    @staticmethod
    def read_equity_weights(equity_weight_file: Path) -> pd.DataFrame:
        try:
            _separator = (
                ";" if ";" in equity_weight_file.read_text().splitlines()[0] else ","
            )
            return pd.read_csv(equity_weight_file, sep=_separator)
        except Exception:
            return pd.DataFrame()

    def optimal_route_od_link(
        self,
        gdf: gpd.GeoDataFrame,
        od_table: gpd.GeoDataFrame,
        equity_data: pd.DataFrame,
        destinations_names: list[str],
    ) -> pd.DataFrame:
        origin_nodes = np.unique(gdf["origin"])
        destination_nodes = np.unique(gdf["destination"])

        unique_destination_nodes = np.unique(list(od_table["d_id"].fillna("0")))
        count_destination_nodes = len([x for x in unique_destination_nodes if x != "0"])

        route_traffic = {}
        route_traffic_equal = {}
        route_traffic_prioritarian = {}
        if len(equity_data) > 0:
            route_traffic_prioritarian = {}
            od_table["values_prioritarian"] = self._get_values_prioritarian(
                equity_data, od_table
            )
        for o_node in origin_nodes:
            for d_node in destination_nodes:
                opt_path = gdf.loc[
                    (gdf["origin"] == o_node) & (gdf["destination"] == d_node),
                    "opt_path",
                ].values[0]
                for i, node in enumerate(range(len(opt_path))):
                    if i < len(opt_path) - 1:
                        u, v = opt_path[i], opt_path[i + 1]
                        t = 1
                        t_eq = 1
                        if len(equity_data) > 0:
                            t_prioritarian = 1
                        if "," in o_node:
                            o_nodes = o_node.split(",")
                            o_num = len(o_nodes)
                            j_ = 0
                            for j, o_n in enumerate(o_nodes):
                                if destinations_names in o_n:
                                    o_num -= 1
                                    j_ -= 1
                                    continue
                                else:
                                    traffic = (
                                        od_table.loc[
                                            od_table["o_id"] == o_n, "values"
                                        ].values[0]
                                        / count_destination_nodes
                                    )
                                if j_ == 0:
                                    t *= traffic
                                else:
                                    t += traffic
                                if len(equity_data) > 0:
                                    traffic_prioritarian = (
                                        od_table.loc[
                                            od_table["o_id"] == o_n,
                                            "values_prioritarian",
                                        ].values[0]
                                        / count_destination_nodes
                                    )
                                    if j_ == 0:
                                        t_prioritarian *= traffic_prioritarian
                                    else:
                                        t_prioritarian += traffic_prioritarian
                                j_ += 1
                            t_eq *= o_num
                        else:
                            traffic = (
                                od_table.loc[
                                    od_table["o_id"] == o_node, "values"
                                ].values[0]
                                / count_destination_nodes
                            )
                            t *= traffic
                            if len(equity_data) > 0:
                                traffic_prioritarian = (
                                    od_table.loc[
                                        od_table["o_id"] == o_node,
                                        "values_prioritarian",
                                    ].values[0]
                                    / count_destination_nodes
                                )
                                t_prioritarian *= traffic_prioritarian
                        if "," in d_node:
                            d_nodes = d_node.split(",")
                            d_num = len(d_nodes)
                            t_eq *= d_num
                            t *= d_num
                            if len(equity_data) > 0:
                                t_prioritarian *= d_num
                        try:
                            route_traffic[str(u) + "_" + str(v)] += t
                            route_traffic_equal[str(u) + "_" + str(v)] += t_eq
                            if len(equity_data) > 0:
                                route_traffic_prioritarian[
                                    str(u) + "_" + str(v)
                                ] += t_prioritarian
                        except Exception:
                            route_traffic.update({str(u) + "_" + str(v): t})
                            route_traffic_equal.update({str(u) + "_" + str(v): t_eq})
                            if len(equity_data) > 0:
                                route_traffic_prioritarian.update(
                                    {str(u) + "_" + str(v): t_prioritarian}
                                )

        u_list = [x.split("_")[0] for x in route_traffic.keys()]
        v_list = [x.split("_")[1] for x in route_traffic.keys()]
        t_list = route_traffic.values()
        teq_list = route_traffic_equal.values()
        if len(equity_data) > 0:
            tprioritarian_list = route_traffic_prioritarian.values()
            data_tuples = list(
                zip(u_list, v_list, t_list, teq_list, tprioritarian_list)
            )
            route_traffic_df = pd.DataFrame(
                data_tuples,
                columns=[
                    "u",
                    "v",
                    "traffic",
                    "traffic_egalitarian",
                    "traffic_prioritarian",
                ],
            )
        else:
            data_tuples = list(zip(u_list, v_list, t_list, teq_list))
            route_traffic_df = pd.DataFrame(
                data_tuples, columns=["u", "v", "traffic", "traffic_egalitarian"]
            )

        return route_traffic_df
