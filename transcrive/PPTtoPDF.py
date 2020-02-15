import sys
import os
import comtypes.client

#%% Get console arguments
input_file_path = sys.argv[1]
output_file_path = sys.argv[2]

#%% Convert file paths to Windows format
input_file_path = os.path.abspath(input_file_path)
output_file_path = os.path.abspath(output_file_path)

#%% Create powerpoint application object
powerpoint = comtypes.client.CreateObject("Powerpoint.Application")

#%% Set visibility to minimize
powerpoint.Visible = 1

#%% Open the powerpoint slides
slides = powerpoint.Presentations.Open(input_file_path)

#%% Save as PDF (formatType = 32)
slides.SaveAs(output_file_path, 32)

#%% Close the slide deck
slides.Close()