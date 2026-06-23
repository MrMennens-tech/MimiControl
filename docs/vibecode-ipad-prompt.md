# Vibe Code Prompt — MimiControl iPad App

Plak onderstaande prompt volledig in Vibe Code (Cursor) om een native iOS/iPad-app te bouwen.

---

## Prompt (kopieer vanaf hier)

```
Bouw een native iPad-app: **MimiControl** — gezichtsbesturing voor toegankelijkheid.

### Context

MimiControl is software waarmee mensen met ernstige motorische beperkingen (bijv. spasmen) hun apparaat kunnen bedienen via gezichtsuitdrukkingen in plaats van handen. Het project is ontwikkeld door Mennens.Tech. De bestaande Windows-app (Python + MediaPipe + CustomTkinter) heet **MimiControl Studio** en werkt als volgt:

**Kerngebruik (echte casus):** MimiControl is oorspronkelijk gebouwd voor een leerling met spasmen. Haar unieke, betrouwbare trigger is **lach + tong** — tong bollen in de mond of tong uitsteken. Op PC werkt `tongueOut` **niet**: MediaPipe levert slechts 51 van 52 blendshapes en mist `tongueOut` ([bekend issue](https://github.com/google/mediapipe/issues/4403)). De iPad-app met ARKit is daarom de **primaire kans** om tongdetectie wél betrouwbaar te bieden. Dit is geen nice-to-have maar de **hoofdreden** voor de iOS-versie.

- Webcam detecteert 51 ARKit-compatibele **blendshapes** (MediaPipe Face Landmarker — `tongueOut` ontbreekt)
- Gebruiker stelt **triggers** samen: meerdere blendshapes met drempelwaarden (AND-logica)
- Bij match + vasthoudtijd → simuleer toetsaanslag (pyautogui op Windows)
- **Anti-spasmefilter**: trigger moet X seconden vasthouden vóór actie
- **Cooldown** tussen acties
- **Profielen** met triggers, drempels, timing-instellingen

Referentie-architectuur Python-app (niet letterlijk kopiëren, wel conceptueel volgen):

| Concept | Python (MimiControl Studio) | iPad equivalent |
|---------|----------------------------|-----------------|
| Blendshape scores | `blendshape_detectie.py` | ARKit `ARFaceAnchor.blendShapes` |
| Trigger structuur | `{ naam, toetsen[], blendshapes: {naam: drempel} }` | Zelfde JSON-structuur |
| AND-logica | Alle blendshapes boven drempel | Identiek |
| Vasthoudtijd | `vasthoud_tijd` (default 0.5s) | Identiek |
| Cooldown | `cooldown` (default 2.0s) | Identiek |
| Profielen | JSON in `profielen/` map | SwiftData of JSON in app sandbox |
| Explorer/kalibratie | Live balkjes per blendshape | Live score-overzicht |
| tongueOut | **Niet beschikbaar** in MediaPipe (51/52) | **WEL beschikbaar** via ARKit — **MVP must-have** |
| mouthFunnel | Beschikbaar (tongbol-proxy) | Beschikbaar — combineer met `tongueOut` voor AND-triggers |

### Doel van de iPad-app

Een **native iPad-app** die gezichtsuitdrukkingen detecteert via de **front camera + ARKit Face Tracking** (TrueDepth of LiDAR/iPad Pro vereist voor ARFaceTrackingConfiguration). De app moet bruikbaar zijn als standalone besturingsinterface én als kalibratie-/configuratietool.

**Prioriteit #1:** betrouwbare detectie van `tongueOut` (tong uitsteken) en combinaties zoals `mouthSmileLeft/Right` + `tongueOut` of `mouthSmileLeft/Right` + `mouthFunnel` (lach + tongbol). Zonder werkende tongdetectie is de app voor de primaire gebruiker niet bruikbaar.

### Technische stack (voorkeur)

- **SwiftUI** voor UI
- **ARKit** (`ARFaceTrackingConfiguration`, `ARSession`, `ARSCNView` of `ARView` via RealityKit)
- **RealityKit** optioneel voor face mesh visualisatie
- **SwiftData** of Codable JSON voor profielen/triggers
- **Combine** of `@Observable` voor live state
- Minimum deployment: iOS 17 / iPadOS 17
- Taal UI: **Nederlands**

### Core features — MVP (must have)

**0. Tongdetectie (`tongueOut`) — HOOGSTE PRIORITEIT**

Dit is de reden dat de iPad-app gebouwd wordt. Implementeer en test dit vóór alle andere features.

- Lees `tongueOut` live uit `ARFaceAnchor.blendShapes` (0.0–1.0)
- Toon `tongueOut` **altijd** prominent in Explorer (eigen sectie "Tong", niet verborgen)
- Kalibratie-flow specifiek voor tong: gebruiker doet tong uit / tongbol; app toont score en suggereert drempel
- Ondersteun AND-triggers met tong, bijv.:
  - `mouthSmileLeft` + `mouthSmileRight` + `tongueOut` (lach + tong uit)
  - `mouthSmileLeft` + `mouthSmileRight` + `mouthFunnel` (lach + tongbol in mond)
- Live modus: visuele feedback wanneer `tongueOut` boven drempel is (aparte indicator, niet alleen trigger-status)
- Voorbeeldprofiel "Standaard" moet minstens één tong-trigger bevatten (zie Deliverables)

1. **Face tracking scherm**
   - Start ARKit sessie met front camera
   - Toon live camera preview + optionele face mesh overlay
   - Lees alle 52 blendshape coefficients (0.0–1.0) uit `ARFaceAnchor`
   - Toon top-N actieve blendshapes als live balkjes/scores (Explorer-modus)

2. **Blendshape Explorer (kalibratie)**
   - Gebruiker maakt een gebaar; app toont welke blendshapes het hoogst scoren
   - Gebruiker selecteert relevante blendshapes voor een trigger
   - Stel per blendshape een drempel in (slider 0.0–1.0)
   - Sla op als trigger met naam

3. **Trigger engine**
   - Trigger = `{ id, naam, blendshapes: [String: Float], actief: Bool }`
   - Evaluatie: **alle** geselecteerde blendshapes moeten ≥ drempel zijn (AND)
   - **Vasthoudtijd**: trigger moet `vasthoudTijd` seconden actief blijven
   - **Cooldown**: na actie wacht `cooldown` seconden
   - **Verplicht:** `tongueOut` (hoogste prioriteit), plus `mouthSmileLeft/Right`, `mouthFunnel`, `jawOpen`, `browInnerUp`, `eyeBlinkLeft/Right`

4. **Actie-uitvoer (realistisch voor iOS)**
   - iOS staat **geen system-wide keyboard injection** toe zonder speciale entitlements
   - MVP-acties (kies minstens 2):
     - **In-app acties**: knoppen/tabs in de app zelf bedienen via triggers
     - **Haptic + visuele feedback** bij trigger
     - **Switch Control integratie**: documenteer hoe gebruiker iOS Switch Control kan koppelen; app toont grote on-screen knoppen die Switch kan targeten
     - **Companion mode**: app stuurt trigger-events via **Bonjour/HTTP/WebSocket** naar een Mac/PC met MimiControl-bridge (toekomst)
   - Toon duidelijk in UI wat wél/niet kan op iPad

5. **Profielen**
   - Meerdere profielen (bijv. "Standaard", "School", "Thuis")
   - Per profiel: triggers + timing (`cooldown`, `vasthoudTijd`)
   - Import/export als JSON (compatibel met Python-structuur waar mogelijk)

6. **Anti-spasmefilter UI**
   - Instelbare vasthoudtijd (slider 0.1–3.0s, default 0.5s)
   - Instelbare cooldown (slider 0.5–10s, default 2.0s)
   - Visuele voortgangsbalk tijdens vasthouden (zoals Python live modus)

### UI / Design — Mennens.Tech branding

- **Licht thema** (achtergrond `#F2F2F7`)
- **Teal accenten** (`#4DB8BE`, `#68CCD1`, donker `#062D36`)
- Kaarten met witte achtergrond, subtiele rand `#E5E5EA`
- Typografie: SF Pro (system)
- Header: "MimiControl" + tagline "Jouw gezicht, jouw besturing — Mennens.Tech"
- Tab-navigatie: **Explorer** | **Triggers** | **Live** | **Instellingen**
- Grote touch targets (toegankelijkheid)
- Ondersteun Dynamic Type

