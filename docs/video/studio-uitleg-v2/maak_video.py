"""Genereert de uitlegvideo MimiControl Studio v2 (HyperFrames-project in deze map).

Hier staan alle gesproken teksten en ondertitels. Pas ze hier aan en draai daarna:

    python maak_video.py stem     # voice-over opnieuw maken (alleen gewijzigde scènes; HeyGen)
    python maak_video.py          # index.html, lib/tijden.js en voorleesscript bijwerken

Render (Node 22 nodig):  npx hyperframes render -o ../Uitleg-MimiControl-Studio-v2.mp4

Elke scène is een eigen bestand in compositions/ met de animatie. De klik- en
animatiemomenten in die scènes volgen de woorden van de voice-over (lib/tijden.js),
dus na een nieuwe stem schuift alles vanzelf mee.
"""

import hashlib
import json
import os
import re
import subprocess
import sys
import urllib.request

HIER = os.path.dirname(os.path.abspath(__file__))
HEYGEN = os.environ.get("HEYGEN_EXE", r"D:\heygen-cli\heygen.exe")
STEM_ID = "f8cd397efcde44109e202f4e8c2d928f"  # HeyGen "Maarten de Vries" (Nederlands)
STEM_SNELHEID = 1.0

# Uitspraak voor de stem; de ondertitel houdt de geschreven vorm.
UITSPRAAK = [
    (r"\bCommunicator 5\b", "Communicator vijf"),
    (r"\bStudio v2\.exe\b", "Studio versie twee"),
]

# Een regel is een ondertitel (één regel op het scherm). Een getal is een pauze in seconden.
# voor = stilte aan het begin van de scène (titel/beeld eerst), na = uitloop na de laatste zin,
# min = minimale scèneduur.
SCENES = [
    dict(id="f01-intro", titel="Intro", voor=1.6, na=1.6, min=6.0, vo=[
        "MimiControl: toetsen indrukken met je gezicht.",
    ]),
    dict(id="f02-concept", titel="Zo werkt het", voor=0.8, na=2.4, min=6.0, vo=[
        "MimiControl kijkt via de webcam naar je gezicht.", 0.5,
        "Maak je een bepaalde beweging,",
        "bijvoorbeeld je mond open,",
        "dan drukt het programma een toets in,",
        "zoals de spatiebalk.", 0.8,
        "Zo bedien je Communicator 5 zonder toetsenbord.",
    ]),
    dict(id="f03-starten", titel="Starten", voor=1.6, na=1.8, min=6.0, vo=[
        "Start het programma met een dubbelklik op het bestand",
        "MimiControl Studio v2.exe.", 0.6,
        "Het programma vraagt of het opnieuw mag starten als beheerder.", 0.4,
        "Klik op Ja,", 0.6,
        "en daarna ook op Ja bij de melding van Windows.", 0.8,
        "Bovenaan het dashboard staat dan: Beheerder: ja.",
    ]),
    dict(id="f04-kiezen", titel="Stap 1: Kies je gezichtsbewegingen", voor=1.8, na=1.4, min=6.0, vo=[
        "Stap één: klik op Mimiek verkennen",
        "en kies je gezichtsbewegingen.", 0.6,
        "Vink aan wat je wilt gebruiken, bijvoorbeeld de kaak.", 1.4,
        "Klik op Toepassen.",
    ]),
    dict(id="f05-opnemen", titel="Stap 2: Neem je beweging op", voor=1.6, na=1.6, min=6.0, vo=[
        "Stap twee: klik op Opname starten",
        "en maak je beweging een paar keer.", 1.6,
        "De sterkste beweging krijgt een gele balk.", 0.6,
        "Klik op Opname stoppen,", 0.4,
        "en daarna op Trigger maken.",
    ]),
    dict(id="f06-trigger", titel="Stap 3: Toets en drempel", voor=1.6, na=1.6, min=6.0, vo=[
        "Stap drie: geef de trigger een naam", 0.4,
        "en kies de toets, bijvoorbeeld Spatie.", 0.8,
        "De drempel is hoe sterk je de beweging moet maken.",
        "Zet hem iets onder de gemeten waarde.", 0.8,
        "Klik op Opslaan.",
    ]),
    dict(id="f07-kaart", titel="Stap 4: Klaar", voor=1.2, na=2.2, min=6.0, vo=[
        "Stap vier: je trigger staat nu als kaart op het dashboard.",
    ]),
    dict(id="f08-live", titel="Live gebruiken", voor=1.0, na=2.6, min=6.0, vo=[
        "Klik op Live modus starten.", 0.6,
        "Rechtsboven verschijnt een klein camerabeeld.",
        "Dat blijft boven je andere programma's staan.", 0.6,
        "Klik nu op Communicator 5:",
        "toetsen gaan altijd naar het actieve venster.", 0.3,
        "Volledig scherm mag gewoon.", 0.8,
        "Maak je beweging.", 1.0,
        "Linksonder in het camerabeeld zie je welke toets is verstuurd.",
    ]),
    dict(id="f09-stoppen", titel="Stoppen", voor=1.4, na=1.6, min=6.0, vo=[
        "Stoppen? Klik op de X rechtsboven in het camerabeeld.", 0.4,
        "De knop wordt rood: klik nog een keer.", 0.4,
        "Zo stopt het programma niet per ongeluk.", 0.6,
        "Je kunt ook op Stop live klikken, of op Q drukken.",
    ]),
    dict(id="f10-hulp", titel="Werkt het niet?", voor=1.4, na=2.4, min=6.0, vo=[
        "Komt de toets niet aan? Start opnieuw en kies Ja.",
        "Camera werkt niet? Sluit andere camera-apps",
        "of een oude MimiControl.",
        "Draait het al? Sluit de andere.",
        "Beeld stil? Probeer Vensterweergave.",
    ]),
    dict(id="f11-outro", titel="Einde", voor=0.8, na=3.4, min=6.0, vo=[
        "Meer uitleg vind je in de handleiding.",
    ]),
]


