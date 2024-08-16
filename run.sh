#!/bin/bash

if [ $? -eq 1 ]
then
    echo Installing missing packages...
    pip install -r requirements.txt
fi
python -m autollama $@
read -p "Press any key to continue..."
