from pathlib import Path

path = Path(r"C:\Users\hauth\OneDrive - Stichting Deltares\Desktop\WCF4Exchange\paper\flood_map_combi")

# return all files:

files = [f for f in path.rglob("*") if f.is_file()]
names = []
for f in path.rglob("*"):
    if f.is_file():
        filename = f.name

        # format is 'scenario_13514.tif', retureve only the number
        if filename.startswith("NEWscenario_"):
            names.append(int(filename.split("_")[1].split(".")[0]))
        # names.append(f.name)
print(files)
print(names)

stop

from pathlib import Path
import pandas as pd

# result_csv = Path(
#     r"C:\Users\hauth\OneDrive - Stichting Deltares\Desktop\WCF4Exchange\paper\res\results.csv"
# )

return_period_file = Path(
    r"C:\Users\hauth\OneDrive - Stichting Deltares\projects\RA2CE Uncertainty\paper\scenario_definition.xlsx")

order_hazards_Waal = [13514, 13516, 13518, 13528, 13529, 13530, 13531, 13532, 13534, 13535, 13536, 13537, 13538, 13539,
                      13540, 13541, 13542, 13543, 19053, 19054, 19055, 19056, 19057, 19058, 19061, 19062, 19063, 19064,
                      19726, 19727, 19728, 19729, 19730, 19731, 19732, 21058, 21069, 810]


# these have been added to the folder on 31th January 2025 to account with all the missing flood maps from
# David Excel sheet
order_hazards_Waal_2 = [13514, 13516, 13518, 13528, 13529, 13530, 13531, 13532, 13534, 13535, 13536, 13537, 13538,
                        13539, 13540, 13541, 13542, 13543, 19053, 19054, 19055, 19056, 19057, 19058, 19059, 19060,
                        19061, 19062, 19063, 19064, 19726, 19727, 19728, 19729, 19730, 19731, 19732, 21052, 21058,
                        21069, 810, 813]

waal_rp_data = pd.read_excel(return_period_file, sheet_name="Waal")
# reorder the hazards according to the order in order_hazards_Waal
print(waal_rp_data)

waal_rp_data = waal_rp_data.set_index("id").loc[order_hazards_Waal].reset_index()
# drop column name
waal_rp_data = waal_rp_data.drop(columns="name")

d = waal_rp_data.to_dict('records')
d = {item["id"]: item['dijkring'] for item in d}
print(waal_rp_data)
print(waal_rp_data.to_dict('records'))

print(d)
