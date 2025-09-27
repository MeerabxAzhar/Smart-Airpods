import sounddevice as sd
import numpy as np
import tkinter as tk
from tkinter import ttk, messagebox
from scipy.signal import butter, lfilter

SAMPLE_RATE = 16000
BLOCK_SIZE = 1024

class FrequencyControlApp:
    def __init__(self, master):
        self.master = master
        self.master.title("Frequency Control - AuroraFX")

        # Store frequency bands and gains
        self.bands = []
        self.gain_vars = []

        # GUI components
        self.band_frame = tk.Frame(master)
        self.band_frame.pack(pady=10)

        tk.Button(master, text="Add Frequency Band", command=self.add_band).pack(pady=5)
        tk.Button(master, text="Start Processing", command=self.start_audio).pack(pady=5)
        tk.Button(master, text="Stop Processing", command=self.stop_audio).pack(pady=5)
        tk.Button(master, text="Quit", command=master.quit).pack(pady=5)

        self.stream = None
        self.is_running = False

    def butter_bandpass(self, lowcut, highcut, fs, order=5):
        nyquist = 0.5 * fs
        low = lowcut / nyquist
        high = highcut / nyquist
        b, a = butter(order, [low, high], btype='band')
        return b, a

    def bandpass_filter(self, data, lowcut, highcut, fs, order=5):
        b, a = self.butter_bandpass(lowcut, highcut, fs, order=order)
        return lfilter(b, a, data)

    def audio_callback(self, indata, outdata, frames, time, status):
        if status:
            print(f"Error in audio callback: {status}", flush=True)

        audio_data = indata[:, 0]  # Input audio data (mono)

        # Process each frequency band dynamically
        processed_audio = np.zeros_like(audio_data)
        for (lowcut_var, highcut_var), gain_var in zip(self.bands, self.gain_vars):
            # Extract numerical values from IntVar
            lowcut = lowcut_var.get()
            highcut = highcut_var.get()

            # Apply bandpass filter for the current band
            filtered_data = self.bandpass_filter(audio_data, lowcut, highcut, SAMPLE_RATE)
            processed_audio += filtered_data * gain_var.get()

        # Normalize to prevent clipping
        processed_audio = np.clip(processed_audio, -1.0, 1.0)
        outdata[:, 0] = processed_audio.astype(np.float32)

    def add_band(self):
        # Add a new frequency band control
        band_frame = tk.Frame(self.band_frame)
        band_frame.pack(pady=5)

        tk.Label(band_frame, text="Low Cutoff (Hz):").grid(row=0, column=0)
        low_cut = tk.IntVar(value=300)
        tk.Entry(band_frame, textvariable=low_cut, width=10).grid(row=0, column=1)

        tk.Label(band_frame, text="High Cutoff (Hz):").grid(row=0, column=2)
        high_cut = tk.IntVar(value=3000)
        tk.Entry(band_frame, textvariable=high_cut, width=10).grid(row=0, column=3)

        tk.Label(band_frame, text="Gain:").grid(row=0, column=4)
        gain = tk.DoubleVar(value=1.0)
        tk.Scale(band_frame, variable=gain, from_=0, to=3, resolution=0.1, orient=tk.HORIZONTAL).grid(row=0, column=5)

        # Add to internal lists
        self.bands.append((low_cut, high_cut))
        self.gain_vars.append(gain)

        # Remove button
        remove_button = tk.Button(band_frame, text="Remove", command=lambda: self.remove_band(band_frame, low_cut, high_cut, gain))
        remove_button.grid(row=0, column=6)

    def remove_band(self, band_frame, low_cut, high_cut, gain):
        # Remove band from lists and GUI
        band_frame.destroy()
        self.bands.remove((low_cut, high_cut))
        self.gain_vars.remove(gain)

    def start_audio(self):
        try:
            if self.is_running:
                return
            self.is_running = True
            self.stream = sd.Stream(
                samplerate=SAMPLE_RATE,
                blocksize=BLOCK_SIZE,
                channels=1,
                dtype='float32',
                callback=self.audio_callback
            )
            self.stream.start()
            self.master.after(0, lambda: messagebox.showinfo("Info", "Audio processing started."))
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start audio processing: {e}")

    def stop_audio(self):
        try:
            if self.stream is not None:
                self.stream.stop()
                self.stream.close()
                self.stream = None
                self.is_running = False
                self.master.after(0, lambda: messagebox.showinfo("Info", "Audio processing stopped."))
        except Exception as e:
            messagebox.showerror("Error", f"Failed to stop audio processing: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = FrequencyControlApp(root)
    root.mainloop() 