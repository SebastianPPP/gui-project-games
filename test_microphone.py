import pyaudio

print("Start testu PyAudio...")

p = pyaudio.PyAudio()

try:
    print("Urządzenia audio:")
    for i in range(p.get_device_count()):
        info = p.get_device_info_by_index(i)
        print(i, info["name"], "| input channels:", info["maxInputChannels"])
except Exception as e:
    print("Błąd PyAudio:", e)

print("Koniec testu.")
