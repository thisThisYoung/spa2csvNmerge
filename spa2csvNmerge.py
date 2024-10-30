#!/usr/bin/env python
"""
This is a python script for automatically merging .spa files to .csv files
Modified by thisyoung, based on spa2csv.py by ne0dim
"""
import os
import struct
from pathlib import Path
import pandas as pd

cwd = os.getcwd()
file_dir = os.path.join(cwd, "split")
files = [i for i in os.listdir(file_dir) if i.endswith(".spa")]
if files:
    print(f'Files in directory: {files}')
else:
    print('No files in directory')
    os._exit(0)
# Looping over the files in the directory
for file in files:
    print(f"Processing : {file}")

    # Opening datafile in binary mode provided as 0 argument
    with open(Path(file_dir, file), "rb") as f:
        spectrum_spa_binary_string = f.read()
    
    # Searching for spectrum offset
    # which is stored as 16bit unsigned number marked by x00x00x00x03x00
    raw_spectrum_offsets = spectrum_spa_binary_string.split(b"\x00\x00\x00\x03\x00")[1]
    bit_remainder = len(raw_spectrum_offsets)%2
    if bit_remainder:
        raw_spectrum_offsets = raw_spectrum_offsets[:-bit_remainder]
    spectrum_offsets = struct.unpack("<" + "H"*(len(raw_spectrum_offsets)//2), raw_spectrum_offsets)
    
    # Saving spectrum offset
    spectrum_offset = spectrum_offsets[0]
    # Spectrum end offset is stored after x00x00
    spectrum_end_offset = spectrum_offsets[2]
    
    # Searching for spectrum range
    # which are float 32bit numbers marked by pattern x00x00x00x03x00x00x00
    raw_spectrum_from_values = spectrum_spa_binary_string.split(b"\x00\x00\x00\x03\x00\x00\x00")
    spectrum_sections = len(raw_spectrum_from_values) # 1 section = background, 2 sections = background + spectrum

    output_data = {'wavenumber': None, 'intensity': None, 'background': None}
    for i in range(spectrum_sections):
        bit_remainder = (len(raw_spectrum_from_values[i]) - 4)%4
        if bit_remainder:
            raw_spectrum_from_values[i] = raw_spectrum_from_values[i][:-bit_remainder]
        if i == 0:
            spectrum_type = 'background'
            spectrum_from_values = struct.unpack("<" + "f"*((len(raw_spectrum_from_values[i])-4)//4), raw_spectrum_from_values[i][4:])
        else:
            spectrum_type = 'spectrum'
            spectrum_from_values = struct.unpack("<" + "f"*((len(raw_spectrum_from_values[i])-4)//4), raw_spectrum_from_values[i][4:])

        # Storing from and values for spectrum to get X axis coordinates
        spectrum_from_value = spectrum_from_values[2]
        spectrum_to_value = spectrum_from_values[3]
        
        # Unpacking spectrum using the offset found earlier.
        # The spectrum is just 32bit floats
        spectrum = spectrum_spa_binary_string[spectrum_offset:spectrum_end_offset]
        spectrum_float = struct.unpack("<" + "f"*(len(spectrum)//4), spectrum)
        # Calculating X axis step. Maybe it's also somewhere in the file, just couldn't find it right away
        spectrum_step = abs((spectrum_from_value - spectrum_to_value)/(len(spectrum_float)-1))
        # Making a new array for X axis values
        spectrum_xaxis = [spectrum_from_value - spectrum_step*i for i in range(len(spectrum_float))]
        
        if spectrum_type == 'background':
            output_data['background'] = spectrum_float
        elif spectrum_type == 'spectrum':
            output_data['wavenumber'] = spectrum_xaxis
            output_data['intensity'] = spectrum_float

        # save the file to csv
        df = pd.DataFrame(output_data)
        df.to_csv(Path(file_dir, file.replace('spa', 'csv')).absolute(), index=False)



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
