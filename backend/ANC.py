import numpy as np
import pyaudio
import threading
import matplotlib.pyplot as plt
from scipy import signal
import webrtcvad

class VoiceActivityDetector:
    def __init__(self, sample_rate=16000, frame_duration=30):
        self.vad = webrtcvad.Vad(3)  # Aggressiveness mode 3
        self.sample_rate = sample_rate
        self.frame_duration = frame_duration
        self.frame_len = int(sample_rate * frame_duration / 1000)

    def is_speech(self, audio_frame):
        # Ensure the audiopip frame is the correct length
        if len(audio_frame) != self.frame_len:
            return False
        # Ensure the audio frame is in the correct format (16-bit PCM)
        audio_frame = (audio_frame * 32768).astype(np.int16)
        return self.vad.is_speech(audio_frame.tobytes(), self.sample_rate)

# In the RealTimeANC class, modify the callback method:
def callback(self, in_data, frame_count, time_info, status):
    audio_data = np.frombuffer(in_data, dtype=np.int16).astype(np.float32) / 32768.0
    
    # Ensure the frame length matches what VAD expects
    if len(audio_data) != self.vad.frame_len:
        is_speech = False
    else:
        is_speech = self.vad.is_speech(audio_data)
    

class SimpleNoiseReducer:
    def __init__(self, frame_len=1024, smoothing=0.98):
        self.frame_len = frame_len
        self.smoothing = smoothing
        self.noise_spectrum = None

    def reduce_noise(self, frame):
        spectrum = np.fft.rfft(frame)
        mag_spectrum = np.abs(spectrum)
        phase_spectrum = np.angle(spectrum)
        
        if self.noise_spectrum is None:
            self.noise_spectrum = mag_spectrum
        else:
            self.noise_spectrum = self.smoothing * self.noise_spectrum + (1 - self.smoothing) * mag_spectrum

        gain = np.maximum(1 - self.noise_spectrum / (mag_spectrum + 1e-10), 0)
        enhanced_spectrum = mag_spectrum * gain * np.exp(1j * phase_spectrum)
        return np.fft.irfft(enhanced_spectrum)

class RealTimeANC:
    def __init__(self, input_device_index=None, output_device_index=None):
        self.CHUNK = 1024
        self.FORMAT = pyaudio.paFloat32
        self.CHANNELS = 1
        self.RATE = 16000
        self.noise_reducer = SimpleNoiseReducer(frame_len=self.CHUNK)
        self.p = pyaudio.PyAudio()
        self.stream = None
        self.is_running = False
        self.plot_data = {'original': [], 'filtered': []}
        self.plot_lock = threading.Lock()
        self.input_device_index = input_device_index
        self.output_device_index = output_device_index

    def audio_callback(self, in_data, frame_count, time_info, status):
        audio_data = np.frombuffer(in_data, dtype=np.float32)
        processed = self.noise_reducer.reduce_noise(audio_data)

        with self.plot_lock:
            self.plot_data['original'].extend(audio_data)
            self.plot_data['filtered'].extend(processed)

            if len(self.plot_data['original']) > self.RATE * 5:  # Keep last 5 seconds
                self.plot_data['original'] = self.plot_data['original'][-self.RATE * 5:]
                self.plot_data['filtered'] = self.plot_data['filtered'][-self.RATE * 5:]

        return (processed.astype(np.float32).tobytes(), pyaudio.paContinue)

    def start_stream(self):
        self.stream = self.p.open(format=self.FORMAT,
                                  channels=self.CHANNELS,
                                  rate=self.RATE,
                                  input=True,
                                  output=True,
                                  input_device_index=self.input_device_index,
                                  output_device_index=self.output_device_index,
                                  stream_callback=self.audio_callback,
                                  frames_per_buffer=self.CHUNK)
        
        self.is_running = True
        print("Stream started")


    def stop_stream(self):
        if self.stream is not None:
            self.stream.stop_stream()
            self.stream.close()
        self.is_running = False
        print("Stream stopped")

    def update_plot(self):
        with self.plot_lock:
            plt.clf()
            plt.subplot(211)
            plt.title('Original Audio')
            plt.plot(self.plot_data['original'])
            plt.subplot(212)
            plt.title('Filtered Audio')
            plt.plot(self.plot_data['filtered'])
            plt.tight_layout()
        plt.pause(0.01)

    def run(self):
        self.start_stream()
        plt.ion()
        plt.figure(figsize=(10, 6))

        try:
            while self.is_running:
                self.update_plot()
        except KeyboardInterrupt:
            print("Stopping...")
        finally:
            self.stop_stream()
            self.p.terminate()
            plt.ioff()
            plt.show()

if __name__ == "__main__":
    anc_system = RealTimeANC()
    anc_system.run()