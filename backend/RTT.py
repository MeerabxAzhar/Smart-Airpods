import speech_recognition as sr
from googletrans import Translator, LANGUAGES
from gtts import gTTS
import playsound
import os
import time
import tempfile
import threading # For concurrency
import queue     # Not strictly used in this version, but good for more complex async tasks
import uuid      # For unique temporary filenames
import shutil    # For robust directory cleanup

class RealTimeTranslator:
    def __init__(self):
        """Initializes the translator components and threading helpers."""
        self.recognizer = sr.Recognizer()
        self.translator = Translator()
        try:
            self.temp_dir = tempfile.mkdtemp()
            print(f"Temporary directory created at: {self.temp_dir}")
        except Exception as e:
            print(f"Error creating temporary directory: {e}")
            self.temp_dir = "." # Fallback to current directory if temp fails

        self.stop_event = threading.Event() # To signal threads to stop gracefully

        # --- Variables for pausing listener during playback to prevent feedback ---
        self.active_playbacks = 0           # Counter for ongoing playsound instances
        self.playback_lock = threading.Lock() # Lock to protect access to the counter
        # --- End feedback prevention variables ---

        # Available languages for translation - now using language names as keys
        self.languages = {
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
        print("RealTimeTranslator Initialized.")


    def get_target_language(self):
        """Displays available languages and prompts the user for selection by name."""
        print("\nAvailable languages for translation:")
        for lang_name in self.languages.keys():
            print(f"- {lang_name}")
        
        while True:
            choice = input("\nEnter the target language name: ")
            # Case-insensitive matching
            choice = choice.capitalize()
            if choice in self.languages:
                return self.languages[choice]
            print(f"Invalid choice. Please enter one of: {', '.join(self.languages.keys())}")


    def _play_audio_and_cleanup(self, file_path):
        """
        Plays the audio file using playsound, manages the active playback counter,
        and ensures the temporary file is deleted afterwards.
        Runs in its own thread.
        """
        # --- Increment active playback count (thread-safe) ---
        with self.playback_lock:
            self.active_playbacks += 1
            current_playbacks = self.active_playbacks # Get count inside lock
        # ---

        try:
            print(f"Playing: {os.path.basename(file_path)} (Active playbacks: {current_playbacks})")
            playsound.playsound(file_path)
            print(f"Finished playing: {os.path.basename(file_path)}")
        except Exception as e:
            # Need to catch potential playsound errors (e.g., file not found briefly, codec issues)
            print(f"Error playing sound {os.path.basename(file_path)}: {e}")
        finally:
            # --- Decrement active playback count (thread-safe) ---
            with self.playback_lock:
                self.active_playbacks -= 1
            # ---
            # Ensure cleanup happens even if playback fails
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    # print(f"Deleted temp file: {os.path.basename(file_path)}") # Optional debug print
            except Exception as e:
                print(f"Error deleting temp file {os.path.basename(file_path)}: {e}")


    def _process_and_speak(self, audio, target_lang):
        """
        Worker function executed in a separate thread.
        Recognizes speech, translates, synthesizes TTS, and starts playback.
        """
        # Check if stop signal was received before starting expensive operations
        if self.stop_event.is_set():
            return

        try:
            # 1. Convert speech to text
            print("Recognizing...")
            text = self.recognizer.recognize_google(audio)
            if not text.strip():
                print("Recognition returned empty text.")
                return # Don't process empty or whitespace-only text

            print(f"\nYou said: {text}")

            # Check again before network calls
            if self.stop_event.is_set(): return

            # 2. Translate the text
            print("Translating...")
            translation = self.translator.translate(text, dest=target_lang)
            translated_text = translation.text
            print(f"Translation: {translated_text}")

            # Check again before TTS generation
            if self.stop_event.is_set(): return

            # 3. Convert translation to speech (TTS)
            print("Generating speech...")
            # Generate a unique filename for each utterance
            temp_filename = f"speech_{uuid.uuid4()}.mp3"
            temp_file_path = os.path.join(self.temp_dir, temp_filename)

            tts = gTTS(text=translated_text, lang=target_lang, slow=False)
            tts.save(temp_file_path)
            print(f"Saved speech to: {os.path.basename(temp_file_path)}")

            # Check one last time before starting playback thread
            if self.stop_event.is_set():
                try:
                    if os.path.exists(temp_file_path): os.remove(temp_file_path)
                except: pass # Ignore cleanup errors if stopping
                return

            # 4. Play the audio in yet another thread to allow this worker thread to finish
            #    The _play_audio_and_cleanup method handles its own lifecycle.
            playback_thread = threading.Thread(target=self._play_audio_and_cleanup, args=(temp_file_path,))
            playback_thread.daemon = True # Allow main program to exit even if playback thread hangs
            playback_thread.start()

        except sr.UnknownValueError:
            print("Google Speech Recognition could not understand audio")
        except sr.RequestError as e:
            print(f"Could not request results from Google Speech Recognition service; {e}")
        except Exception as e:
            # Catch potential errors during translation or gTTS
            print(f"Error in processing thread: {str(e)}")


    def translate_speech(self, target_lang):
        """
        Main loop: Listens for audio and dispatches processing to worker threads.
        Includes logic to pause listening while audio is playing back.
        """
        try:
            with sr.Microphone() as source:
                print("\nAdjusting for ambient noise...")
                self.recognizer.adjust_for_ambient_noise(source, duration=1)

                # --- Set Recognizer attributes AFTER adjustment ---
                # How long silence indicates the end of a phrase
                self.recognizer.pause_threshold = 1.0  # Adjust this value (0.8 default, 1.0-1.5 often good)
                # Disable dynamic energy threshold adjustment after initial calibration
                # This can sometimes help prevent minor background noises (like playback start)
                # from triggering recognition, but might make it less sensitive to quiet speech.
                self.recognizer.dynamic_energy_threshold = False
                # --- End Attributes ---

                print(f"Initial energy threshold: {self.recognizer.energy_threshold:.2f}")
                print(f"Pause threshold set to: {self.recognizer.pause_threshold}s")
                print("\nListening... (Press Ctrl+C to exit)")

                while not self.stop_event.is_set():
                    # --- Wait until no audio is playing back ---
                    is_playing = True
                    while is_playing and not self.stop_event.is_set():
                         with self.playback_lock:
                             if self.active_playbacks == 0:
                                 is_playing = False # Safe to listen
                         if is_playing:
                             # Optional: print a message indicating waiting state
                             # print(".", end="", flush=True)
                             time.sleep(0.1) # Wait briefly before checking again to avoid busy-waiting
                    # --- Listener is paused if loop above ran ---

                    if self.stop_event.is_set(): break # Exit main loop if stop signal received

                    try:
                        print("\nListening for next phrase...")
                        # Listen for audio input. timeout ensures the loop doesn't block indefinitely
                        # if there's no speech, allowing the stop_event check to run.
                        audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=10)

                        # If audio is captured, process it in a background thread
                        print("Audio captured, processing in background...")
                        worker_thread = threading.Thread(target=self._process_and_speak, args=(audio, target_lang))
                        worker_thread.daemon = True # Allow main program to exit even if workers are running
                        worker_thread.start()

                    except sr.WaitTimeoutError:
                        # No speech detected within the timeout period, just loop back and listen again
                        # print("Timeout waiting for speech...") # Optional debug print
                        continue
                    except Exception as e:
                        # Catch errors during the listen() call itself
                        print(f"Error in listening loop: {str(e)}")
                        # Avoid spamming errors if there's a persistent issue (e.g., mic disconnected)
                        time.sleep(1)

        except KeyboardInterrupt:
            print("\nCtrl+C detected. Stopping translation...")
        except Exception as e:
            print(f"\nAn critical error occurred in translate_speech: {str(e)}")
        finally:
            print("Exiting main listening loop.")
            self.stop_event.set() # Signal all threads to stop


    def cleanup(self):
        """Cleans up resources, particularly the temporary directory."""
        print("Cleaning up temporary files...")
        self.stop_event.set() # Ensure threads know to stop
        # Give threads a very brief moment to finish file operations before deletion
        time.sleep(0.5)
        try:
            if hasattr(self, 'temp_dir') and os.path.exists(self.temp_dir):
                # Use shutil.rmtree for robust directory removal
                shutil.rmtree(self.temp_dir, ignore_errors=True)
                print(f"Removed temporary directory: {self.temp_dir}")
        except Exception as e:
            print(f"Error during cleanup: {e}")

# --- Main execution block ---
def main():
    """Sets up and runs the translator."""
    translator = RealTimeTranslator()
    try:
        target_language = translator.get_target_language()
        translator.translate_speech(target_language)
    except Exception as e:
        print(f"An error occurred in main execution: {str(e)}")
    finally:
        # Ensure cleanup runs even if errors occur
        translator.cleanup()
        print("Program finished.")

if __name__ == "__main__":
    main()