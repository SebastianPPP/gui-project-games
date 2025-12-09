Snake + Chrome Dino
============================= 

Opis
----
Projekt zawiera dwie minigry sterowane głosem/gestami uruchamiane z menu:
- Snake (sterowanie gestami dłoni przez kamerę; awaryjnie strzałki na klawiaturze)
- Dino (sterowanie głośnym dźwiękiem z mikrofonu; awaryjnie spacja/strzałka w górę)

Wymagania
---------
- Python 3.10+ (testowane z 3.12)
- Kamera internetowa (do sterowania gestami w Snake)
- Mikrofon (do sterowania głośnością w Dino)
- Pakiety: pygame, opencv-python, mediapipe, pyaudio, numpy

Instalacja zależności
----------------------------------
```
python -m pip install pygame opencv-python mediapipe pyaudio numpy
```

Uruchomienie
------------
```
python .\menu.py
```
W menu wybierz:
- `1` lub Enter na Snake
- `2` lub Enter na Dino
- `ESC` aby wyjść

Sterowanie - Snake 
--------------------------------
- Gesty dłoni (kamera):
	- Góra: wyprostowany tylko palec wskazujący
	- Dół: dwa palce (V) – wskazujący + środkowy
	- Lewo: „L” (kciuk + wskazujący wyprostowane)
	- Prawo: pięść (wszystkie palce zgięte)
- Klawiatura (fallback lub bez kamery): strzałki
- Wyjście z okna gry: zamknij okno Pygame (gra wróci do menu)

Sterowanie – Dino 
----------------------------------
- Mikrofon: głośny dźwięk (np. klaśnięcie / okrzyk „hop”) wywołuje skok
- Klawiatura (fallback lub bez mikrofonu): spacja albo strzałka w górę
- Po zderzeniu: ekran GAME OVER i powrót do menu

Autowykrywanie urządzeń
------------------------
- Snake: automatycznie szuka kamery; gdy brak – gra działa na klawiaturze
- Dino: automatycznie szuka mikrofonu; gdy brak – gra działa na klawiaturze

Problemy i wskazówki
--------------------
- Brak kamery/mikrofonu: gra przełączy się na sterowanie klawiaturą
- Okno kamery się nie zamyka: zamknij okno gry Pygame; wątek kamery kończy się po GAME OVER lub zamknięciu gry
- Audio na Windows: jeśli `pyaudio` sprawia kłopoty, zainstaluj binarkę: `pip install pipwin` potem `pipwin install pyaudio`

Struktura
---------
- `menu.py` – główne menu gier
- `vc_snake.py` – Snake sterowany gestami
- `dino_chrome.py` – Dino sterowany głośnością
