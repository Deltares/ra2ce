#Some tests that we need to insert in the test module later.
import pandas as pd
from pathlib import Path

from ra2ce.analyses.direct.direct_damage_calculation import DamageNetworkEvents


### Tests

class direct_damage_tests:
    def __init__(self):
        pass

    def event_based_damage_calculation_huizinga(self):
        damage_function = 'HZ'

        #This test roughly follows the DirectDamage.road_damage() controller in analyses_direct.py
        test_input, test_ref_output = prepare_event_test_input_output()

        road_gdf = test_input

        val_cols = [
            col for col in road_gdf.columns if (col[0].isupper() and col[1] == "_")
        ]

        event_cols = [x for x in val_cols if "_EV" in x]

        event_gdf = DamageNetworkEvents(road_gdf,val_cols)
        event_gdf.main(damage_function=damage_function)
        test_output_series = event_gdf.gdf['dam_EV1_HZ']
        reference_output_series = test_ref_output['dam_HZ_ref']

        if test_output_series.equals(reference_output_series):
            print('test passed')
        else:
            comparison2 = test_output_series.eq(reference_output_series,fill_value=0.)
            if comparison2.all(): #all elements are exactly the same
                print('test passed')
            else:
                print('{} roads are exactly the same'.format(comparison2.sum()))
                print('So {} roads are different'.format((~comparison2).sum()))
                print('Below the 5 first differences')
                print(event_gdf.gdf[~comparison2].head())
                print(test_ref_output[~comparison2].head())


    def event_based_damage_calculation_OSdaMage(self):
        pass

    def load_manual_damage_function(self):
        pass




#### Sample data
def load_osm_test_data(file_path=Path('test_data/NL332.csv')):
    # This is taken from OSdaMage version 0.8 D:\Europe_trade_disruptions\EuropeFloodResults\Model08_VMs\main
    # Region is NL332
    folder = Path('test_data')
    file = folder / 'NL332.csv'
    raw_data = pd.read_csv(file,index_col=0)
    return raw_data

#def prepare_data_for_event_test(raw_data):


def prepare_event_test_input_output():
    import numpy as np

    raw_data = load_osm_test_data()
    input_cols = ['osm_id', 'infra_type','lanes', 'bridge','length','length_rp100','val_rp100']
    test_input = raw_data[input_cols]

    #rework and rename some columns
    test_input['F_EV1_me'] = test_input['val_rp100'] / 100 #from cm to m
    test_input['F_EV1_fr'] = test_input['length_rp100'] / test_input['length']
    test_input['length'] = test_input['length'] * 1000 #from km to m
    test_input['highway'] = test_input['infra_type']
    test_input = test_input.drop(columns=['val_rp100','length_rp100','infra_type'])

    test_output = test_input.copy()
    test_output['dam_HZ_ref'] = raw_data['dam_HZ_rp100']
    test_output['dam_HZ_ref'] = test_output['dam_HZ_ref'].replace(to_replace=0.,value=np.nan)
    test_output['road_type_ref'] = raw_data['road_type']

    return test_input,test_output

tests = direct_damage_tests()
tests.event_based_damage_calculation_huizinga()
