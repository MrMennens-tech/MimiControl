# MimiControl ⌨️😊

**MimiControl** is een op maat gemaakte, open-source toegankelijkheidsapplicatie die unieke gezichtsuitdrukkingen (mimiek) omzet in toetsenbordaanslagen of sneltoetscombinaties. 

Dit project is specifiek gebouwd voor gebruikers met zware spasmen waarbij standaard software tekortschiet, omdat deze vaak geen complexe, gecombineerde triggers (AND-logica) of sterk afwijkende gezichtsbewegingen ondersteunen.

## 🎯 Waarom MimiControl?
Voor de eerste gebruiker van deze app was de trigger een specifieke lach gecombineerd met het bollen van de tong in de mond. Door spasmen was live kalibreren frustrerend en onnauwkeurig. MimiControl lost dit op door een unieke **Video Kalibratie Modus** toe te voegen, in combinatie met een **Anti-spasme filter**.

## ✨ Features
- **Video Kalibratie:** Upload een korte video van de gebruiker. De software analyseert de video frame-voor-frame om de uiterste piekwaarden van de unieke gezichtsuitdrukking te meten en op te slaan.
- **Vrije Toetskeuze:** Stel eenvoudig in welke toets (bijv. Spatie of Enter) of toetsencombinatie geactiveerd moet worden als de trigger wordt herkend. Ideaal voor *switch access* (schakelaarbediening).
- **Live Toetsenbordbesturing:** Gebruikt de webcam en de opgeslagen kalibratiedata om met hoge precisie toetsenbordacties uit te voeren.
- **Anti-Spasme Filter:** Een actie wordt pas uitgevoerd als de unieke drempelwaarden voor een instelbare tijd (bijv. 0.5 seconden) aaneengesloten worden vastgehouden.

## 🛠️ Tech Stack
- **Taal:** Python
- **Gezichtsdetectie:** Google MediaPipe (`mediapipe.solutions.face_mesh`)
- **Beeldverwerking:** OpenCV (`cv2`)
- **Toetsenbordbesturing:** PyAutoGUI
- **Interface:** Tkinter (voor file-dialogs)

## 🚀 Installatie

### Vereisten
- Python 3.9 of hoger
- Een webcam (voor de Live Modus)

### Stap 1: Clone de repository
```bash
git clone <repo-url>
cd mimicontrol
```

### Stap 2: Installeer de dependencies
```bash
pip install -r requirements.txt
```

Dit installeert:
| Package | Doel |
|---------|------|
| `opencv-python` | Video en webcam verwerking |
| `mediapipe` | Google's Face Mesh gezichtsdetectie |
| `pyautogui` | Simuleren van toetsenbordaanslagen |

> **Let op:** Tkinter is standaard meegeleverd met Python op Windows. Op Linux: `sudo apt install python3-tk`

### Stap 3: Start de applicatie
```bash
python mimicontrol.py
```

## 📖 Gebruik

### Hoofdmenu
Bij het starten verschijnt een menu met drie opties:

```
  [1]  Kalibreren via Video
  [2]  Sneltoets / Actie instellen
  [3]  Live Besturing starten
  [4]  Huidige configuratie bekijken
  [0]  Afsluiten
```

### Optie 1: Kalibreren
Je kiest uit twee methodes:

**[A] Video importeren** – analyseer een bestaand videobestand:
1. Neem een korte video op (bijv. 5-10 seconden) waarin de gebruiker de triggeruitdrukking maakt (lach + tongbol).
2. Selecteer de video via de file-dialog die opent.
3. De software analyseert de video frame-voor-frame en toont de Face Mesh in realtime.
4. Na analyse worden de piekwaarden getoond en opgeslagen in `config.json` (met 10% marge).

**[B] Direct opnemen** – gebruik de webcam:
1. De webcam opent met een live preview en Face Mesh, zodat je het gezicht kunt positioneren.
2. Druk op **Spatie** als je klaar bent — er volgt een countdown van 3 seconden.
3. Daarna loopt een opname van 10 seconden met een rode REC-indicator.
4. Voer tijdens de opname de triggeruitdrukking uit.
5. Na de opname worden de piekwaarden geanalyseerd en opgeslagen, en het bestand wordt bewaard als `kalibratie_opname.mp4`.

### Optie 2: Sneltoets instellen
- Voer een enkele toets in (bijv. `space`, `enter`) of een combinatie (bijv. `ctrl+c`, `alt+tab`).
- Optioneel: pas de **cooldown** (standaard 2s) en **vasthoudtijd** (standaard 0.5s) aan.

### Optie 3: Live Besturing
- De webcam opent met de Face Mesh gevisualiseerd.
- Een overlay toont realtime meetwaarden, drempelwaarden en de status.
- Wanneer de trigger wordt herkend en 0.5s vastgehouden, wordt de ingestelde toets uitgevoerd.
- Visuele feedback: gele flash rond het beeld bij een uitgevoerde actie.
- Druk op `q` in het videovenster om te stoppen.

## 📁 Projectstructuur

```
mimicontrol/
├── mimicontrol.py        # Hoofdmenu / entrypoint
├── calibratie.py         # Video kalibratie module
├── actie_instellen.py    # Toetsconfiguratie
├── live_modus.py         # Live webcam besturing
├── gezichtsdetectie.py   # Face Mesh detectie & meetfuncties
├── config_beheer.py      # Configuratiebeheer (config.json)
├── config.json           # Opgeslagen drempelwaarden & instellingen
├── requirements.txt      # Python dependencies
└── Readme.md
```

## ⚙️ Configuratie (config.json)

Na kalibratie en het instellen van een actie ziet `config.json` er bijvoorbeeld zo uit:

```json
{
    "drempelwaarde_breedte": 0.8234,
    "drempelwaarde_hoogte": 0.1456,
    "toetsen": ["space"],
    "cooldown": 2.0,
    "vasthoud_tijd": 0.5
}
```

| Instelling | Beschrijving |
|------------|-------------|
| `drempelwaarde_breedte` | Minimale genormaliseerde mondbreedte voor trigger |
| `drempelwaarde_hoogte` | Minimale genormaliseerde liphoogte voor trigger |
| `toetsen` | De toets(en) die worden uitgevoerd |
| `cooldown` | Wachttijd in seconden na een actie voordat de volgende mag |
| `vasthoud_tijd` | Hoe lang de trigger aaneengesloten moet worden vastgehouden |
