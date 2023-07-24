# Purpose of this module

The validation module defines the generic protocol `Ra2ceValidatorProtocol` which can be implemented by concrete validators across the tool.

A validator is not binded to a given type, so one can create validators for instance for: `runners`, `readers`,  `writers`, `analyses` or `networks`.

In this module we also have a generic `ValidationReport` implementation. This definition should suffice for the current solution (`v0.1.1`). 