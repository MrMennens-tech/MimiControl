# Handover — MimiControl Studio v2

Voor Mark / Claude Opus. Stand: 2 okt 2026. Geen commit gedaan; bron = `app_v2/`.

---

## 1. Project in 1 alinea

MimiControl Studio zet mimiek (MediaPipe Face Landmarker blendshapes) om naar hardware-toetsen via Windows `SendInput` met `KEYEVENTF_SCANCODE`, zodat een leerling met spasmen apps kan bedienen — vooral **Communicator 5** (Tobii Dynavox), plus leerzone.nl en een aparte React-toetsentestomgeving. **v1** = `app/` + release `releases\MimiControl Studio\`. **v2** = `app_v2/` (CustomTkinter Explorer). **v1-releases nooit overschrijven.**

---

## 2. Wat we recent gedaan hebben

- Studio v2 GUI-overhaul: explorer, triggers, PiP-overlay, hotkeys, performance (MP max 640 px, HUD throttle).
- Nieuwe onedir-map: `releases\MimiControl Studio v2\` + zip `releases\MimiControl-Studio-v2.1-onedir.zip` (18-9-2026).
  - **Die zip/onedir is STALE t.o.v. latere codefixes** (layered overlay, filter/menu, UIPI-meldingen). Altijd testen met repo-root **`Start MimiControl Studio v2.bat`** (Python → `app_v2\mimiexplorer_ctk.py`).
- Overlay: van OpenCV HighGUI (`imshow`/`waitKey`) naar **eigen Win32 layered HWND + `UpdateLayeredWindow`** — fix voor freeze boven C5. Live-loop (camera/triggers/SendInput) skip’t niet meer omdat C5 eronder zit; tekenfout logt, capture blijft lopen.
- Toetsen: werken als Studio **als administrator** draait (zelfde elevation als C5). Anders blokkeert **UIPI** `SendInput`. Scancodes niet wijzigen. `toets_actie.py` heeft status + NL UIPI-waarschuwing.
- Camera “pakt niet”: vaak een oude Studio/Python-instantie houdt de webcam vast → andere processen sluiten + herstart.
- **Filter vs trigger-menu — GEDAAN in code:** `pieken_voor_trigger_menu()` toont altijd alle bruikbare blendshapes; explorer-filter is alleen kijkhulp (`pieken_voor_editor`). `trigger_editor_ctk.py` gebruikt die menu-helper.
- **Tong — GEDAAN (documentatie + model-filter):** MediaPipe Face Landmarker heeft **geen** `tongueOut` in de output. Tong alleen zichtbaar in camerabeeld/mesh bij open mond. Workaround-trigger: **jawOpen + mouthFunnel** (tekst in `MODEL_BEPERKING_TEKST` / `blendshape_labels.py`).

Zie ook `app_v2/LEESMIJ.txt` (korte gebruikersnotities, sync met bovenstaande).

---

## 3. Open / te verifiëren

| Item | Status |
|------|--------|
| Overlay boven C5 (Vensterweergave + Studio admin) | Fix in bron; **Mark moet bevestigen** dat beeld blijft bewegen |
| Exclusive/fullscreen DirectX in C5 | Fundamenteel problematisch (overlay + soms input). Advies: **Vensterweergave** |
| Portable onedir | Achter op bron → nieuwe build na stabiele C5-test |
| Filter/tong-menu | **Gedaan** in code (niet half) |
| Admin-vereiste | Constraint voor eindgebruikers; UX-verbeterpad open (manifest / “vraag elevation”) |

---

## 4. Harde constraints (niet breken)

1. **`SendInput` + `KEYEVENTF_SCANCODE` behouden** — geen `WM_CHAR` / PostMessage als vervanging.
2. **Geen DLL-injectie / DirectX-hook** in Communicator.
3. **v1 `app/` en `releases\MimiControl Studio\` niet overschrijven.**
4. UI in het **Nederlands**.
5. **Geen git commit/push** tenzij Mark expliciet vraagt.

---

## 5. Hoe starten / testen

1. Alle oude Studio/Python-processen sluiten (camera lock).
2. Repo-root: `Start MimiControl Studio v2.bat` → **Als administrator**.
3. Communicator 5: **Vensterweergave**, zelfde admin-niveau als Studio.
4. Live aan → overlay PiP rechtsboven: beeld moet bewegen; trigger → toets in C5 **zonder** Studio-focus.
5. Stop: Q (overlay-focus), knop Stop live, of beide vensters sluiten. Alleen overlay sluiten = live op achtergrond.

Portable (andere pc zonder Python): hele map `releases\MimiControl Studio v2\` of zip uitpakken; start de `.bat` **in die map** — niet alleen de `.exe`. Na codefixes eerst opnieuw bouwen (`scripts\build_onedir_v2.bat`).

---

## 6. Advies Claude Opus — verbeterplan

### Stabiliteit (P0)

- Camera-pipeline robuust: `CAP_DSHOW` (al deels), retry indices, duidelijke NL-fout als camera locked, nooit stille crash.
- Overlay: layered path als **enige** live-renderer; geen skip omdat C5 eronder zit; headless/fallback zonder capture te droppen (richting al gezet in `live_modus_explorer.py`).
- SendInput: foutlog + UIPI in UI (deels aanwezig); overweeg elevation bij start of installer-manifest (`requireAdministrator` / asInvoker + prompt).
- **Single-instance mutex** zodat tweede start de camera niet steelt.

### Architectuur (P1)

- Threads strak: capture → detectie → trigger → input; UI/overlay apart.
- Geen OpenCV `waitKey` in kritieke pad (layered message-pump is de vervanging).
- Config/profielen duidelijk; filter vs trigger-menu ontkoppeld houden (`blendshape_labels.py`).

### UX (P1)

- Trigger-editor: volledige blendshape-lijst (al zo) — niet terugdraaien.
- Tong: eerlijke NL-uitleg + jawOpen/mouthFunnel-preset (tekst aanwezig; eventueel 1-klik preset-knop).
- C5 setup-wizard: Vensterweergave + admin-checklist.

### Performance (P2)

- Lagere MP-resolutie / throttle HUD (deels gedaan).
- Overlay size-hotkeys behouden.

### Release (P2)

- Pas nieuwe onedir **na groene C5-test**.
- Build: `scripts\build_onedir_v2.bat` → `python -m PyInstaller --noconfirm …`
- Zip-naam vandaag: `MimiControl-Studio-v2.1-onedir.zip` (niet `…-v2-onedir.zip`).

### Testomgeving

- Apart React-project in `testomgeving/` — **niet** mengen met Studio-onedir tenzij gevraagd.

---

## 7. Belangrijkste bestanden

| Bestand | Rol |
|---------|-----|
| `app_v2/mimiexplorer_ctk.py` | Entry: start CustomTkinter Explorer-app |
| `app_v2/gui_explorer_ctk.py` | Hoofd-GUI (dashboard, Live/Explorer, rail) |
| `app_v2/live_modus_explorer.py` | Live-loop + layered PiP-overlay + hotkeys |
| `app_v2/toets_actie.py` | SendInput scancodes + UIPI/admin-detectie |
| `app_v2/trigger_editor_ctk.py` | Dialoog triggers (volledige shape-lijst) |
| `app_v2/blendshape_labels.py` | NL-labels, filter vs menu, tong-beperking |
| `app_v2/config_explorer.py` | Profiel/config voor explorer-layout |
| `app_v2/paths.py` | Paden assets/model/profielen |
| `app_v2/LEESMIJ.txt` | Korte NL-notities voor ontwikkelaar/testers |
| `scripts/build_onedir_v2.bat` | PyInstaller onedir-build → `releases\… v2\` |

Gerelateerd: `app_v2/blendshape_detectie.py`, `gezichtsdetectie.py`, `face_landmarker.task`. Profielen gedeeld met v1 via map `app/` (zie LEESMIJ).

---

## 8. Volgende sessie — checklist

1. **Overlay freeze bevestigen** met C5 Vensterweergave + Studio als admin (beeld blijft bewegen?).
2. **Filter-menu spot-check:** trigger-editor toont alle shapes ook als explorer-filter smal is.
3. Eventueel **single-instance mutex** + elevation-UX (manifest of startprompt).
4. Na groene test: **nieuwe onedir** bouwen; oude zip niet als “huidig” behandelen.
5. **Geen v1 aanraken** (`app/`, `releases\MimiControl Studio\`, v1-zip).

---

## Snelle feiten

- Start-bat bestaat: `Start MimiControl Studio v2.bat` (repo-root) → True.
- Releases: `MimiControl Studio` (v1) | `MimiControl Studio v2` | zips `…-onedir.zip` / `…-v2.1-onedir.zip`.
- docs/ bestaat (`docs/onderzoek-windows-tongdetectie.md` e.d.); dit handover-bestand staat bewust naast de code: **`app_v2/HANDOVER.md`**.

---

## 9. Update 2 okt 2026 (later)

- **Nieuwe release:** `releases\MimiControl Studio v2\` is opnieuw gebouwd (227 MB, was 392 MB) en
  `releases\MimiControl-Studio-v2.2-onedir.zip`. De v2.1-zip en alle v1-bestanden zijn ongemoeid. De
  vorige opmerking "onedir is stale" geldt niet meer. De release is getest met een rooktest
  (start, GUI klaar na ~5 s); de C5-test op een andere pc moet nog.
- **Nieuw:** knoppen in de Explorer, "Beweging kiezen" kan toevoegen, tong-preset, beheerders-vraag +
  mutex (`opstart_controle.py`), statuskaart "Communicator 5", actief-venster-melding, stopknop (X,
  twee klikken) in het camerabeeld, toets-melding (K) in het camerabeeld.
- **Handleiding:** `docs\Handleiding-MimiControl-Studio-v2.docx/.pdf`. Opnieuw maken na schermwijzigingen:
  `python docs\maak_screenshots.py` en daarna `node docs\maak_handleiding.js` (npm-pakket `docx` nodig).
- **Nog open:** video (HyperFrames), opstarttijd/FPS op een trage pc meten, DSHOW-volgorde
  (camera-indices kunnen verschuiven, bewust niet gedaan), niets gecommit.
