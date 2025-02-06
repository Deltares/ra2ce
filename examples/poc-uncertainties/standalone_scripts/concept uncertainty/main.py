from pathlib import Path
import pandas as pd
from event import ProbabilisticEvent
from hazard_probabilitistic_set import HazardProbabilisticEventsSet

result_csv = Path(
    r"C:\Users\hauth\OneDrive - Stichting Deltares\projects\RA2CE Uncertainty\paper\res\results_925.csv"
    # r"C:\Users\hauth\OneDrive - Stichting Deltares\Desktop\WCF4Exchange\paper\res\results500-700.csv"
)

scenario_data = pd.read_excel(
    Path(r'C:\Users\hauth\OneDrive - Stichting Deltares\projects\RA2CE Uncertainty\paper\scenario_definition.xlsx'))

order_hazards_Waal = [13514, 13516, 13518, 13528, 13529, 13530, 13531, 13532, 13534, 13535, 13536, 13537, 13538, 13539,
                      13540, 13541, 13542, 13543, 19053, 19054, 19055, 19056, 19057, 19058, 19061, 19062, 19063, 19064,
                      19726, 19727, 19728, 19729, 19730, 19731, 19732, 21058, 21069, 810]

print(scenario_data)
data_waal = scenario_data[scenario_data['Rivier'] == 'Waal']
data_waal = data_waal.set_index("Scenario ID").loc[order_hazards_Waal].reset_index()
print(data_waal)

df = pd.read_csv(result_csv)
print(df.shape)
# remove row with nan values
df = df.dropna()
data_array = df.to_numpy().transpose()

print(data_array.shape)
# stop

list_events = []
for i, event_data in data_waal.iterrows():

    event = ProbabilisticEvent(id=event_data['Scenario ID'],
                               name=event_data['Scenarionaam'], #breakage location name
                               annual_probability=event_data['prob_cond'],
                               location=event_data["Bres"],
                               dijkring=event_data['dijkring'],
                               hazard_map=None,
                               damage=data_array[i])
    list_events.append(event)

hazard_set = HazardProbabilisticEventsSet(id=1,
                                          set_name="Waal",
                                          events=list_events,
                                          number_events=len(list_events),
                                          number_runs=len(data_array[0]))

hazard_set.plot_violin(var='damage', sort_by_return_period=True)
hazard_set.plot_histogram(var='AAL')
# hazard_set.plot_histogram_events()
hazard_set.plot_CDF_AAL()

# for loc in range(1,10):
#     hazard_set.plot_histogram_events(location=loc)
# hazard_set.plot_violin(location=loc)
# hazard_set.plot_violin(location
