#!/bin/bash

sudo apt-get update
sudo apt-get dist-upgrade

sudo pip3 install numpy --upgrade 
sudo apt-get install python3-pandas python3-pyaudio

sudo apt-get install python3-sklearn llvm-3.8

#udo apt-get install llvm-3.8
sudo ln -s /usr/bin/llvm-config-3.8 /usr/bin/llvm-config
sudo pip3 install llvmlite==0.15.0 numba==0.32.0 librosa==0.6.0

sudo apt-get install libatlas-base-dev
