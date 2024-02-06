import os
import sys
from flask import Flask, render_template, request, jsonify
from werkzeug.utils import secure_filename
import demucs.separate
import subprocess

sys.path.insert(0, os.path.dirname(__file__))

def add_ffmpeg_to_path():
    # Add the directory containing ffmpeg to the PATH environment variable
    ffmpeg_path = "/home/ixra1300/software/ffmpeg"  # Update this with the actual path to ffmpeg
    
    if ffmpeg_path not in os.environ["PATH"]:
        os.environ["PATH"] += os.pathsep + ffmpeg_path
        print('FFMPEG added to path')
    
    os.environ['FFMPEG_PATH'] = ffmpeg_path
    os.environ['FFPROBE_PATH'] = ffmpeg_path


add_ffmpeg_to_path()

app = Flask(__name__)

app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['OUTPUT_FOLDER'] = 'static/output'
app.config['ALLOWED_EXTENSIONS'] = {'mp3'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/')
def index():
    return render_template('index.html')
    

@app.route('/test')
def test():
    output_directory = app.config['OUTPUT_FOLDER']
    try:
        # Separate vocals and accompaniment
        run_demucs_command( 'uploads/demo.mp3' )
        #demucs.separate.main(["--mp3", "--two-stems", "vocals", "-n", "mdx_extra", "uploads/demo.mp3"])
        return jsonify({'success': 'Audio separation completed', 'output_directory': output_directory})
    except Exception as e:
        print(f'RJ Error during audio separation: {e}')
        return jsonify({'error': f'Error during audio separation: {str(e)}'})


@app.route('/separate_audio', methods=['POST'])
def separate_audio():
    # Check if the post request has the file part
    if 'audio_file' not in request.files:
        return jsonify({'error': 'No file part'})

    audio_file = request.files['audio_file']

    # Check if the file is empty
    if audio_file.filename == '':
        return jsonify({'error': 'No selected file'})

    # Check if the file type is allowed
    if not allowed_file(audio_file.filename):
        return jsonify({'error': 'Invalid file type'})

    # Save the uploaded file to a temporary location
    temp_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(audio_file.filename))
    audio_file.save(temp_path)

    # Define the output directory
    output_directory = app.config['OUTPUT_FOLDER']

    try:
        # Separate vocals and accompaniment
        run_demucs_command( temp_path )
        return jsonify({'success': 'Audio separation completed', 'output_directory': output_directory})
    except Exception as e:
        print(f'RJ Error during audio separation: {e}')
        return jsonify({'error': f'Error during audio separation: {str(e)}'})
    finally:
        # Clean up: remove the uploaded audio file
        os.remove(temp_path)
        
        
def run_demucs_command(path_to_audio_file):
    print('[Dev Guy] Starting track separation ...')
    command = [
        'python',
        '-m',
        'demucs.separate',
        '-d',
        'cpu',
        '--mp3',
        #f'--mp3-bitrate {bitrate}',
        path_to_audio_file
    ]

    try:
        subprocess.run(command, check=True)
        print('[Dev Guy] Track Separation success! :)')
    except subprocess.CalledProcessError as e:
        print(f"Error executing demucs command: {e}")
        

# Executed on prod
application = app

if __name__ == '__main__':
    app.run(debug=True)
