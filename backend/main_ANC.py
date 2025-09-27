# -*- coding: utf-8 -*-
"""
Real-time Audio Processor - CONSTANT SILENCE OUTPUT

Listens to microphone input and performs VAD analysis (for plotting).
However, the output sent to the speakers/headphones is ALWAYS silent,
regardless of whether speech is detected or not.
Includes real-time plotting of input and (silent) output waveforms.
"""

import numpy as np
import pyaudio
import threading
import matplotlib.pyplot as plt
import webrtcvad
import time
import sys # For flushing output

# --- Voice Activity Detector Class (Remains the same, used for analysis/plot) ---
class VoiceActivityDetector:
    """Detects speech in audio frames using WebRTC VAD."""
    def __init__(self, sample_rate=16000, frame_duration=30):
        """
        Initializes the VAD.

        Args:
            sample_rate (int): Sample rate in Hz (8k, 16k, 32k, 48k).
            frame_duration (int): Frame duration in ms (10, 20, 30).
        """
        if frame_duration not in [10, 20, 30]:
            raise ValueError("Invalid frame duration: must be 10, 20, or 30 ms")
        if sample_rate not in [8000, 16000, 32000, 48000]:
             raise ValueError("Invalid sample rate: must be 8k, 16k, 32k, or 48k Hz")

        self.vad = webrtcvad.Vad(3)  # Aggressiveness mode 3
        self.sample_rate = sample_rate
        self.frame_duration = frame_duration
        self.frame_len = int(sample_rate * frame_duration / 1000)
        print(f"VAD Initialized: Sample Rate={self.sample_rate}Hz, Frame Duration={self.frame_duration}ms, Frame Length={self.frame_len} samples")

    def is_speech(self, audio_frame_float32):
        """
        Checks if a float32 audio frame contains speech.

        Args:
            audio_frame_float32 (np.ndarray): Audio data frame (float32, range -1.0 to 1.0).

        Returns:
            bool: True if speech is detected, False otherwise.
        """
        if len(audio_frame_float32) != self.frame_len:
            return False
        audio_frame_int16 = np.clip(audio_frame_float32 * 32767, -32768, 32767).astype(np.int16)
        try:
            audio_frame_bytes = audio_frame_int16.tobytes()
            return self.vad.is_speech(audio_frame_bytes, self.sample_rate)
        except Exception as e:
            print(f"Error during VAD processing: {e}", file=sys.stderr)
            return False

