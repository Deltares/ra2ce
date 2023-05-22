from pathlib import Path
import geopandas as gpd
import webbrowser

# Just to make sonar-cloud stop complaining.
# _network_ini_name = "network.ini"
_analysis_ini_name = "analysis.ini"

if __name__ == "__main__":
    from ra2ce.ra2ce_handler import Ra2ceHandler
    example_num = 2
    root_dir = Path(rf'C:\repos\ra2ce\examples\example_{example_num}')

    # network_ini = root_dir / _network_ini_name
    # assert network_ini.is_file()

    analysis_ini = root_dir / _analysis_ini_name
    assert analysis_ini.is_file()

    # When run test.
    handler = Ra2ceHandler(network=None, analysis=analysis_ini)  # you can also input only the network_ini
    handler.configure()  # this will configure (create) the network and do the overlay of the hazard map with the
    # network if there is any
    handler.run_analysis()  # this will run the analysis
