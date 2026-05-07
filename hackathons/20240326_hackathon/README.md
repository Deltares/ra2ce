# Hackathon Q1 - 2024

Directory containing all jupyter notebooks and related work from the hackathon taken place 26 March 2024.

For a more in-detail summary of all the work done, please check the [jupyter notebook summary](./summary_2024q1.ipynb).


## Overall goal

Setting up a workflow to enable running RA2CE with multiple flood scenarios in an efficient way, on a larger geographical scale and post-processing the outcomes effectively into meaningful results


## User questions

- [UQ.1](user_question_1\README.md) Which roads are most likely to get hit by flooding from this hurricane given its projected flood maps?
- [UQ.2](user_question_2\README.md) Where are the flood impacts most disruptive in terms of accessibility? (detour length) = multi-link redundancy 
- [UQ.3] Which areas/locations are most likely to be unreachable because of this hurricane given its possible tracks? (OD analysis) (to be refined)
- [UQ.4] Optional if damages module works: What is the range of minimum and maximum damages that might occur because of this hurricane given its possible tracks?


## Hackathon requirements

- Being able to run RA2CE on a large scale with a complex network 
    - This should be coded generically so that we could do this ‘anywhere’
    - But computational time increases a lot with the scale and complexity of the network – how to handle?
    - How to determine the extent of the network with different flood maps?
    - Splitting up in smaller subsets? How would that change workflow and results?
- Running RA2CE in the cloud with multiple flood maps (100+) in different formats and storing the results
    - Being able to handle netcdf / data array / zar data formats?
    - Storing the different RA2CE runs and data efficiently
    - Skipping the second hazard overlay with the segmented graph as it increases computational time? 
    - Running multiple flood maps that represent a time series and then adding a time dimension in RA2CE results / analysis 
- Having a script that handles and post-processes multiple results 
    - Processing and storing results for all scenario runs and consolidate/merge them
    - Determining what the most interesting information is and how to communicate/visualize this
    - Visualization outputs such as statistics or ranges 
