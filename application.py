import os
from flask import Flask, render_template, request, jsonify
from werkzeug.utils import secure_filename
import demucs.separate

app = Flask(__name__)

app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['OUTPUT_FOLDER'] = 'static/output'
app.config['ALLOWED_EXTENSIONS'] = {'mp3'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/')
def index():
    return render_template('index.html')

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
        demucs.separate.main(["--mp3", "--segment", '8', "--two-stems", "vocals", "-n", "mdx_extra", temp_path])
        return jsonify({'success': 'Audio separation completed', 'output_directory': output_directory})
    except Exception as e:
        return jsonify({'error': f'Error during audio separation: {str(e)}'})
    finally:
        # Clean up: remove the uploaded audio file
        os.remove(temp_path)

# Executed on prod
application = app

if __name__ == '__main__':
    app.run(debug=True)
