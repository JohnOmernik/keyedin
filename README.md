# keyedin Stream Playing

I took the tool from https://github.com/zwaltman/keyedin and worked it to operate on streams of data with a Raspberry Pi.  The reasoning here was

1. Raspberry Pi's are small and portable, could I get it working ?
2. There are cheap decent quality USB microphones available for Raspbeery Pi (I used a Sony Playstation 3 Eye Camera... it has  4 channel Mic that works well!)
3. I wanted to be able to log the data in JSON format for queries in Apache Drill
4. I wanted to be able to take actions, so I included a way to send the key as a UDP packet to another PI for actions (in my case, I wanted to synthesize synesthesia via LEDs based on the Key).

## Results

- Key detection is pretty good. I played a CD and it got over 80% of the bluegrass songs correct
- Key detection is better on diatonic music. Bluegrass works well because of it's strong diatonic nature, other music in current form: YMMV
- Because the Pi (or perhaps Python) is pretty weak, the operation of "listening" is blocked in Python by the operation of "detecting notes"  I may look into threading to address this
- To address the previous point, I take random sized samples, essentially dropping a needle, listening, doing a note count, and then doing it again, keeping track of the total note counts over time. 
- I log both the overall notecounts, the overall key, and each samples time, note counts, and key detections. This is all in the JSON file for further analysis
- My code is a mess right now, but it's working.
- I did have to modify the original keyedin, I have provided links for reference, but that will not work with the mykey_stream.py file. 

## To-do
- Use threading, gevent, or multiprocessing to allow note detections on all parts of the song, not just the samples
- Potentially provide a interface to push blocks of sound to an event stream like MapR Streams and operate off that
- Once note detection is where I want it, understand and explore the machine learning component and see if we can help it by teaching it some music theory
- Clean up code
- Share LED strip code so people can put the two together


 





# keyedin - https://github.com/zwaltman/keyedin

**Tool for distributional key-finding using Python.**

Identifies the most likely key of a musical audio recording from among the major and minor [diatonic scales](https://en.wikipedia.org/wiki/Diatonic_scale). Approximates the audio's [pitch class distribution](http://mp.ucpress.edu/content/25/3/193) using the [constant-Q transform](https://en.wikipedia.org/wiki/Constant-Q_transform), and then provides a variety of classifiers for guessing its key based on this distribution. 

Applications of automated key-finding range from computing metadata for music databases (which is extremely tedious to do by hand/ear) to making music producers' lives easier when they're working with samples.

*[Note: The distributional view of tonality is well-known to be an incomplete picture of how the human auditory system identifies phenomena like 'key': It's an extreme abstraction which completely ignores structural information such as the order notes are heard in, which notes occur at the same time, etc. Despite this, in surprisingly many cases it allows for key-finding algorithms with acceptable accuracy. Google "distributional key-finding" or "pitch class distribution" for more info.]*

## Classifiers
### Krumhansl-Schmuckler
Uses a method based on the [Krumhansl-Schmuckler](http://rnhart.net/articles/key-finding/) key-finding algorithm to find a 'best fit' to a pitch class distribution. Compares the distribution to the 'typical' distribution for each key by taking their [Pearson correlation coefficient](https://en.wikipedia.org/wiki/Pearson_correlation_coefficient), and then takes the argmax over these.

### Naive Bayes
Uses a [Naive Bayes](https://en.wikipedia.org/wiki/Naive_Bayes_classifier) model wherein the audio's key is the class and the proportions of the audio made up by each note (i.e. the values of its pitch class distribution) are the features. 

### Others
Coming soon! The plan is to eventually include a classifier which uses a neural net (possibly just a multi-class perceptron), but first I need to figure out training data.

## Example Usage
```python
from keyedin import pitchdistribution as pd, classifiers

# Use naive Bayes classifier to guess the key of SongInGMajor.mp3
naive_bayes = classifiers.NaiveBayes()
dist = pd.PitchDistribution.from_file('path/to/SongInGMajor.mp3')
naive_bayes.get_key(dist) # Returns Key object Key('G', 'major')

# Use Krumhansl-Schmuckler classifier to guess the key of SongInBMinor.mp3
krumhansl_schmuckler = classifiers.KrumhanslSchmuckler()
dist = pd.PitchDistribution.from_file('path/to/SongInBMinor.mp3')
krumhansl_schmuckler.get_key(dist) # Returns Key object Key('B', 'minor')

# After key identification, tonal center and scale of keys are available through Key.get_tonic() and Key.get_scale()
k = pd.Key('F', 'major')
k.get_tonic() # Returns string 'F'
k.get_scale() # Returns string 'major'
```

## Dependencies
* KeyedIn uses [Librosa](https://github.com/librosa) for its constant-Q transform implementation, which is required for Keyedin to work on any audio input. An installation guide for Librosa can be found [here](https://librosa.github.io/librosa/install.html).

* KeyedIn also uses [NumPy](https://github.com/numpy) for essential functions, so you'll need it too. Installation info for NumPy can be found [here](https://www.scipy.org/install.html).