### Schermen (MVP)

1. **Onboarding** — uitleg face tracking, privacy (camera alleen lokaal), vereiste hardware (Face ID iPad)
2. **Explorer** — live blendshape scores, selectie voor trigger
3. **Trigger editor** — naam, blendshapes + drempels, preview of trigger "vuurt"
4. **Live modus** — actieve triggers evalueren, status per trigger (wachtend / vasthouden / cooldown / ACTIEF)
5. **Profielen & instellingen** — profiel wisselen, timing, export/import

### iOS beperkingen — wees expliciet

Documenteer en implementeer realistische alternatieven:

| Beperking | Alternatief |
|-----------|-------------|
| Geen globale toetsaanslagen | Switch Control, AssistiveTouch, in-app knoppen |
| ARKit face tracking alleen op TrueDepth iPads | Check `ARFaceTrackingConfiguration.isSupported`; toon foutmelding op niet-ondersteunde devices |
| App op achtergrond → tracking stopt | Waarschuuw gebruiker; Live modus vereist app op voorgrond |
| Geen pyautogui equivalent | Companion Mac-app via netwerk (later) of Switch Control workflow |

### Data model (Swift)

```swift
struct Profiel: Codable, Identifiable {
    var id: UUID
    var naam: String
    var triggers: [Trigger]
    var cooldown: Double       // default 2.0
    var vasthoudTijd: Double   // default 0.5
}

struct Trigger: Codable, Identifiable {
    var id: UUID
    var naam: String
    var blendshapes: [String: Float]  // ARKit blendshape key → drempel
    var actief: Bool
    var actie: TriggerActie
}

enum TriggerActie: Codable {
    case inAppKnop(String)      // MVP
    case haptic
    case companionEvent(String) // later
}
```

