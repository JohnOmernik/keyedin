#!/usr/bin/env python
"""
Tools for processing audio data
"""

import librosa
import numpy as np

def chromagram_from_file(filename):
    """
    Takes path FILENAME to audio file and returns the file's chromagram C (numpy array with shape=(12, t=number time samples))
    """
    y, sr = librosa.load(filename)
    # Separate harmonic component from percussive
    y_harmonic = librosa.effects.hpss(y)[0]
    # Make CQT-based chromagram using only the harmonic component to avoid pollution
    C = librosa.feature.chroma_cqt(y=y_harmonic, sr=sr)
    return C



def chromagram_from_stream(str_data, sr):
    """
    Takes path FILENAME to audio file and returns the file's chromagram C (numpy array with shape=(12, t=number time samples))
    """
    y = np.fromstring(str_data, dtype=np.float32)

#   y, sr = librosa.load(filename)
    # Separate harmonic component from percussive
    y_harmonic = librosa.effects.hpss(y)[0]
    # Make CQT-based chromagram using only the harmonic component to avoid pollution
    C = librosa.feature.chroma_cqt(y=y_harmonic, sr=sr)
    return C
