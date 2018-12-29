import io
import pyaudio
import string
import sys
import wave

script, text = sys.argv

voice = 'SWAR1686_TalkingEngF'
# this gives letters spoken as their names for TalkingEng
#char_list = string.ascii_lowercase
#seg_index = {c:"{0}/{1:03d}.wav".format(voice, 94-i) for i,c in enumerate(char_list[::-1])}
# plus digit names
char_list = string.digits + string.ascii_lowercase
seg_index = {c:"{0}/{1:03d}.wav".format(voice, 94-i) for i,c in enumerate(char_list[::-1])}

text_lower = text.lower()

# concatenate segment wavs to temp buffer (not to output file object)
# this is useful because lets you use Wave_write methods rather than handle lists of bytes
params_set = False
wf_out_buff = io.BytesIO()
# Wave_{read,write} only work in context managers in py3.x; otherwise need explicit open/close
with wave.open(wf_out_buff, 'wb') as wf_out:
    for c in text_lower:
        # skip spaces, punctuation etc.
        if c in char_list:
            with wave.open(seg_index[c], 'rb') as wf:
                if not params_set:
                    # this defines (nchannels, sampwidth, framerate, nframes, comptype, compname)
                    # all should be identical per segment except nframes
                    # only need to set once: writeframes() updates nframes automatically
                    wf_out.setparams(wf.getparams())
                    params_set = True
                # append audio data
                wf_out.writeframes(wf.readframes(wf.getnframes()))

# audio data is available in wf_out_buff to write to file if required
#with open('test.wav', 'wb') as f:
#    f.write(wf_out_buff.getvalue())

# instantiate pyaudio to stream output audio
p = pyaudio.PyAudio()

# define callback function for streaming
#def callback(in_date, frame_count, time_info, status):
#    data = wf_out.readframes(frame_count)
#    return (data, pyaudio.paContinue)

# read audio CHUNK bytes at a time
CHUNK = 1024

# open stream
# this runs through whatever alsa has configured, not pulse
stream = p.open(format=p.get_format_from_width(wf_out.getsampwidth()),
                channels=wf_out.getnchannels(),
                rate=wf_out.getframerate(),
                output=True)
#                ,stream_callback=callback)

# return to beginning of output file for playback and open again
wf_out_buff.seek(0)
with wave.open(wf_out_buff, 'rb') as wf:
    data = wf.readframes(CHUNK)
    # play stream until we run out of data
    while len(data) > 0:
        stream.write(data)
        data = wf.readframes(CHUNK)

# stop stream
stream.stop_stream()
stream.close()

# close pyaudio
p.terminate()
