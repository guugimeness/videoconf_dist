import sounddevice as sd
import numpy as np

sd.default.device = (1, 3)  # ajuste aqui

fs = 16000
t = np.linspace(0, 1, fs)
audio = 0.2 * np.sin(2 * np.pi * 440 * t)

sd.play(audio, fs)
sd.wait()