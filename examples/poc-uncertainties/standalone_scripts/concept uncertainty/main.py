from pathlib import Path
import pandas as pd
from event import ProbabilisticEvent
from hazard_probabilitistic_set import HazardProbabilisticEventsSet

result_csv = Path(
    r"C:\Users\hauth\OneDrive - Stichting Deltares\Desktop\WCF4Exchange\paper\res\results.csv"
)

rp_dict_waal = {13514: 200, 13516: 2000, 13518: 2000, 13528: 200, 13529: 200, 13530: 2000, 13531: 2000, 13532: 2000,
                13534: 200, 13535: 200, 13536: 2000, 13537: 2000, 13538: 20000, 13539: 200, 13540: 2000, 13541: 2000,
                13542: 20000, 13543: 20000, 19053: 125, 19054: 12500, 19055: 12500, 19056: 125, 19057: 1250,
                19058: 12500, 19061: 125, 19062: 12500, 19063: 125, 19064: 1250, 19726: 20000, 19727: 20000,
                19728: 2000, 19729: 20000, 19730: 2000, 19731: 20000, 19732: 2000, 21058: 1250, 21069: 1250, 810: 1250}

df = pd.read_csv(result_csv)
# remove row with nan values
df = df.dropna()
data_array = df.to_numpy().transpose()

list_events = []
for index, (event_id, event_rp) in enumerate(rp_dict_waal.items()):
    event = ProbabilisticEvent(id=event_id, name=f"event_{event_id}", annual_probability=1 / event_rp, hazard_map=None,
                               damage=data_array[index])
    list_events.append(event)

hazard_set = HazardProbabilisticEventsSet(id=1,
                                          set_name="Waal",
                                          events=list_events,
                                          number_events=len(list_events),
                                          number_runs=len(data_array[0]))



