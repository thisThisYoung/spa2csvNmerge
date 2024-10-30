#!/usr/bin/env python
"""
This is a python script for merging .csv files of drifts spectra by thisyoung
"""

import pandas as pd
import glob
import os

# create an empty dataframe
dataframes = pd.DataFrame()

# get the directory of each .csv file in the "split" folder 
csv_dir = os.path.join(os.getcwd(), "split/*csv")

# go through each .csv file in the "split" folder
for filepath in glob.glob(csv_dir):

    # read the .csv file
    df = pd.read_csv(filepath)

    # get the filename without extension of the .csv file and set it as the name of the second column
    filename = os.path.splitext(os.path.basename(filepath))[0]
    print(f"Processing : {filename}.csv")

    df = df.rename(columns = {df.columns[1]: filename}).iloc[:, 0:2] # remove the third column

    # record the first column of the first .csv file
    if dataframes.empty:
        dataframes = df[[df.columns[0]]]

    # join the second column of df to dataframes
    dataframes = dataframes.join(df.iloc[:, 1], how = "left")

# sort the spectra according to theirs names
wavenum = dataframes.iloc[:, 0]  # first column is the wavenumber
spectra = dataframes.iloc[:, 1:] # rest columns are the spectra
spectra = spectra.sort_index(axis = 1) # sort
dataframes = pd.concat([wavenum, spectra], axis = 1)

# write the spectra to .csv in current folder
dataframes.to_csv("merged.csv", index = False)