# Momenten in de scènes, gekoppeld aan woorden van de voice-over: naam -> (woord, n-de keer, verschuiving)
# of een vast getal (seconden vanaf het begin van de scène). Namen met "klik" krijgen een klikgeluid,
# "toets" een toetsgeluid, "plof" een zacht plofje, "typ" typgeluid.
CUES = {
    "f02-concept": {"open1": ("mond", 1, -0.1), "toets1": ("toets", 1, 0.0), "dicht1": ("spatiebalk", 1, 0.4),
                    "open2": ("communicator", 1, 0.0), "toets2": ("vijf", 1, 0.05)},
    "f03-starten": {"klikDubbel1": ("dubbelklik", 1, 0.05), "klikDubbel2": ("dubbelklik", 1, 0.27),
                    "klikJa1": ("ja", 1, -0.05), "klikJa2": ("ja", 2, -0.05)},
    "f04-kiezen": {"klikVerkennen": ("mimiek", 1, 0.0), "klikUitvinken": ("vink", 1, 0.0),
                   "klikKaakAlles": ("kaak", 1, 0.35),
                   "klikToepassen": ("toepassen", 1, 0.0)},
    "f05-opnemen": {"klikStart": ("opname", 1, 0.15), "klikStop": ("stoppen", 1, 0.0),
                    "klikMaken": ("trigger", 1, 0.15)},
    "f06-trigger": {"klikNaam": ("geef", 1, 0.1), "typNaam": ("naam", 1, -0.1), "klikActie": ("kies", 1, 0.1),
                    "klikSpatie": ("spatie", 1, 0.0), "sleepStart": ("zet", 1, 0.0), "sleepEind": ("waarde", 1, 0.2),
                    "klikOpslaan": ("opslaan", 1, 0.0)},
    "f07-kaart": {"plofKaart": ("trigger", 1, -0.1)},
    "f08-live": {"klikLive": ("live", 1, -0.1), "klikComm": ("communicator", 1, 0.0),
                 "toetsA": ("beweging", 1, 0.55), "toetsB": ("verstuurd", 1, 0.1)},
    "f09-stoppen": {"klikX": ("camerabeeld", 1, 0.3), "klikX2": ("nog", 1, 0.0),
                    "toetsQ": ("drukken", 1, -0.1)},
}

