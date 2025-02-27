from datetime import datetime

from flask import Flask, flash, render_template, request, redirect, url_for, send_file, send_from_directory
from werkzeug.utils import secure_filename

import os, io

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "atomic-monument-449117-h0-9d24d55c9d36.json"
from google.cloud import speech
from google.protobuf import wrappers_pb2
from google.cloud import texttospeech_v1
from IPython.display import Audio, display

app = Flask(__name__)

# Configure upload folder
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'wav'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Configure tts folder
TTS_FOLDER = 'tts'
ALLOWED_EXTENSIONS = {'wav'}
app.config['TTS_FOLDER'] = TTS_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(TTS_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_files():
    files = []
    for filename in os.listdir(UPLOAD_FOLDER):
        if allowed_file(filename):
            files.append(filename)
            print(filename)
    files.sort(reverse=True)  
    return files

    #new code
def get_ttsfiles():
    ttsfiles =[]
    for filename in os.listdir(TTS_FOLDER):
        if allowed_file(filename):
            ttsfiles.append(filename)
            print(filename)
    ttsfiles.sort(reverse=True)
    return ttsfiles

@app.route('/')
def index():
    files = get_files()
    ttsfiles = get_ttsfiles()
    return render_template('index.html', files=files, ttsfiles=ttsfiles)

@app.route('/upload', methods=['POST'])
def upload_audio():
    if 'audio_data' not in request.files:
        flash('No audio data')
        return redirect(request.url)
    file = request.files['audio_data']
    if file.filename == '':
        flash('No selected file')
        return redirect(request.url)
    if file:
        filename = secure_filename(file.filename)
        filename = filename + datetime.now().strftime("%Y%m%d-%I%M%S%p") + '.wav'
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)

        # Modify this block to call the speech to text API
        # Save transcript to same filename but .txt
        #f = open(filename,'rb')
        #data = f.read()
        #f.close()
        client=speech.SpeechClient()

        with io.open(file_path, "rb") as audio_file:
            content = audio_file.read()
        audio=speech.RecognitionAudio(content=content)

        config=speech.RecognitionConfig(
        #encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        #sample_rate_hertz=44100,
            language_code="en-US",
            model="default",
            audio_channel_count=1,
            enable_word_confidence=True,
            enable_word_time_offsets=True,
        )

        # Detects speech in the audio file
        operation=client.long_running_recognize(config=config, audio=audio)

        #print("Waiting for operation to complete...")
        response=operation.result(timeout=90)



        txt = ''
        for result in response.results:
            txt = txt + result.alternatives[0].transcript + '\n'

        #print(txt)
        f = open('uploads/'+filename +'.txt','w')
        f.write(txt)
        f.close()
        #

    return redirect('/') #success

@app.route('/upload/<filename>')
def get_file(filename):
    return send_file(filename)
    
@app.route('/upload_text', methods=['POST'])
def upload_text():
    text = request.form['text']
    print(text)
    client = texttospeech_v1.TextToSpeechClient()
    input = texttospeech_v1.SynthesisInput()
    input.text = text   
    voice = texttospeech_v1.VoiceSelectionParams()
    voice.language_code = "en-UK"
    # voice.ssml_gender = "MALE"

    audio_config = texttospeech_v1.AudioConfig()
    audio_config.audio_encoding = "LINEAR16"

    req = texttospeech_v1.SynthesizeSpeechRequest(
    input=input,
    voice=voice,
    audio_config=audio_config,
    )

    response = client.synthesize_speech(request=req)
                                        
    wav = response.audio_content

    # save audio
    filename = datetime.now().strftime("%Y%m%d-%I%M%S%p") + '.wav'
    f = open('tts/'+filename,'wb')
    f.write(wav)
    f.close()

    #save text
    f = open('tts/'+filename + '.txt','w')
    f.write(text)
    f.close()
    #
    # Modify this block to call the stext to speech API
    # Save the output as a audio file in the 'tts' directory 
    # Display the audio files at the bottom and allow the user to listen to them

    return redirect('/') #success

@app.route('/script.js',methods=['GET'])
def scripts_js():
    return send_file('./script.js')

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/tts/<filename>')
def upload_file(filename):
    return send_from_directory(app.config['TTS_FOLDER'], filename)

if __name__ == '__main__':
    app.run(debug=True)