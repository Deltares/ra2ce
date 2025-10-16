# Introduction
Subpackage `output_validator` is used to validate the output of a certain operation (e.g. creation of a network, running an analysis) against predefined reference data.

# Input
It can be applied to both the examples and acceptance tests by adding `OutputValidator(_result_directory).validate_output()`
The reference data should be put in folder `reference` within the folder where the outputs are generated.

A data folder containing test data might look like this:
```
analysis/
├── output
├── reference
│   ├── output
│   └── static
│       └── output_graph
└── static
    └── output_graph
```

# Validation
Each type of file to be validated has its own validator:
| Type of file | Validations |
|--------------|-------------|
| `.csv`, `.feather`, `.gpkg` | After sorting of columns, rows and list values, the values don't differ >1e-6 relatively |
| `.json` | The data is identical |
| `.p` | >95% of the edges have the same `u` and `v` |