SFX = {"klik": ("click-soft.mp3", 0.55), "toets": ("key-press.mp3", 0.35), "plof": ("pop.mp3", 0.25),
       "typ": ("typing.mp3", 0.3)}
BGM = ("assets/audio/bgm-training.wav", 0.11)  # HeyGen-muziek eb9729536df94069a5c8313bff330626, 180 s

OVERLAP = 0.0  # scènes sluiten op elkaar aan; elke scène vervaagt zelf in en uit


# ---------------------------------------------------------------------------
def uitspraak(tekst):
    for patroon, vervanging in UITSPRAAK:
        tekst = re.sub(patroon, vervanging, tekst)
    return tekst


def tts_tekst(scene):
    delen = []
    for regel in scene["vo"]:
        if isinstance(regel, (int, float)):
            delen.append('<break time="%.1fs"/>' % regel)
        else:
            delen.append(uitspraak(regel))
    return " ".join(delen)


def vo_pad(scene, ext):
    return os.path.join(HIER, "assets", "vo", scene["id"] + ext)


def maak_stem(alles=False):
    os.makedirs(os.path.join(HIER, "assets", "vo"), exist_ok=True)
    env = dict(os.environ, HEYGEN_NO_ANALYTICS="1")
    for scene in SCENES:
        tekst = tts_tekst(scene)
        sleutel = hashlib.sha1((STEM_ID + str(STEM_SNELHEID) + tekst).encode("utf8")).hexdigest()
        meta_pad = vo_pad(scene, ".json")
        if not alles and os.path.exists(meta_pad):
            with open(meta_pad, encoding="utf8") as f:
                if json.load(f).get("sleutel") == sleutel:
                    print("  ongewijzigd:", scene["id"])
                    continue
        print("  stem maken:", scene["id"])
        uit = subprocess.run(
            [HEYGEN, "voice", "speech", "create", "--voice-id", STEM_ID, "--language", "nl",
             "--speed", str(STEM_SNELHEID), "--text", tekst],
            capture_output=True, text=True, encoding="utf8", env=env)
        if uit.returncode != 0:
            sys.exit("HeyGen-fout bij %s:\n%s\n%s" % (scene["id"], uit.stdout, uit.stderr))
        data = json.loads(uit.stdout)["data"]
        urllib.request.urlretrieve(data["audio_url"], vo_pad(scene, ".mp3"))
        woorden = [w for w in data.get("word_timestamps", []) if not w["word"].startswith("<")]
        with open(meta_pad, "w", encoding="utf8") as f:
            json.dump({"sleutel": sleutel, "tekst": tekst, "duur": data["duration"],
                       "woorden": woorden}, f, ensure_ascii=False, indent=1)


# ---------------------------------------------------------------------------
def norm(w):
    return re.sub(r"[^\wéëèïöü]", "", w.lower())


def lees_vo(scene):
    with open(vo_pad(scene, ".json"), encoding="utf8") as f:
        meta = json.load(f)
    uit = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                          vo_pad(scene, ".mp3")], capture_output=True, text=True)
    meta["duur"] = float(uit.stdout.strip())
    return meta


def regels_met_tijden(scene, meta):
    """Koppel elke ondertitelregel aan de tijden van zijn woorden (via uitspraaktekst)."""
    woorden = meta["woorden"]
    uit, i = [], 0
    for regel in scene["vo"]:
        if isinstance(regel, (int, float)):
            continue
        n = len(uitspraak(regel).split())
        stuk = woorden[i:i + n]
        i += n
        if not stuk:
            raise SystemExit("Woordtijden kloppen niet met de tekst in %s" % scene["id"])
        uit.append({"tekst": regel, "begin": stuk[0]["start"], "eind": stuk[-1]["end"]})
    if i != len(woorden):
        print("  let op: %s heeft %d woorden in de stem, %d in de tekst" % (scene["id"], len(woorden), i))
    return uit


