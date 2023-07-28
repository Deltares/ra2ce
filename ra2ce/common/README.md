# Common

This module is meant to contain **ONLY** protocols (`typing.Protocol`) to be used by the different modules within `ra2ce`. Very concrete classes (such as some readers or writers) could also be defined in here, **IF** more than one different module is indeed using it.

- `configuration`: Contains the protocols for defining a configuration (`ConfigDataProtocol`), how to read it (`ConfigDataReaderProtocol`) and how to wrap it (`ConfigWrapperProtocol`).
- `io`: Module to cluster protocols for reading (`FileReaderProtocol`) and writing (`Ra2ceExporterProtocol`).
- `validation`: A validator will need to implement our protocol `Ra2ceIoValidator` which will return an object of type `ValidationReport`.