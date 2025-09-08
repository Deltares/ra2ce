from pathlib import Path

import numpy as np
import pandas as pd
from event import ProbabilisticEvent
from hazard_probabilitistic_set import HazardProbabilisticEventsSet

result_csv = Path(
    # r"C:\Users\hauth\OneDrive - Stichting Deltares\projects\RA2CE Uncertainty\paper\res\tertiary.csv"
    # r"C:\Users\hauth\OneDrive - Stichting Deltares\projects\RA2CE Uncertainty\paper\res\results_new_all.csv"
    # r"C:\Users\hauth\OneDrive - Stichting Deltares\Desktop\WCF4Exchange\paper\res\results500-700.csv"
    r"c:\Users\hauth\OneDrive - Stichting Deltares\projects\RA2CE Uncertainty\2024\output_new_damage_cuvres\results_new_ALL.csv"
)

scenario_data = pd.read_excel(
    Path(r'c:\Users\hauth\OneDrive - Stichting Deltares\projects\RA2CE Uncertainty\2024\paper\scenario_definition.xlsx'))

huizinga_ref_data = Path(
    r"c:\Users\hauth\OneDrive - Stichting Deltares\projects\RA2CE Uncertainty\2024\output_new_damage_cuvres\results_ref_C6.csv"
)

order_hazards_Waal = [13514, 13516, 13518, 13528, 13529, 13530, 13531, 13532, 13534, 13535, 13536, 13537, 13538, 13539,
                      13540, 13541, 13542, 13543, 19053, 19054, 19055, 19056, 19057, 19058, 19059, 19060, 19061, 19062,
                      19063, 19064, 19726, 19727, 19728, 19729, 19730, 19731, 19732, 21052, 21058, 21069, 810, 813]

order_hazards_Lek = [13545, 13546, 13548, 13550, 13554, 13555, 13970, 13971, 13974, 13975, 13979, 13980, 19035, 19036,
                     19037, 19038, 19039, 19040, 19041, 19042, 19043, 19044, 19045, 19046, 19047, 19048, 19049, 19050,
                     19051, 19052, 19121, 19122, 21053, 21054, 21055, 21056, 21057, 21068]

order_combi = [13514, 13516, 13518, 13528, 13529, 13530, 13531, 13532, 13534, 13535, 13536, 13537, 13538, 13539, 13540,
               13541, 13542, 13543, 13545, 13546, 13548, 13550, 13554, 13555, 13970, 13971, 13974, 13975, 13979, 13980,
               19035, 19036, 19037, 19038, 19039, 19040, 19041, 19042, 19043, 19044, 19045, 19046, 19047, 19048, 19049,
               19050, 19051, 19052, 19053, 19054, 19055, 19056, 19057, 19058, 19059, 19060, 19061, 19062, 19063, 19064,
               19121, 19122, 19726, 19727, 19728, 19729, 19730, 19731, 19732, 21052, 21053, 21054, 21055, 21056, 21057,
               21058, 21068, 21069, 810, 813]

data_waal = scenario_data[scenario_data['Rivier'] == 'Waal']
data_lek = scenario_data[scenario_data['Rivier'] == 'Lek']
data_combi = scenario_data
data_waal = data_waal.set_index("Scenario ID").loc[order_hazards_Waal].reset_index()
data_lek = data_lek.set_index("Scenario ID").loc[order_hazards_Lek].reset_index()
data_combi = data_combi.set_index("Scenario ID").loc[order_combi].reset_index()

# Load MC results from csv
df = pd.read_csv(result_csv)
df = df.dropna()
data_array = df.to_numpy().transpose()
print(np.max(data_array) / 1e6)
print(data_array.shape)
print(f" Number of hazards: {len(data_array)}, number of Monte Carlo runs: {len(data_array[0])}")

# Load reference Huizinga results. CAREFULL the order holds only for combi dataset!
huizinga_data = pd.read_csv(huizinga_ref_data).to_numpy().transpose()[0]

list_events = []
for i, event_data in data_combi.iterrows():
    event = ProbabilisticEvent(id=event_data['Scenario ID'],
                               name=event_data['Scenarionaam'],  # breakage location name
                               annual_probability=event_data['prob_cond'],
                               location=event_data["Bres"],
                               dijkring=event_data['dijkring'],
                               hazard_map=None,
                               damage=data_array[i])
    list_events.append(event)

hazard_set = HazardProbabilisticEventsSet(id=1,
                                          set_name="Combi",
                                          events=list_events,
                                          number_events=len(list_events),
                                          number_runs=len(data_array[0]),
                                          reference_values = huizinga_data)

# hazard_set.plot_violin(var='damage', sort_by_return_period=True)
hazard_set.plot_EP_spaghetti_plot()
# hazard_set.plot_histogram(var='AAL')
# hazard_set.plot_histogram(var='damage')
# hazard_set.plot_histogram_events()
# hazard_set.plot_CDF_AAL()

# hazard_set.plot_

# for loc in range(1,10):
#     hazard_set.plot_histogram_events(location=loc)
# hazard_set.plot_violin(location=loc)
# hazard_set.plot_violin(location
