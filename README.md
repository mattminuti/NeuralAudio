# NeuralAudio
Sound compression (originally) based on Growing Self-Organizing Maps

Just some really old (2008-ish) code I've been meaning to make available.

## History
The original MATLAB code was hideously slow, and used a Growing Self-Organizing Map to try and cover the input space, which happened to be a mono wave file. Unfortunately, I can't seem to find any of the python implementations of the GSOM code. It was essentially a line-by-line translation from MATLAB to SciPy, and was roughly 10x faster than the MATLAB version on the same hardware, producing identical output WAVs. It was still really, really slow, though, like 5 minutes for a few seconds of mono audio.

The newer stuff works by taking time-series data and breaking it up to constant-length chunks, and then identifying matching chunks within a given tolerance level. It then generates a lookup table with the representative chunks, and a sequential list of indices to the table. These are then further compressed by bundling them together and zipping with lzma, because the tables are easily compressible. Decoding is simple: unzip, load the LUT, and read the index list, outputting the corresponding entry from the LUT.

## Applications
The method works for anything that can be represented as a vector of numbers, and can tolerate some "analog"-ish noise. Since the LUT and index thing are separate, you can do some nifty things like store a LUT that fits multiple tracks, or do some near-realtime decoding by loading the LUT and playing the appropriate entries from the index stream as it arrives.

## Recommended settings
Tests I did a few years back suggested that a blocksize of 2 produced the highest quality, for a given filesize. For some reason, I have a ton of files encoded with blocksize 2, tolerance 11, but I don't remember why those numbers were special.

## Usage

encode_multicore.py takes an input wave file, how large the blocksize should be, error tolerance level, and filename to base the output on. The compressed data is split into outputfile_index.bin, and outputfile_lutable.bin, which are then tarred and zipped into outputfile.tar.lzma, the .bins are cleaned up, and if you add a fifth argument ending in .wav, a decoded version will be created.

The .tar.lzma file can be decoded back into a stereo WAV with decode-to-wav.py, which expects to be provided the blocksize, input file, and output file.
