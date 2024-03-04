import socket
import sys
import time
import argparse
import signal
import struct
import os
import json
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import style
import sounddevice as sd
from scipy.signal import hilbert, savgol_filter, coherence

raw_pulse_signal = []
all_data = []

# Print received message to console
def print_message(*args):
    try:
        # print(args[0]) #added to see raw data
        data = json.loads(args[0].decode()).get('data')
        averages = []
        for i in np.arange(5):
            sum = 0
            for j in np.arange(8):
                sum += data[j][i]
            averages.append(sum/8)
        return averages

    except BaseException as e:
        print(e)


#  print("(%s) RECEIVED MESSAGE: " % time.time() +
# ''.join(str(struct.unpack('>%df' % int(length), args[0]))))

# Clean exit from print mode
def exit_print(signal, frame):
    print("Closing listener")
    sys.exit(0)


# Record received message in text file
def record_to_file(*args):
    textfile.write(str(time.time()) + ",")
    # textfile.write(''.join(str(struct.unpack('>%df' % length, args[0]))))
    textfile.write(str(json.loads(args[0].decode()).get('data')))
    textfile.write("\n")


# Save recording, clean exit from record mode
def close_file(*args):
    print("\nFILE SAVED")
    textfile.close()
    sys.exit(0)

def run_main():
    # Collect command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("--ip",
                        default="127.0.0.1", help="The ip to listen on")
    parser.add_argument("--port",
                        type=int, default=12346, help="The port to listen on")
    parser.add_argument("--address", default="/openbci", help="address to listen to")
    parser.add_argument("--option", default="print", help="Debugger option")
    parser.add_argument("--len", default=8, help="Debugger option")
    args = parser.parse_args()

    # Set up necessary parameters from command line
    length = args.len
    if args.option == "print":
        signal.signal(signal.SIGINT, exit_print)
    elif args.option == "record":
        i = 0
        while os.path.exists("udp_test%s.txt" % i):
            i += 1
        filename = "udp_test%i.txt" % i
        textfile = open(filename, "w")
        textfile.write("time,address,messages\n")
        textfile.write("-------------------------\n")
        print("Recording to %s" % filename)
        signal.signal(signal.SIGINT, close_file)

    # Connect to socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_address = (args.ip, args.port)
    sock.bind(server_address)

    # Display socket attributes
    print('--------------------')
    print("-- UDP LISTENER -- ")
    print('--------------------')
    print("IP:", args.ip)
    print("PORT:", args.port)
    print('--------------------')
    print("%s option selected" % args.option)

    # Receive messages
    print("Listening...")
    sec_data = []
    for i in np.arange(5):
        sec_data.append([])
    start = time.time()
    numSamples = 0
    sample_size = np.inf
    duration = np.inf
    fs = 22050

    def audio_callback(indata, frames, time, status):
        if status:
            print('Error:', status)

        analytic_signal = hilbert(indata[:, 0])
        envelope = np.abs(analytic_signal)
        envelope = savgol_filter(envelope, len(analytic_signal), 1)

        coherence_results = []
        for i in sec_data:
            f, Cxy = coherence(envelope, i, fs)
            max_c = np.max(Cxy)
            max_f = f[np.argmax(Cxy)]
            coherence_results.append([max_c, max_f])
        
        print(coherence_results)

        sec_data = []
        for i in np.arange(5):
            sec_data.append([])

    while (time.time() <= start + duration) and (numSamples < sample_size):
        # with sd.InputStream(callback=audio_callback,
        #         samplerate=fs,
        #         blocksize=int(fs * duration),  # Set the block size to collect more data per frame
        #         channels=1):
        data, addr = sock.recvfrom(20000)  # buffer size is 20000 bytes
        # audio_data = sd.rec(int(1 * 22050), samplerate=fs, channels=1, dtype='float64')
        # sd.wait()  # Wait until recording is finished
        if args.option == "print":
            averages = print_message(data)
            for i in np.arange(5):
                sec_data[i].append(averages[i])
            
            numSamples += 1
            # audio_data = audio_data.flatten()

            # analytic_signal = hilbert(audio_data)
            # envelope = np.abs(analytic_signal)
            # envelope = savgol_filter(envelope, len(analytic_signal), 1)

            # print(sec_data)
            # coherence_results = []
            # for i in sec_data:
            #     f, Cxy = coherence(i, i, fs)
            #     max_c = np.max(Cxy)
            #     max_f = f[np.argmax(Cxy)]
            #     coherence_results.append([max_c, max_f])
            # print(coherence_results)
        elif args.option == "record":
            # record_to_file(data)
            textfile.write(str(time.time()) + ",")
            textfile.write(str(json.loads(args[0].decode()).get('data')[0]))
            textfile.write("\n")
        if (len(sec_data[0]) > 10):
            #random transform each value in sec data
            new_audio_sec_data = []
            for i in range(len(sec_data)):
                new_audio_sec_data.append(sec_data[i] * np.random.rand(len(sec_data[i])))
            
            coherence_results = []
            for i in range(len(new_audio_sec_data)):
                f, Cxy = coherence(sec_data[i], new_audio_sec_data[i], fs)
                max_c = np.max(Cxy)
                max_f = f[np.argmax(Cxy)]
                coherence_results.append([max_c, max_f])

            # y = [point[1] for point in coherence_results]
            # plt.plot(y)

            # plt.xlabel('Time')
            # plt.ylabel('Frequency (Hz)')
            # plt.title('Brain Waves vs. Audio Coherence')
            # plt.legend(['Delta', 'Theta', 'Alpha', 'Beta', 'Gamma'])

            # # Show the plot
            # plt.grid(True)
            # plt.show()

            sec_data = []
            for i in np.arange(5):
                sec_data.append([])

if __name__ == "__main__":
    run_main()

            


# print("Samples == {}".format(numSamples))
# print("Duration == {}".format(duration))
# print("Avg Sampling Rate == {}".format(numSamples / duration))

# plt.plot(raw_pulse_signal)
# plt.ylabel('raw analog signal')
# plt.show()
