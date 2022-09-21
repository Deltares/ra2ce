# Purpose of this module.

This module has been created to define generic protocols for read / write functionality as well as to implement concrete generic readers that can be later on reused by specific modules.

## Do not:
* Create here readers / writers that are very specific for a given module. If only one concrete class is using it, think twice if it should go here.


## Do:
* Create your own wrappers for external libraries. It might help you getting control over what gets written and how as well as for some exception handling.