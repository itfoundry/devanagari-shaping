import os

DIRECTORY = '../dump/ITF Devanagari/Medium/1.074/100/'

for file_name in os.listdir(DIRECTORY):
    os.symlink(DIRECTORY + file_name, file_name[5:][:-4])
