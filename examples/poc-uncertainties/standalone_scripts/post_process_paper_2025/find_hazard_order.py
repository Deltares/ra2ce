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