import requests
import base64
import io
import os
import json
import argparse
import configparser
import time
import zipfile
from tqdm import tqdm

url_root = "http://164.90.158.133:8080"
url_get_speech = "/to_speech"
url_get_speaker = "/get_speaker"
url_get_audios = "/is_ready"
path_menu = './Menu.ini'
path_st = './Sentences.ini'
path_cus = './Customer.ini'

# read the ini file to string
def read_config(path_to_ini):
    with open(path_to_ini, "r") as f:
        config = f.read()
    return config

# tell if the audio file is ready, since generating all 
# audio files will probably takes a long time and it will time out
# the client.
def is_ready():
    pass

# get all speech audio files and unzip them into './audios/'
def get_speeches(menu, customers, sentences, output):
    req = {}
    req["menu"] = read_config(menu)
    req["customers"] = read_config(customers)
    req["sentences"] = read_config(sentences)
    result = requests.post(url_root+url_get_speech, json=req)
    prog_old = 0
    prog_new = 0
    # download the file when it is ready
    # or maybe we can print a progress bar here
    if result.status_code != 200:
        print("Log:\t%s"%result.text)
    else:
        print("Log:\t%s"%result.text)
        if "processing" in result.text:
            pid = result.text.split(" ")[-1]
            bar = tqdm()
            bar.total = 100
            while True:
                # update every 10s
                time.sleep(5)
                result = requests.post(url_root+url_get_audios, data=pid, stream=True)
                if result.status_code == 200:
                    if os.path.exists(output) == False:
                        os.mkdir(output)
                    zip_path_temp = os.path.join(output, "speech_audios.zip")
                    with open(zip_path_temp, "wb") as f:
                        f.write(result.content)
                    with zipfile.ZipFile(zip_path_temp, 'r') as zip_ref:
                        zip_ref.extractall(output)

                    # clean up
                    os.remove(zip_path_temp)
                    break
                else:
                    try:
                        prog_old = prog_new
                        prog_new = float(result.text)
                        bar.update(prog_new - prog_old)
                    except:
                        pass

# get and save speakers into ./speakers.ini
def get_speakers(path_to_speaker):
    result = requests.get(url_root+url_get_speaker)
    if result.status_code == 200:
        speakers = result.json()
        if type(speakers) == str:
            speakers = speakers.strip("[").strip("]").split(",")
        config_speakers = configparser.ConfigParser()
        dict_speakers = {}
        # import pdb
        # pdb.set_trace()
        for idx, spk in enumerate(speakers):
            dict_speakers["%03d"%idx] = spk.strip(" ").strip("\"")
        config_speakers["speakers"] = dict_speakers
        with open(path_to_speaker, "w") as f:
            config_speakers.write(f)
        print("Log:\tspeakers are saved to %s"%path_to_speaker)
    else:
        print("Error:\tfailed to get correct speak info")

# verify if all needed audio files are ready
def verify_speeches(menu, customers, sentences):
    pass

if __name__ == "__main__":
    # parse cmd lines
    parser = argparse.ArgumentParser()
    parser.add_argument('--speech', action='store_true',
        help="get all speech audios in a zip file")
    parser.add_argument("--samples", action='store_true',
        help="generate samples speaked by all speakers")
    parser.add_argument("--dinnerset", action='store_true',
        help="generate all speeches for asking more dinner sets")

    parser.add_argument('--speaker', action='store_true',
        help="get all speaker id and put them into ./speaker.ini")
    parser.add_argument("--misc", type=str, default='./Misc.ini',
        help="the path to misc config file, default is ./Misc.ini")
    parser.add_argument("--customers", type=str, default='./Customer (1).ini',
        help="the path to customer config file, default is ./Customer.ini")
    parser.add_argument("--sentences", type=str, default='./Sentences.ini',
        help="the path to sentence template file, default is ./Sentences.ini")
    parser.add_argument("--speakers", type=str, default='./Speakers.ini',
        help="the path to save speaker keys, default is ./Speakers.ini")
    parser.add_argument("--output", type=str, default='./speech_audios',
        help="the path to save generated audios")

    args = parser.parse_args()

    # send request and get result
    if args.speech:
        get_speeches(args.menu, args.customers, args.sentences, args.output)
    if args.speaker:
        get_speakers(args.speakers)
    if args.samples:
        pass
    if args.dinnerset:
        pass