# --- Real Time Audio Processing Class (Modified Callback) ---
class RealTimeAudioSilencer: # Renamed class for clarity
    """
    Manages the real-time audio stream, performs VAD (for plotting/info),
    but ALWAYS outputs silence.
    """
    def __init__(self, input_device_index=None, output_device_index=None):
        # --- Audio Stream Configuration ---
        self.RATE = 16000
        self.VAD_FRAME_MS = 30
        self.CHANNELS = 1
        self.FORMAT = pyaudio.paFloat32
        self.VAD_FRAME_SAMPLES = int(self.RATE * self.VAD_FRAME_MS / 1000)
        self.CHUNK = 1024

        print(f"Audio Stream Config: Rate={self.RATE}Hz, Chunk Size={self.CHUNK} samples")
        if self.CHUNK % self.VAD_FRAME_SAMPLES != 0:
            print(f"Note: CHUNK size ({self.CHUNK}) is not a perfect multiple of VAD frame size ({self.VAD_FRAME_SAMPLES}).")

        # --- VAD Initialization (Still used for analysis if desired) ---
        try:
            self.vad = VoiceActivityDetector(sample_rate=self.RATE, frame_duration=self.VAD_FRAME_MS)
        except ValueError as e:
            print(f"Error initializing VAD: {e}", file=sys.stderr)
            sys.exit(1)

        # --- PyAudio Setup ---
        self.p = pyaudio.PyAudio()
        self.stream = None
        self.is_running = False
        self.input_device_index = input_device_index
        self.output_device_index = output_device_index

        # --- Plotting Setup ---
        self.plot_data = {'original': [], 'output': []} # Output will always be zeros
        self.plot_lock = threading.Lock()
        self.plot_time_len_s = 2.0
        self.plot_max_len = int(self.RATE * self.plot_time_len_s)


    def audio_callback(self, in_data, frame_count, time_info, status):
        """
        Processes audio chunks: performs VAD analysis (optional), ALWAYS outputs silence.
        """
        # Convert incoming bytes to float32 numpy array
        audio_data_float32 = np.frombuffer(in_data, dtype=np.float32)

        # --- VAD Processing (Optional - can be commented out if analysis isn't needed) ---
        # You could still run VAD here if you wanted to log or visualize its decision,
        # even though it doesn't affect the output. For simplicity, we'll leave it out
        # of the main output logic path.
        # ---- Example: ----
        # num_samples = len(audio_data_float32)
        # num_vad_frames = num_samples // self.VAD_FRAME_SAMPLES
        # speech_detected_in_chunk = False
        # for i in range(num_vad_frames):
        #     start = i * self.VAD_FRAME_SAMPLES
        #     end = start + self.VAD_FRAME_SAMPLES
        #     vad_frame = audio_data_float32[start:end]
        #     if self.vad.is_speech(vad_frame):
        #         speech_detected_in_chunk = True
        #         break
        # # (Handle remainder if needed)
        # # Now 'speech_detected_in_chunk' holds the VAD result, but we ignore it below.
        # ---- End Example ----

        # --- Generate Output ---
        # >>> MODIFICATION: Always output silence <<<
        output_data = np.zeros_like(audio_data_float32)

        # --- Update Plot Data (Thread-Safe) ---
        with self.plot_lock:
            self.plot_data['original'].extend(audio_data_float32.tolist())
            self.plot_data['output'].extend(output_data.tolist()) # Will be zeros

            # Keep plot data buffer trimmed
            if len(self.plot_data['original']) > self.plot_max_len:
                self.plot_data['original'] = self.plot_data['original'][-self.plot_max_len:]
            if len(self.plot_data['output']) > self.plot_max_len:
                self.plot_data['output'] = self.plot_data['output'][-self.plot_max_len:]

        # Convert silent float32 numpy array back to bytes for PyAudio output
        out_data = output_data.astype(np.float32).tobytes()
        return (out_data, pyaudio.paContinue)

    # --- Methods start_stream, stop_stream, update_plot, run remain largely the same ---
    # --- (Minor change in update_plot title for clarity) ---

    def start_stream(self):
        """Initializes and starts the PyAudio stream."""
        # (Validation and stream opening code is identical to the previous version)
        try:
            if self.input_device_index is not None:
                input_dev_info = self.p.get_device_info_by_index(self.input_device_index)
                print(f"Using Input Device : Index {self.input_device_index} - {input_dev_info['name']}")
            if self.output_device_index is not None:
                output_dev_info = self.p.get_device_info_by_index(self.output_device_index)
                print(f"Using Output Device: Index {self.output_device_index} - {output_dev_info['name']}")
        except IOError as e:
            print(f"Error accessing audio device: {e}", file=sys.stderr); self.p.terminate(); sys.exit(1)
        except Exception as e:
            print(f"An unexpected error occurred during device setup: {e}", file=sys.stderr); self.p.terminate(); sys.exit(1)

        try:
            self.stream = self.p.open(format=self.FORMAT, channels=self.CHANNELS, rate=self.RATE,
                                      input=True, output=True,
                                      input_device_index=self.input_device_index,
                                      output_device_index=self.output_device_index,
                                      stream_callback=self.audio_callback,
                                      frames_per_buffer=self.CHUNK)
        except Exception as e:
            print(f"Error opening PyAudio stream: {e}", file=sys.stderr); self.p.terminate(); sys.exit(1)

        self.is_running = True
        self.stream.start_stream()
        print("Audio stream started. Output will ALWAYS be silent.")
        print("Close the plot window or press Ctrl+C in the terminal to stop.")

    def stop_stream(self):
        """Stops and closes the PyAudio stream."""
        # (Identical to the previous version)
        if self.stream is not None:
            if self.is_running and self.stream.is_active():
                self.stream.stop_stream()
            self.stream.close()
        self.is_running = False
        print("Audio stream stopped.")

    def update_plot(self, fig):
        """Updates the Matplotlib plot with the latest audio data."""
        # (Plotting code is identical, but the 'output' data will be flat)
        with self.plot_lock:
            if not self.plot_data['original'] or not self.plot_data['output']: return
            original_data = np.array(self.plot_data['original'])
            output_data = np.array(self.plot_data['output']) # This will be zeros
            time_axis = np.linspace(0, len(original_data) / self.RATE, num=len(original_data))

        plt.clf()
        ax1 = plt.subplot(211); plt.title('Microphone Input'); plt.plot(time_axis, original_data, color='lightblue')
        plt.ylabel("Amplitude"); plt.ylim([-1.0, 1.0]); plt.grid(True, linestyle=':', alpha=0.6); ax1.tick_params(labelbottom=False)

        ax2 = plt.subplot(212, sharex=ax1); plt.title('Output Audio (Always Silent)') # <-- Title changed
        plt.plot(time_axis, output_data, color='lightcoral'); # Color changed for silent output
        plt.xlabel(f"Time (Last {self.plot_time_len_s:.1f} Seconds)"); plt.ylabel("Amplitude")
        plt.ylim([-1.0, 1.0]); plt.grid(True, linestyle=':', alpha=0.6)

        plt.tight_layout(); fig.canvas.flush_events()

    def run(self):
        """Starts the audio stream and the plotting loop."""
        # (Identical to the previous version)
        self.start_stream()
        plt.ion(); fig = plt.figure(figsize=(10, 6))
        try:
            while self.is_running:
                if not plt.fignum_exists(fig.number):
                    print("Plot window closed, stopping application..."); self.is_running = False; break
                self.update_plot(fig)
                plt.pause(0.05)
        except KeyboardInterrupt: print("\nKeyboard interrupt received, stopping...")
        except Exception as e: print(f"\nAn unexpected error occurred in the main loop: {e}", file=sys.stderr)
        finally:
            self.stop_stream()
            if self.p: self.p.terminate(); print("PyAudio terminated.")
            plt.ioff()
            if plt.fignum_exists(fig.number): print("Final plot displayed."); plt.show()
            print("Application finished.")