def bouw():
    tijden, ondertitels, audio, slots, geluiden = {}, [], [], [], []
    t = 0.0
    for nr, scene in enumerate(SCENES):
        meta = lees_vo(scene)
        duur = round(max(scene["min"], scene["voor"] + meta["duur"] + scene["na"]), 2)
        regels = regels_met_tijden(scene, meta)
        woorden = [{"w": norm(w["word"]), "t": round(scene["voor"] + w["start"], 3),
                    "e": round(scene["voor"] + w["end"], 3)} for w in meta["woorden"]]
        cues = {}
        for naam, spec in CUES.get(scene["id"], {}).items():
            if isinstance(spec, (int, float)):
                cues[naam] = float(spec)
            else:
                woord, n, schuif = spec
                hits = [w for w in woorden if w["w"] == woord]
                if len(hits) < n:
                    raise SystemExit("Cue %s: woord '%s' (%dx) niet gevonden in %s" % (naam, woord, n, scene["id"]))
                cues[naam] = round(hits[n - 1]["t"] + schuif, 3)
            for soort, (bestand, vol) in SFX.items():
                if naam.startswith(soort):
                    geluiden.append((t + cues[naam], bestand, vol))
        tijden[scene["id"]] = {"start": round(t, 3), "duur": duur, "voor": scene["voor"],
                               "woorden": woorden, "cues": cues,
                               "regels": [{"tekst": r["tekst"], "t": round(scene["voor"] + r["begin"], 3),
                                           "e": round(scene["voor"] + r["eind"], 3)} for r in regels]}
        slots.append((scene, t, duur))
        audio.append((scene, t + scene["voor"], meta["duur"]))
        for j, r in enumerate(regels):
            begin = t + scene["voor"] + r["begin"] - 0.12
            if j + 1 < len(regels):
                eind = t + scene["voor"] + regels[j + 1]["begin"] - 0.12
                eind = min(eind, t + scene["voor"] + r["eind"] + 1.4)
            else:
                eind = min(t + scene["voor"] + r["eind"] + 1.2, t + duur - 0.2)
            ondertitels.append((round(begin, 3), round(eind - begin, 3), r["tekst"]))
        t += duur - OVERLAP
    totaal = round(t + OVERLAP, 2)

    with open(os.path.join(HIER, "lib", "tijden.js"), "w", encoding="utf8") as f:
        f.write("/* Gegenereerd door maak_video.py — niet met de hand wijzigen. */\n")
        f.write("window.TIJDEN = " + json.dumps(tijden, ensure_ascii=False, indent=1) + ";\n")

    schrijf_index(slots, audio, ondertitels, totaal, geluiden)
    schrijf_voorleesscript(slots)
    print("Totale duur: %d:%04.1f (%.1f s), %d ondertitelregels" % (totaal // 60, totaal % 60, totaal, len(ondertitels)))


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def schrijf_index(slots, audio, ondertitels, totaal, geluiden):
    with open(os.path.join(HIER, "sjabloon", "index.html.tpl"), encoding="utf8") as f:
        sjabloon = f.read()
    s_slots = "\n".join(
        '      <div id="el-%s" data-composition-id="%s" data-composition-src="compositions/%s.html" '
        'data-start="%.3f" data-duration="%.3f" data-track-index="1" data-width="1920" data-height="1080"></div>'
        % (sc["id"], sc["id"], sc["id"], st, du) for sc, st, du in slots
        if os.path.exists(os.path.join(HIER, "compositions", sc["id"] + ".html")))
    for sc, st, du in slots:
        if not os.path.exists(os.path.join(HIER, "compositions", sc["id"] + ".html")):
            print("  let op: compositions/%s.html ontbreekt nog" % sc["id"])
    s_audio = "\n".join(
        '      <audio id="vo-%s" src="assets/vo/%s.mp3" data-start="%.3f" data-duration="%.3f" '
        'data-track-index="20" data-volume="1"></audio>' % (sc["id"], sc["id"], st, du)
        for sc, st, du in audio)
    s_audio += "\n" + "\n".join(
        '      <audio id="sfx-%02d" src="assets/sfx/%s" data-start="%.3f" data-duration="%.3f" '
        'data-track-index="%d" data-volume="%.2f"></audio>' % (i, b, st, sfx_duur(b), 21 + 2 * (i % 2), v)
        for i, (st, b, v) in enumerate(sorted(geluiden)))
    bgm_duur = totaal
    automatie = json.dumps({"version": 1, "lanes": [{"target": "volume", "points": [
        {"t": 0, "v": 0}, {"t": 1.5, "v": 1}, {"t": round(bgm_duur - 4.0, 2), "v": 1}, {"t": round(bgm_duur, 2), "v": 0}]}]})
    s_audio += ("\n      <audio id=\"bgm\" src=\"%s\" data-start=\"0\" data-duration=\"%.3f\" data-track-index=\"25\" "
                "data-volume=\"%.2f\" data-automation='%s'></audio>" % (BGM[0], bgm_duur, BGM[1], automatie))
    s_caps = "\n".join(
        '      <div id="cap-%02d" class="clip cap" data-start="%.3f" data-duration="%.3f" data-track-index="10">'
        '<span class="cap-tekst" data-layout-allow-overlap>%s</span></div>' % (i, st, du, esc(tx))
        for i, (st, du, tx) in enumerate(ondertitels))
    uit = (sjabloon.replace("{{DUUR}}", "%.2f" % totaal)
           .replace("{{SLOTS}}", s_slots).replace("{{AUDIO}}", s_audio)
           .replace("{{ONDERTITELS}}", s_caps)
           .replace("{{BGM_DUUR}}", "%.2f" % totaal))
    with open(os.path.join(HIER, "index.html"), "w", encoding="utf8") as f:
        f.write(uit)


def sfx_duur(bestand):
    uit = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                          os.path.join(HIER, "assets", "sfx", bestand)], capture_output=True, text=True)
    return float(uit.stdout.strip())


