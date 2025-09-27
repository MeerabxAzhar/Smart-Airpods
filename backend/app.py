from flask import Flask, jsonify, request
from flask_cors import CORS
import subprocess
import os
import signal
from RTT import RealTimeTranslator
import threading
import time

app = Flask(__name__)

# Global variable to track the ANC process
anc_process = None

# Global variable to track the Frequency Isolator process
isolation_process = None

# Global variable to track the main_isolator process
isolator_process = None

# Global variable to store Translator instance
translator_system = None
translator_thread = None

# Simple CORS configuration
CORS(app, origins=['http://localhost:3000'])

@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', 'http://localhost:3000')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
    response.headers.add('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
    return response

@app.route('/')
def home():
    return "Welcome to the Flask backend!"

@app.route('/run/main_anc', methods=['POST'])
def run_main_anc():
    global anc_process
    try:
        if request.method == 'POST':
            if anc_process is None:
                # Start the main_ANC.py script as a subprocess
                print("Starting main_ANC.py...")
                anc_process = subprocess.Popen(['python', 'main_ANC.py'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                return jsonify({"status": "success", "message": "ANC started"})
            else:
                return jsonify({"status": "error", "message": "ANC is already running"})
    except Exception as e:
        print(f"Error starting ANC: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/stop/main_anc', methods=['POST'])
def stop_main_anc():
    global anc_process
    try:
        if anc_process is not None:
            # Terminate the subprocess
            print("Stopping main_ANC.py...")
            os.kill(anc_process.pid, signal.SIGTERM)
            anc_process = None
            return jsonify({"status": "success", "message": "ANC stopped"})
        else:
            return jsonify({"status": "error", "message": "ANC is not running"})
    except Exception as e:
        print(f"Error stopping ANC: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/run/frequency_isolator', methods=['POST'])
def run_frequency_isolator():
    global isolation_process
    try:
        if isolation_process is None:
            # Start the frequencyisolator.py script as a subprocess
            print("Starting frequencyisolator.py...")
            isolation_process = subprocess.Popen(['python', 'frequencyisolator.py'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            return jsonify({"status": "success", "message": "Frequency Isolator started"})
        else:
            return jsonify({"status": "running", "message": "Frequency Isolator is already running"})
    except Exception as e:
        print(f"Error starting Frequency Isolator: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/stop/frequency_isolator', methods=['POST'])
def stop_frequency_isolator():
    global isolation_process
    try:
        if isolation_process is not None:
            # Terminate the subprocess
            print("Stopping frequencyisolator.py...")
            os.kill(isolation_process.pid, signal.SIGTERM)
            isolation_process = None
            return jsonify({"status": "success", "message": "Frequency Isolator stopped"})
        else:
            return jsonify({"status": "error", "message": "Frequency Isolator is not running"})
    except Exception as e:
        print(f"Error stopping Frequency Isolator: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/run/main_isolator', methods=['POST'])
def run_main_isolator():
    global isolator_process
    try:
        if isolator_process is None:
            # Start the main_isolator.py script as a subprocess
            print("Starting main_isolator.py...")
            isolator_process = subprocess.Popen(['python', 'main_isolator.py'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            return jsonify({"status": "success", "message": "Main Isolator started"})
        else:
            return jsonify({"status": "running", "message": "Main Isolator is already running"})
    except Exception as e:
        print(f"Error starting Main Isolator: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/stop/main_isolator', methods=['POST'])
def stop_main_isolator():
    global isolator_process
    try:
        if isolator_process is not None:
            # Terminate the subprocess
            print("Stopping main_isolator.py...")
            isolator_process.terminate()
            isolator_process = None
            return jsonify({"status": "success", "message": "Main Isolator stopped"})
        else:
            return jsonify({"status": "error", "message": "Main Isolator is not running"})
    except Exception as e:
        print(f"Error stopping Main Isolator: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

def run_translator_in_thread(language):
    global translator_system
    try:
        translator_system.translate_speech(language)
    except Exception as e:
        print(f"Error in Translator thread: {str(e)}")

@app.route('/run/translation', methods=['POST'])
def run_translation():
    global translator_system, translator_thread
    try:
        if request.method == 'POST':
            data = request.json
            language_name = data.get('language')
            
            if not language_name:
                return jsonify({"status": "error", "message": "Language not specified"}), 400
                
            # Create a mapping from language names to language codes
            language_codes = {
                'English': 'en',
                'Hindi': 'hi',
                'Spanish': 'es',
                'French': 'fr',
                'German': 'de',
                'Italian': 'it',
                'Japanese': 'ja',
                'Korean': 'ko',
                'Chinese': 'zh-cn'
            }
            
            # Get the language code from the language name
            language_code = language_codes.get(language_name)
            
            if not language_code:
                return jsonify({"status": "error", "message": f"Unsupported language: {language_name}"}), 400
            
            if translator_thread is None or not translator_thread.is_alive():
                # Start Translation
                print(f"Starting Translation system with language: {language_name} ({language_code})...")
                translator_system = RealTimeTranslator()
                translator_thread = threading.Thread(target=run_translator_in_thread, args=(language_code,))
                translator_thread.daemon = True
                translator_thread.start()
                return jsonify({"status": "success", "message": f"Translation started with {language_name}"})
            else:
                # Stop Translation
                print("Stopping Translation system...")
                if translator_system:
                    # Set the flag to stop the Translation system
                    translator_system.stop_event.set()
                    
                    # Wait for the thread to finish
                    if translator_thread and translator_thread.is_alive():
                        translator_thread.join(timeout=2)
                        
                        # If thread is still alive after timeout, force terminate
                        if translator_thread.is_alive():
                            print("Force terminating Translation thread...")
                    
                    # Clean up resources
                    translator_system.cleanup()
                    
                    # Reset variables
                    translator_system = None
                    translator_thread = None
                    
                    print("Translation system stopped")
                    return jsonify({"status": "success", "message": "Translation stopped"})
                else:
                    return jsonify({"status": "error", "message": "Translation system not running"})
    except Exception as e:
        print(f"Error in Translation: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