# --- Helper function list_audio_devices (Identical) ---
def list_audio_devices(pyaudio_instance):
    """Prints available input and output audio devices."""
    print("-" * 30); print("Available Audio Devices:"); print("-" * 30)
    try:
        info = pyaudio_instance.get_host_api_info_by_index(0)
        numdevices = info.get('deviceCount', 0)
        if numdevices == 0: print("No audio devices found."); return
        for i in range(numdevices):
            try:
                dev_info = pyaudio_instance.get_device_info_by_index(i)
                print(f"Index {i}: {dev_info.get('name', 'Unknown Device')}")
                print(f"  - Max In Channels : {dev_info.get('maxInputChannels', 0)}")
                print(f"  - Max Out Channels: {dev_info.get('maxOutputChannels', 0)}")
                print(f"  - Default Rate    : {int(dev_info.get('defaultSampleRate', 0))} Hz")
                print("-" * 20)
            except Exception as e: print(f"Could not get info for device index {i}: {e}")
    except Exception as e: print(f"Could not retrieve audio device list: {e}", file=sys.stderr)
    print("-" * 30); sys.stdout.flush()

# --- Main Execution ---
if __name__ == "__main__":
    print("Initializing PyAudio to list devices...")
    p_temp = pyaudio.PyAudio(); list_audio_devices(p_temp); p_temp.terminate()

    # --- User Configuration (Select Input/Output Devices) ---
    INPUT_DEVICE_IDX = None
    OUTPUT_DEVICE_IDX = None
    # --- End User Configuration ---

    print("\nStarting Real-Time Audio Silencer...")
    # Use the renamed class
    audio_silencer_system = RealTimeAudioSilencer(input_device_index=INPUT_DEVICE_IDX,
                                                  output_device_index=OUTPUT_DEVICE_IDX)
    audio_silencer_system.run()