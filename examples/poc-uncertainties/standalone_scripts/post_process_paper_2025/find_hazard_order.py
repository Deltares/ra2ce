from pathlib import Path


path = Path(r"C:\Users\hauth\OneDrive - Stichting Deltares\projects\RA2CE Uncertainty\paper\flood_map_Waal")

# return all files:

files = [f for f in path.rglob("*") if f.is_file()]
names = []
for f in path.rglob("*"):
    if f.is_file():
        filename = f.name

        # format is 'scenario_13514.tif', retureve only the number
        if filename.startswith("scenario_"):
            names.append(int(filename.split("_")[1].split(".")[0]))
        # names.append(f.name)
print(files)
print(names)




from pathlib import Path
import pandas as pd
result_csv = Path(
    r"C:\Users\hauth\OneDrive - Stichting Deltares\Desktop\WCF4Exchange\paper\res\results.csv"
)

return_period_file = Path(
    r"C:\Users\hauth\OneDrive - Stichting Deltares\Desktop\WCF4Exchange\paper\scenario_definition.xlsx")

order_hazards_Waal = [13514, 13516, 13518, 13528, 13529, 13530, 13531, 13532, 13534, 13535, 13536, 13537, 13538, 13539,
                      13540, 13541, 13542, 13543, 19053, 19054, 19055, 19056, 19057, 19058, 19061, 19062, 19063, 19064,
                      19726, 19727, 19728, 19729, 19730, 19731, 19732, 21058, 21069, 810]

rp_dict_waal = {13514: 200, 13516: 2000, 13518: 2000, 13528: 200, 13529: 200, 13530: 2000, 13531: 2000, 13532: 2000,
                13534: 200, 13535: 200, 13536: 2000, 13537: 2000, 13538: 20000, 13539: 200, 13540: 2000, 13541: 2000,
                13542: 20000, 13543: 20000, 19053: 125, 19054: 12500, 19055: 12500, 19056: 125, 19057: 1250,
                19058: 12500, 19061: 125, 19062: 12500, 19063: 125, 19064: 1250, 19726: 20000, 19727: 20000,
                19728: 2000, 19729: 20000, 19730: 2000, 19731: 20000, 19732: 2000, 21058: 1250, 21069: 1250, 810: 1250}

waal_rp_data = pd.read_excel(return_period_file, sheet_name="Waal")
# reorder the hazards according to the order in order_hazards_Waal
print(waal_rp_data)

waal_rp_data = waal_rp_data.set_index("id").loc[order_hazards_Waal].reset_index()
# drop column name
waal_rp_data = waal_rp_data.drop(columns="name")

d = waal_rp_data.to_dict('records')
d = {item["id"]: item['rp'] for item in d}
print(waal_rp_data)
print(waal_rp_data.to_dict('records'))

print(d)

