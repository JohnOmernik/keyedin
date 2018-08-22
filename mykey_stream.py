#!/usr/bin/python3

import warnings
from operator import itemgetter
warnings.simplefilter(action='ignore', category=FutureWarning)
from collections import OrderedDict
import sys
import json
import time
import struct
import math
import os.path
from keyedin import pitchdistribution as pd, classifiers
import random
import pyaudio
import socket
import librosa
import numpy as np
from numpy_ringbuffer import RingBuffer
SHORT_NORMALIZE = (1.0/32768.0)

UDP_PINGTIMEOUT = 1
UDP_SOCK = None
song_start = 0
out_file = "./outputs.json"
class_array = []
rms_buffer = RingBuffer(capacity=50, dtype=np.float32)
song_dist = None
samp_cnt = 0
myfile = ""
myclass = ""
classifier = None
last_class = 0
class_interval_min = 20
class_interval_max = 70
mic_device_str = "USB Camera"
FORMAT = pyaudio.paFloat32
CHANNELS = 4
RATE = 16000
CHUNK = 1024
in_song = False
break_rms = 45



IP = (([ip for ip in socket.gethostbyname_ex(socket.gethostname())[2] if not ip.startswith("127.")] or [[(s.connect(("8.8.8.8", 53)), s.getsockname()[0], s.close()) for s in [socket.socket(socket.AF_INET, socket.SOCK_DGRAM)]][0][1]]) + ["no IP found"])[0]

UDP_IP = 'pi3'
UDP_PORT = 30000

cursong = {}
# ring buffer will keep the last 2 seconds worth of audio
data_buffer = None

max_buffer = int(random.randint(class_interval_min, class_interval_max) * RATE)
try:
    myfile = sys.argv[1]
    if myfile == "stream":
        pass
    elif os.path.isfile(myfile): 
        print("File is : %s" % myfile)
    else:
        print("File: %s not found - exiting" % myfile)
        sys.exit(1)
except:
    print("please provide a filename and then an optional 1 or 2 (1 for bayes 2 for krumhansl) - If none provided, bayes will be used")
    print("Ex: ./mykey.py filename 1 or ./mykey.py filename")
    sys.exit(1)
try:
    tclass = int(sys.argv[2])
except:
    print("Second argument not provided or not an integer, defaulting to bayes")
    tclass = 1

if tclass == 1:
    print("using bayes")
    myclass = "bayes"
elif tclass == 2:
    print ("Using krumhansl")
    myclass = "krumhansl"
else:
    print("Integer provided, but not 1 or 2 for classifier, defaulting to bayes (1)")
    myclass = bayes

def main():
    global classifier
    global UDP_SOCK
    global UDP_PINGTIMEOUT
    if myclass == "bayes":
        classifier = classifiers.NaiveBayes()
    elif myclass == "krumhansl":
        classifier = classifiers.KrumhanslSchmuckler()
    else:
        print("No classifier known: exiting")
        sys.exit(1)

    if myfile != "stream": 
        dist = pd.PitchDistribution.from_file(myfile)
        mykey = classifier.get_key(dist)
        print("We ran the %s classifier on %s and found it to be %s" % (myclass, myfile, mykey))
    else:
        pa = pyaudio.PyAudio()
# function that finds the index of the Soundflower
# input device and HDMI output device
    mymic = -0
    print("Finding Mic %s" % mic_device_str)
    for i in range(pa.get_device_count()):
        dev = pa.get_device_info_by_index(i)
        print(dev['name'])
        if dev['name'].find(mic_device_str) >= 0:
            mymic = i
            print("Mic string %s found for Device ID %s" % (mic_device_str, mymic))
            break
    if mymic == -1:
        print("Could not find mic device string %s in the following list - Exiting" % mic_device_str)
        for i in range(pa.get_device_count()):
            dev = pa.get_device_info_by_index(i)
            print((i,dev['name'],dev['maxInputChannels']))
        sys.exit(1)
    if UDP_IP != "":
        UDP_SOCK = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # UDP
        UDP_SOCK.settimeout(UDP_PINGTIMEOUT)
    print("Opening Stream")
    mystream = pa.open(format = FORMAT,
             channels = CHANNELS,
             rate = RATE,
             frames_per_buffer=CHUNK,
             input = True,
             input_device_index=mymic,
             stream_callback = callback)
# start the stream
# arecord -D plughw:1,0 -d 10 test.wav

    mystream.start_stream()
    while mystream.is_active():
       time.sleep(0.25)

    mystream.close()
    pa.terminate()



def rms( data ):

    count = len(data)/2
    format = "%dh"%(count)
    shorts = struct.unpack( format, data )
    sum_squares = 0.0
    for sample in shorts:
        n = sample * SHORT_NORMALIZE
        sum_squares += n*n
    return math.sqrt( sum_squares / count ) * 100
