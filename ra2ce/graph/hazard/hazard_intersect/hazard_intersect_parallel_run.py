"""
                    GNU GENERAL PUBLIC LICENSE
                      Version 3, 29 June 2007

    Risk Assessment and Adaptation for Critical Infrastructure (RA2CE).
    Copyright (C) 2023 Stichting Deltares

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

# This file contains the common utils to run a method in parallel
from joblib import Parallel, delayed
from typing import Callable


def get_hazard_parallel_process(
    delegated_func: Callable, func_iterable: Callable
) -> None:
    """
    Runs in parallel a delegated process which will consume using the `delayed` method together
    with its associated parameters to retrieve from `func_iterable`.

    Args:
        delegated_func (Callable): Method signature which will be run in parallel.
        func_iterable (Callable): Method generating the arguments required for `delegated_func`.
    """
    return Parallel(n_jobs=2, require="sharedmem")(
        func_iterable(delayed(delegated_func))
    )