ARKit blendshape keys volgen Apple's naming (camelCase, bijv. `mouthSmileLeft`, `tongueOut`).

### Nederlandse blendshape labels (gebruik in UI)

| Key | Label |
|-----|-------|
| mouthSmileLeft | Lach links |
| mouthSmileRight | Lach rechts |
| jawOpen | Kaak open |
| browInnerUp | Wenkbrauwen omhoog |
| eyeBlinkLeft | Oogknip links |
| eyeBlinkRight | Oogknip rechts |
| tongueOut | Tong uitsteken |
| mouthFunnel | Mond trechter (tongbol) |
| ... | (vul aan voor alle 52) |

### Architectuur

```
MimiControlApp (SwiftUI App)
├── Features/
│   ├── Explorer/       ARSession + blendshape display
│   ├── Triggers/       CRUD + editor
│   ├── Live/           Trigger engine loop
│   └── Settings/       Profielen, export
├── Core/
│   ├── FaceTracking/   ARKit wrapper, blendshape publisher
│   ├── TriggerEngine/  Evaluatie + vasthoud + cooldown
│   └── Storage/        Profiel persistence
└── DesignSystem/       Mennens.Tech kleuren, componenten
```

Trigger engine pseudocode (volg Python `live_modus_explorer.py`):

```
for each frame with blendshape scores:
  for each active trigger:
    allMatch = every (score[key] >= drempel[key] for key in trigger.blendshapes)
    if allMatch and not inCooldown:
      if holdStart is nil: holdStart = now
      if now - holdStart >= vasthoudTijd:
        fireAction(trigger)
        lastAction = now
        holdStart = nil
    else:
      holdStart = nil
```

### Later features (niet MVP, wel architectuur voorbereiden)

- Companion Mac/Windows bridge (UDP/WebSocket) voor echte toetsaanslagen op desktop
- iCloud sync profielen
- Widget met grote actieknoppen
- Siri Shortcuts integratie
- Statistieken / logging voor therapeuten
- Meerdere talen

### Testcriteria — tongdetectie (acceptatie MVP)

De MVP is **niet** acceptabel zonder werkende tongdetectie. Test met echte gebruiker of video-opname van de primaire casus (lach + tong).

| Test | Verwacht resultaat |
|------|-------------------|
| Tong uitsteken | `tongueOut` score ≥ 0.5 binnen 1 frame-cyclus; indicator actief |
| Tong in rust | `tongueOut` score < 0.2; geen false trigger |
| Lach + tong uit (AND) | Trigger vuurt alleen als beide blendshapes boven drempel |
| Lach + tongbol (`mouthFunnel`) | Trigger vuurt bij combinatie; `tongueOut` blijft laag |
| Vasthoudtijd + cooldown | Tong-trigger respecteert timing; geen spasmefalse positives |
| Explorer kalibratie | Gebruiker kan drempel voor `tongueOut` instellen en direct zien of trigger "vuurt" |
| 30+ fps | Tong-score updates vloeiend zonder haperen op iPad Pro |

### Kwaliteitseisen

- Graceful degradation als geen gezicht gedetecteerd
- Permission flow voor camera (NSCameraUsageDescription in Info.plist, Nederlands)
- Unit tests voor TriggerEngine (zonder ARKit)
- Preview providers voor SwiftUI
- Geen crashes bij rotatie (iPad landscape preferred)
- Performance: 30+ fps face tracking op iPad Pro

### Deliverables

1. Xcode project met werkende MVP
2. README in het Nederlands
3. Info.plist met privacy strings
4. Voorbeeldprofiel "Standaard" met minstens 2 demo-triggers, waarvan **één tong-trigger**:
   - Trigger "Lach + tong uit": `mouthSmileLeft` ≥ 0.4, `mouthSmileRight` ≥ 0.4, `tongueOut` ≥ 0.5
   - Trigger "Lach + tongbol": `mouthSmileLeft` ≥ 0.4, `mouthSmileRight` ≥ 0.4, `mouthFunnel` ≥ 0.4
5. Comments in code waar iOS-beperkingen gelden

Begin met project setup, dan **ARKit POC met `tongueOut` live score** (acceptatie-gate), dan TriggerEngine met tong-AND-logica, dan UI schermen in bovenstaande volgorde.
```

---

## Gebruik

1. Open Vibe Code in Cursor
2. Plak de prompt (alles tussen de ``` markers)
3. Werk iteratief: eerst ARKit POC, daarna trigger engine, daarna UI

## Referenties in deze repository

- `app/blendshape_detectie.py` — blendshape detectie + NL labels
- `app/config_explorer.py` — profiel/trigger JSON-structuur
- `app/live_modus_explorer.py` — trigger evaluatie, vasthoudtijd, cooldown
- `app/explorer.py` — Explorer UX-concept
- `app/gui_explorer_ctk.py` — UI kleurenpalet Mennens.Tech