def mmss(t):
    return "%d:%02d" % (int(t) // 60, int(t) % 60)


def schrijf_voorleesscript(slots):
    regels = [
        "# Voorleesscript: uitlegvideo MimiControl Studio v2", "",
        "De video heeft een Nederlandse voice-over (HeyGen-stem \"Maarten de Vries\") en Nederlandse",
        "ondertitels. Wil je zelf inspreken? Hieronder de tekst per scène met het tijdstip waarop de scène",
        "begint. De gesproken tekst begint telkens kort na dat tijdstip.", "",
        "| Tijd | Scène | Tekst |", "|---|---|---|",
    ]
    for sc, st, du in slots:
        tekst = " ".join(r for r in sc["vo"] if isinstance(r, str))
        regels.append("| %s | %s | %s |" % (mmss(st), sc["titel"], tekst))
    regels += ["", "## Opnieuw maken", "",
               "Teksten staan in `docs/video/studio-uitleg-v2/maak_video.py`. Daarna, in die map:", "",
               "```", "python maak_video.py stem", "python maak_video.py",
               "npx hyperframes render -o ../Uitleg-MimiControl-Studio-v2.mp4", "```", "",
               "Voor `stem` is de HeyGen-CLI nodig (`D:\\heygen-cli\\heygen.exe`, ingelogd met "
               "`heygen auth login --oauth`). Het gratis stemtegoed van HeyGen is beperkt per maand; `stem` maakt "
               "alleen scènes opnieuw waarvan de tekst veranderd is. Voor `npx hyperframes` is Node.js 22 of nieuwer nodig.", ""]
    with open(os.path.join(HIER, "..", "voorleesscript.md"), "w", encoding="utf8") as f:
        f.write("\n".join(regels))


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "stem":
        maak_stem(alles="--alles" in sys.argv)
    else:
        bouw()
