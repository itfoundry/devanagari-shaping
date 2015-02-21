import os

for file_name in os.listdir('../drawbot/output/png/'):
    os.symlink('../drawbot/output/png/' + file_name, file_name[5:][:-4])
