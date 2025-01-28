from pathlib import Path
import pandas as pd
from event import ProbabilisticEvent
from hazard_probabilitistic_set import HazardProbabilisticEventsSet

result_csv = Path(
    # r"C:\Users\hauth\OneDrive - Stichting Deltares\Desktop\WCF4Exchange\paper\res\results.csv"
    r"C:\Users\hauth\OneDrive - Stichting Deltares\Desktop\WCF4Exchange\paper\res\results500-700.csv"
)

rp_dict_waal = {13514: 200, 13516: 2000, 13518: 2000, 13528: 200, 13529: 200, 13530: 2000, 13531: 2000, 13532: 2000,
                13534: 200, 13535: 200, 13536: 2000, 13537: 2000, 13538: 20000, 13539: 200, 13540: 2000, 13541: 2000,
                13542: 20000, 13543: 20000, 19053: 125, 19054: 12500, 19055: 12500, 19056: 125, 19057: 1250,
                19058: 12500, 19061: 125, 19062: 12500, 19063: 125, 19064: 1250, 19726: 20000, 19727: 20000,
                19728: 2000, 19729: 20000, 19730: 2000, 19731: 20000, 19732: 2000, 21058: 1250, 21069: 1250, 810: 1250}

loc_dict_waal = {13514: 4, 13516: 4, 13518: 4, 13528: 3, 13529: 3, 13530: 3, 13531: 3, 13532: 3, 13534: 2, 13535: 2,
                 13536: 2, 13537: 2, 13538: 2, 13539: 1, 13540: 1, 13541: 1, 13542: 1, 13543: 1, 19053: 12, 19054: 12,
                 19055: 11, 19056: 10, 19057: 10, 19058: 10, 19061: 9, 19062: 9, 19063: 8, 19064: 8, 19726: 4, 19727: 5,
                 19728: 5, 19729: 6, 19730: 6, 19731: 7, 19732: 7, 21058: 11, 21069: 12, 810: 9}

dijkring_dict_waal = {13514: 1, 13516: 1, 13518: 1, 13528: 1, 13529: 1, 13530: 1, 13531: 1, 13532: 1, 13534: 1,
                      13535: 1, 13536: 1, 13537: 1, 13538: 1, 13539: 1, 13540: 1, 13541: 1, 13542: 1, 13543: 1,
                      19053: 2, 19054: 2, 19055: 2, 19056: 2, 19057: 2, 19058: 2, 19061: 2, 19062: 2, 19063: 2,
                      19064: 2, 19726: 1, 19727: 1, 19728: 1, 19729: 1, 19730: 1, 19731: 1, 19732: 1, 21058: 2,
                      21069: 2, 810: 2}

df = pd.read_csv(result_csv)
# remove row with nan values
df = df.dropna()
data_array = df.to_numpy().transpose()

list_events = []
for index, (event_id, event_rp, event_loc, event_dijkring) in enumerate(zip(rp_dict_waal.keys(), rp_dict_waal.values()
        , loc_dict_waal.values()
        , dijkring_dict_waal.values()
                                                                            )):
    event = ProbabilisticEvent(id=event_id,
                               name=f"event_{event_id}",
                               annual_probability=1 / event_rp,
                               location=event_loc,
                               dijkring=event_dijkring,
                               hazard_map=None,
                               damage=data_array[index])
    list_events.append(event)

hazard_set = HazardProbabilisticEventsSet(id=1,
                                          set_name="Waal",
                                          events=list_events,
                                          number_events=len(list_events),
                                          number_runs=len(data_array[0]))

hazard_set.plot_violin(var='damage')
# hazard_set.plot_histogram(var='AAL')
# hazard_set.plot_histogram_events()

# for loc in range(1,10):
#     hazard_set.plot_histogram_events(location=loc)
    # hazard_set.plot_violin(location=loc)
    # hazard_set.plot_violin(location