def sendCmd(sendstr):
    global UDP_SOCK
    global UDP_IP
    global UDP_PORT
    print ("******** Sending this: %s " %  (sendstr))
    UDP_SOCK.sendto(sendstr.encode(), (UDP_IP, UDP_PORT))

def sortKeys(csong):
    ret = OrderedDict()
    for k, v in sorted(csong.items(), key=itemgetter(1), reverse=True):
        mystr = k.get_tonic() + " " + k.get_scale()
        ret[mystr] = v
    return ret

def printKeys(c):
    d = sortKeys(c)
    for k in d.keys():
        print("Key: %s - Count: %s" % (k, d[k]))

def callback(in_data, frame_count, time_info, flag):
    global data_buffer
    global last_class
    global class_interval_min
    global class_interval_max
    global class_array
    global max_buffer
    global classifier
    global cursong
    global break_rms
    global in_song
    global samp_cnt
    global rms_buffer
    global song_dist
    global song_start
    song_end = 0
    samp_cnt += 1
    curtime = int(time.time())

    currms = rms(in_data)
    rms_buffer.append(currms)

    rms_avg = sum(rms_buffer) / len(rms_buffer)
    if samp_cnt % 20 == 0:
        print("CurRMS: %s - RMS Avg: %s" % (currms, rms_avg))
        samp_cnt = 0
     
    if rms_avg > break_rms:
        if in_song == False:
            song_start = curtime
            song_end = 0
            print("Not in song and detecting high RMS: Starting to class song!")
            in_song = True
            cursong = {}
            class_array = []
            song_dist = None
            data_buffer = None
    else:
        if in_song == True:
            song_end = curtime
            print("In song and it got quiet, gonna stop class songing!")
            song = OrderedDict()
            song['start'] = song_start
            song['end'] = song_end
            dursecs = song_end - song_start
            durmin = int(dursecs / 60)
            dursecrem = dursecs % 60
            song['duration'] = dursecs
            song['duration_min'] = str(durmin) + ":" + str(dursecrem)
            song['final_keys'] = sortKeys(cursong)
            song['all_class'] = class_array
            if song_dist is not None:
                song['final_note_count'] = song_dist.to_dict()
                final_key = classifier.get_key(song_dist.class_norm())
                song['final_overall_key'] = final_key.get_tonic() + " " + final_key.get_scale()
            else:
                song['final_overall_key'] = "Unknown minor"
            u = open(out_file, "a")
            u.write(json.dumps(song) + "\n")
            u.close()
            sendCmd("No Key")
            print(json.dumps(song))
            in_song = False
            song_start = 0
            song_end = 0
            class_array = []
            data_buffer = None
            song_dist = None
            cursong = {}

    if data_buffer is None:
        data_buffer = in_data
    else:
        data_buffer += in_data


#    print("Size: %s - Max Size: %s" % (len(data_buffer), max_buffer))

    if len(data_buffer) >= max_buffer:
        if in_song == True:
            max_buffer = int(random.randint(class_interval_min, class_interval_max) * RATE)
   #         print("Classifying now")
            classstart = int(time.time())
            delta_time = curtime - last_class
            audio_data = np.fromstring(data_buffer, dtype=np.float32)
#            print("%s Start Pitch Dist" % int(time.time()))
            dist, raw = pd.PitchDistribution.from_stream(audio_data, RATE)
  #          print("Dist: %s" % dist)
 #           print("Raw Dist: %s" % raw)
            if song_dist is None:
                song_dist = raw
                song_dist_norm = song_dist.class_norm()
            else:
                song_dist.concat(raw)
#                print("Concat: %s" % song_dist)
                song_dist_norm = song_dist.class_norm()
 #               print("Concat Norm: %s" % song_dist_norm)
   #         print("%s End Pitch Dist - Type dist: %s" % (int(time.time()), type(dist)))
            last_class = curtime
            if dist is not None:
                mykey = classifier.get_key(dist)
                mykeyall = classifier.get_key(song_dist_norm)

                print ("Cur class: %s - Song total: %s" % (mykey, mykeyall))
                if mykey in cursong:
                    cursong[mykey] += 1
                else:
                    cursong[mykey] = 1
                classar = OrderedDict()
                classar['classtime'] = curtime
                classar['cursong'] = sortKeys(cursong)
                classar['classnotes'] = raw.to_dict()
                classar['curoverall'] = mykeyall.get_tonic() + " " + mykeyall.get_scale()
                sendCmd(classar['curoverall'])
                class_array.append(classar)
                classar = None
                classend = int(time.time())
                classdur = classend - classstart
#                print("%s - Key %s - Took: %s - Delta from last class: %s" % (curtime, mykey, classdur, delta_time))
                printKeys(cursong)
 #               print("Done Class")
            else:
                print("dist returned none")
            data_buffer = None
        else:
            data_buffer = None

    return (in_data, pyaudio.paContinue)

if __name__ == "__main__":
    main()
