/**
 * Inhoudseditor: schermen en tegels toevoegen, wijzigen, verwijderen en
 * ordenen. Afbeeldingen en geluiden worden lokaal opgeslagen (IndexedDB) en
 * verlaten het apparaat nooit.
 *
 * Import en export gaan via JSON; bij import wordt het bestand eerst
 * gevalideerd en worden fouten en waarschuwingen getoond.
 */

import { useRef, useState } from 'react';
import type { ActieType, AppData, Scherm, Tegel } from '../types';
import {
  ACTIE_OMSCHRIJVING,
  exportBestandsnaam,
  exporteerJson,
  nieuwScherm,
  nieuweTegel,
  standaardAppData,
  uniekId,
  valideerJsonTekst,
  verplaats,
} from '../modules/ContentEditor';
import { MAX_TEGELS_PER_SCHERM } from '../inhoud/standaardInstellingen';
import {
  controleerAfbeelding,
  controleerAudio,
  formatteerBytes,
  MAX_AFBEELDING_BYTES,
  MAX_AUDIO_BYTES,
} from '../modules/SafetyLayer';
import { bewaarMedia, nieuwMediaId, verwijderMedia } from '../modules/opslag';
import { downloadTekst, leesTekstbestand } from '../modules/bestanden';
import { Beeld } from './Beeld';

const ACTIE_TYPEN = Object.keys(ACTIE_OMSCHRIJVING) as ActieType[];

interface Props {
  appData: AppData;
  opSchermen: (schermen: Scherm[]) => void;
  opVolledigeData: (data: AppData) => void;
  opVoorbeeld: (schermId: string) => void;
}

interface Melding {
  soort: 'goed' | 'fout' | 'waarschuwing';
  titel: string;
  regels?: string[];
}

export function InhoudEditor({ appData, opSchermen, opVolledigeData, opVoorbeeld }: Props) {
  const schermen = appData.screens;
  const [gekozenId, zetGekozenId] = useState(schermen[0]?.id ?? '');
  const [melding, zetMelding] = useState<Melding | null>(null);
  const importVeld = useRef<HTMLInputElement>(null);

  const huidigIndex = Math.max(
    0,
    schermen.findIndex((scherm) => scherm.id === gekozenId),
  );
  const huidig = schermen[huidigIndex];

  const vervangScherm = (index: number, nieuw: Scherm) => {
    opSchermen(schermen.map((scherm, i) => (i === index ? nieuw : scherm)));
  };

  const wijzigTegel = (tegelIndex: number, nieuw: Tegel) => {
    if (!huidig) return;
    vervangScherm(huidigIndex, {
      ...huidig,
      items: huidig.items.map((item, i) => (i === tegelIndex ? nieuw : item)),
    });
  };

  // --- Schermen -----------------------------------------------------------

  const voegSchermToe = () => {
    const nieuw = nieuwScherm(schermen.map((scherm) => scherm.id));
    opSchermen([...schermen, nieuw]);
    zetGekozenId(nieuw.id);
    zetMelding({ soort: 'goed', titel: `Scherm "${nieuw.title}" toegevoegd.` });
  };

  const verwijderScherm = () => {
    if (!huidig) return;
    if (schermen.length <= 1) {
      zetMelding({ soort: 'fout', titel: 'Er moet minstens één scherm blijven bestaan.' });
      return;
    }
    const verwijzingen = schermen
      .filter((scherm) => scherm.id !== huidig.id)
      .flatMap((scherm) =>
        scherm.items
          .filter((item) => item.action.type === 'navigate' && item.action.target === huidig.id)
          .map((item) => `${scherm.title} > ${item.label}`),
      );
    if (verwijzingen.length) {
      zetMelding({
        soort: 'fout',
        titel: 'Dit scherm kan niet verwijderd worden; er verwijzen nog tegels naar.',
        regels: verwijzingen,
      });
      return;
    }
    const rest = schermen.filter((scherm) => scherm.id !== huidig.id);
    opSchermen(rest);
    zetGekozenId(rest[0]?.id ?? '');
    zetMelding({ soort: 'goed', titel: 'Scherm verwijderd.' });
  };

  const verplaatsScherm = (richting: -1 | 1) => {
    opSchermen(verplaats(schermen, huidigIndex, huidigIndex + richting));
  };

  // --- Tegels -------------------------------------------------------------

  const voegTegelToe = () => {
    if (!huidig) return;
    const alleTegelIds = schermen.flatMap((scherm) => scherm.items.map((item) => item.id));
    const nieuw = nieuweTegel(alleTegelIds);
    vervangScherm(huidigIndex, { ...huidig, items: [...huidig.items, nieuw] });
  };

  const verwijderTegel = (index: number) => {
    if (!huidig) return;
    vervangScherm(huidigIndex, {
      ...huidig,
      items: huidig.items.filter((_, i) => i !== index),
    });
  };

  const verplaatsTegel = (index: number, richting: -1 | 1) => {
    if (!huidig) return;
    vervangScherm(huidigIndex, { ...huidig, items: verplaats(huidig.items, index, index + richting) });
  };

  // --- Media --------------------------------------------------------------

  const uploadAfbeelding = async (tegelIndex: number, bestand: File) => {
    const controle = controleerAfbeelding(bestand);
    if (!controle.goed) {
      zetMelding({ soort: 'fout', titel: controle.fout ?? 'Bestand geweigerd.' });
      return;
    }
    const id = nieuwMediaId();
    await bewaarMedia({
      id,
      naam: bestand.name,
      type: bestand.type,
      grootte: bestand.size,
      soort: 'afbeelding',
      blob: bestand,
      toegevoegdOp: new Date().toISOString(),
    });
    const tegel = huidig?.items[tegelIndex];
    if (tegel) wijzigTegel(tegelIndex, { ...tegel, image: `media:${id}` });
    zetMelding({
      soort: 'goed',
      titel: `Afbeelding "${bestand.name}" toegevoegd (${formatteerBytes(bestand.size)}).`,
    });
  };

  const uploadAudio = async (tegelIndex: number, bestand: File) => {
    const controle = controleerAudio(bestand);
    if (!controle.goed) {
      zetMelding({ soort: 'fout', titel: controle.fout ?? 'Bestand geweigerd.' });
      return;
    }
    const id = nieuwMediaId();
    await bewaarMedia({
      id,
      naam: bestand.name,
      type: bestand.type,
      grootte: bestand.size,
      soort: 'audio',
      blob: bestand,
      toegevoegdOp: new Date().toISOString(),
    });
    const tegel = huidig?.items[tegelIndex];
    if (tegel) {
      wijzigTegel(tegelIndex, { ...tegel, action: { ...tegel.action, audio: `media:${id}` } });
    }
    zetMelding({
      soort: 'goed',
      titel: `Geluid "${bestand.name}" toegevoegd (${formatteerBytes(bestand.size)}).`,
    });
  };

  const verwijderTegelMedia = async (tegelIndex: number, soort: 'afbeelding' | 'audio') => {
    const tegel = huidig?.items[tegelIndex];
    if (!tegel) return;
    const verwijzing = soort === 'afbeelding' ? tegel.image : tegel.action.audio;
    if (verwijzing?.startsWith('media:')) {
      await verwijderMedia(verwijzing.slice('media:'.length));
    }
    if (soort === 'afbeelding') {
      const kopie = { ...tegel };
      delete kopie.image;
      wijzigTegel(tegelIndex, kopie);
    } else {
      const actie = { ...tegel.action };
      delete actie.audio;
      wijzigTegel(tegelIndex, { ...tegel, action: actie });
    }
  };

  // --- Import en export ---------------------------------------------------

  const exporteer = () => {
    downloadTekst(exportBestandsnaam(), exporteerJson(appData), 'application/json');
    zetMelding({ soort: 'goed', titel: 'Inhoud en instellingen zijn geëxporteerd.' });
  };

  const importeer = async (bestand: File) => {
    if (bestand.size > 4 * 1024 * 1024) {
      zetMelding({ soort: 'fout', titel: 'Het bestand is te groot (maximaal 4 MB).' });
      return;
    }
    const tekst = await leesTekstbestand(bestand);
    const resultaat = valideerJsonTekst(tekst);
    if (!resultaat.geldig || !resultaat.data) {
      zetMelding({
        soort: 'fout',
        titel: 'Het bestand is niet geïmporteerd; er zijn fouten gevonden.',
        regels: [...resultaat.fouten, ...resultaat.waarschuwingen],
      });
      return;
    }
    opVolledigeData(resultaat.data);
    zetGekozenId(resultaat.data.screens[0]?.id ?? '');
    zetMelding({
      soort: resultaat.waarschuwingen.length ? 'waarschuwing' : 'goed',
      titel: `Import gelukt: ${resultaat.data.screens.length} scherm(en) geladen.`,
      regels: resultaat.waarschuwingen,
    });
  };

  const herstelVoorbeeldinhoud = () => {
    const standaard = standaardAppData();
    opVolledigeData({ ...standaard, settings: appData.settings });
    zetGekozenId(standaard.screens[0]?.id ?? '');
    zetMelding({ soort: 'goed', titel: 'De voorbeeldinhoud is teruggezet.' });
  };

  // --- Weergave -----------------------------------------------------------

  return (
    <div>
      <section className="paneel">
        <h2>Inhoud beheren</h2>
        <p>
          Schermen en tegels aanpassen kan hier volledig zonder programmeerkennis. Afbeeldingen
          (max. {formatteerBytes(MAX_AFBEELDING_BYTES)}) en geluiden (max.{' '}
          {formatteerBytes(MAX_AUDIO_BYTES)}) worden alleen op dit apparaat opgeslagen.
        </p>
        <div className="knoppenrij" style={{ marginTop: 0 }}>
          <button type="button" className="knop" onClick={exporteer}>
            Exporteren naar JSON
          </button>
          <button type="button" className="knop" onClick={() => importVeld.current?.click()}>
            Importeren uit JSON
          </button>
          <input
            ref={importVeld}
            type="file"
            accept="application/json,.json"
            style={{ display: 'none' }}
            onChange={(event) => {
              const bestand = event.target.files?.[0];
              event.target.value = '';
              if (bestand) void importeer(bestand);
            }}
          />
          <button type="button" className="knop gevaar" onClick={herstelVoorbeeldinhoud}>
            Voorbeeldinhoud terugzetten
          </button>
        </div>

        {melding && (
          <div className={`melding ${melding.soort}`}>
            <strong>{melding.titel}</strong>
            {melding.regels && melding.regels.length > 0 && (
              <ul>
                {melding.regels.map((regel, i) => (
                  <li key={i}>{regel}</li>
                ))}
              </ul>
            )}
          </div>
        )}
      </section>

      <div className="editor">
        <section className="paneel">
          <h2>Schermen</h2>
          <ul className="schermlijst">
            {schermen.map((scherm) => (
              <li key={scherm.id}>
                <button
                  type="button"
                  aria-current={scherm.id === huidig?.id ? 'true' : 'false'}
                  onClick={() => zetGekozenId(scherm.id)}
                >
                  {scherm.title}
                  <br />
                  <small className="eenregel">
                    {scherm.id} · {scherm.items.length} tegel(s)
                  </small>
                </button>
              </li>
            ))}
          </ul>
          <div className="knoppenrij">
            <button type="button" className="knop klein" onClick={voegSchermToe}>
              Scherm toevoegen
            </button>
            <button
              type="button"
              className="knop klein"
              onClick={() => verplaatsScherm(-1)}
              disabled={huidigIndex <= 0}
            >
              Omhoog
            </button>
            <button
              type="button"
              className="knop klein"
              onClick={() => verplaatsScherm(1)}
              disabled={huidigIndex >= schermen.length - 1}
            >
              Omlaag
            </button>
            <button type="button" className="knop klein gevaar" onClick={verwijderScherm}>
              Verwijderen
            </button>
          </div>
          <p className="hulptekst">
            Het bovenste scherm is het beginscherm van de leerlingmodus.
          </p>
        </section>

        <section className="paneel">
          {!huidig ? (
            <p>Kies een scherm.</p>
          ) : (
            <>
              <h2>Scherm bewerken</h2>
              <div className="veldenrij">
                <div className="veld">
                  <label htmlFor="schermtitel">Titel (vraag boven de tegels)</label>
                  <input
                    id="schermtitel"
                    type="text"
                    value={huidig.title}
                    maxLength={80}
                    onChange={(event) =>
                      vervangScherm(huidigIndex, { ...huidig, title: event.target.value })
                    }
                  />
                </div>
                <div className="veld">
                  <span className="veldnaam">Scherm-id (vast)</span>
                  <div className="toetsvak">{huidig.id}</div>
                  <small>Wordt gebruikt door tegels die naar dit scherm verwijzen.</small>
                </div>
              </div>
              <div className="aanvinken">
                <input
                  id="schermzichtbaar"
                  type="checkbox"
                  checked={huidig.zichtbaar !== false}
                  onChange={(event) =>
                    vervangScherm(huidigIndex, { ...huidig, zichtbaar: event.target.checked })
                  }
                />
                <label htmlFor="schermzichtbaar">Scherm in gebruik</label>
              </div>
              <div className="knoppenrij">
                <button type="button" className="knop" onClick={() => opVoorbeeld(huidig.id)}>
                  Voorbeeld bekijken
                </button>
                <button
                  type="button"
                  className="knop"
                  onClick={voegTegelToe}
                  disabled={huidig.items.length >= MAX_TEGELS_PER_SCHERM}
                >
                  Tegel toevoegen
                </button>
              </div>
              {huidig.items.length >= MAX_TEGELS_PER_SCHERM && (
                <p className="hulptekst">
                  Er staan {MAX_TEGELS_PER_SCHERM} tegels op dit scherm; dat is het maximum voor de
                  leerlingmodus.
                </p>
              )}

              <h3>Tegels</h3>
              {huidig.items.map((tegel, index) => (
                <TegelEditor
                  key={tegel.id}
                  tegel={tegel}
                  index={index}
                  aantal={huidig.items.length}
                  schermen={schermen}
                  alleTegelIds={schermen.flatMap((scherm) => scherm.items.map((item) => item.id))}
                  opWijzig={(nieuw) => wijzigTegel(index, nieuw)}
                  opVerwijder={() => verwijderTegel(index)}
                  opVerplaats={(richting) => verplaatsTegel(index, richting)}
                  opAfbeelding={(bestand) => void uploadAfbeelding(index, bestand)}
                  opAudio={(bestand) => void uploadAudio(index, bestand)}
                  opMediaWeg={(soort) => void verwijderTegelMedia(index, soort)}
                />
              ))}
            </>
          )}
        </section>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Eén tegel bewerken
// ---------------------------------------------------------------------------

interface TegelEditorProps {
  tegel: Tegel;
  index: number;
  aantal: number;
  schermen: Scherm[];
  alleTegelIds: string[];
  opWijzig: (tegel: Tegel) => void;
  opVerwijder: () => void;
  opVerplaats: (richting: -1 | 1) => void;
  opAfbeelding: (bestand: File) => void;
  opAudio: (bestand: File) => void;
  opMediaWeg: (soort: 'afbeelding' | 'audio') => void;
}

function TegelEditor({
  tegel,
  index,
  aantal,
  schermen,
  alleTegelIds,
  opWijzig,
  opVerwijder,
  opVerplaats,
  opAfbeelding,
  opAudio,
  opMediaWeg,
}: TegelEditorProps) {
  const afbeeldingVeld = useRef<HTMLInputElement>(null);
  const audioVeld = useRef<HTMLInputElement>(null);
  const heeftDoel = tegel.action.type === 'navigate';

  const wijzigActie = (deel: Partial<Tegel['action']>) => {
    opWijzig({ ...tegel, action: { ...tegel.action, ...deel } });
  };

  return (
    <div className="tegelkaart">
      <div className="tegelkaart-kop">
        <span className="kleurstip" style={{ background: tegel.kleur ?? '#1e293b' }} />
        <strong>
          {index + 1}. {tegel.label}
        </strong>
        <button
          type="button"
          className="knop klein"
          onClick={() => opVerplaats(-1)}
          disabled={index === 0}
        >
          Omhoog
        </button>
        <button
          type="button"
          className="knop klein"
          onClick={() => opVerplaats(1)}
          disabled={index === aantal - 1}
        >
          Omlaag
        </button>
        <button type="button" className="knop klein gevaar" onClick={opVerwijder}>
          Verwijderen
        </button>
      </div>

      <div className="veldenrij">
        <div className="veld">
          <label htmlFor={`label-${tegel.id}`}>Label (kort)</label>
          <input
            id={`label-${tegel.id}`}
            type="text"
            maxLength={60}
            value={tegel.label}
            onChange={(event) => opWijzig({ ...tegel, label: event.target.value })}
          />
        </div>
        <div className="veld">
          <label htmlFor={`emoji-${tegel.id}`}>Emoji als beeld</label>
          <input
            id={`emoji-${tegel.id}`}
            type="text"
            maxLength={8}
            value={tegel.emoji ?? ''}
            onChange={(event) => opWijzig({ ...tegel, emoji: event.target.value })}
          />
          <small>Wordt gebruikt zolang er geen afbeelding is.</small>
        </div>
        <div className="veld">
          <label htmlFor={`kleur-${tegel.id}`}>Kleur van de tegel</label>
          <input
            id={`kleur-${tegel.id}`}
            type="text"
            value={tegel.kleur ?? '#1e293b'}
            onChange={(event) => opWijzig({ ...tegel, kleur: event.target.value })}
          />
          <small>Hexkleur, bijvoorbeeld #2563eb.</small>
        </div>
        <div className="veld">
          <label htmlFor={`spreek-${tegel.id}`}>Gesproken benoeming</label>
          <input
            id={`spreek-${tegel.id}`}
            type="text"
            maxLength={120}
            value={tegel.spreekTekst ?? ''}
            placeholder={tegel.label}
            onChange={(event) => opWijzig({ ...tegel, spreekTekst: event.target.value })}
          />
          <small>Leeg laten om het label te gebruiken.</small>
        </div>
        <div className="veld">
          <label htmlFor={`actie-${tegel.id}`}>Wat gebeurt er bij een keuze?</label>
          <select
            id={`actie-${tegel.id}`}
            value={tegel.action.type}
            onChange={(event) => wijzigActie({ type: event.target.value as ActieType })}
          >
            {ACTIE_TYPEN.map((type) => (
              <option key={type} value={type}>
                {ACTIE_OMSCHRIJVING[type]}
              </option>
            ))}
          </select>
        </div>
        {heeftDoel && (
          <div className="veld">
            <label htmlFor={`doel-${tegel.id}`}>Naar welk scherm?</label>
            <select
              id={`doel-${tegel.id}`}
              value={tegel.action.target ?? ''}
              onChange={(event) => wijzigActie({ target: event.target.value })}
            >
              <option value="">— kies een scherm —</option>
              {schermen.map((scherm) => (
                <option key={scherm.id} value={scherm.id}>
                  {scherm.title} ({scherm.id})
                </option>
              ))}
            </select>
          </div>
        )}
        {!heeftDoel && (
          <>
            <div className="veld">
              <label htmlFor={`tekst-${tegel.id}`}>Tekst in beeld / gesproken boodschap</label>
              <input
                id={`tekst-${tegel.id}`}
                type="text"
                maxLength={200}
                value={tegel.action.tekst ?? ''}
                onChange={(event) => wijzigActie({ tekst: event.target.value })}
              />
            </div>
            <div className="veld">
              <label htmlFor={`duur-${tegel.id}`}>Duur van de actie (ms)</label>
              <input
                id={`duur-${tegel.id}`}
                type="number"
                min={500}
                max={60000}
                step={500}
                value={tegel.action.duurMs ?? 6000}
                onChange={(event) => wijzigActie({ duurMs: Number(event.target.value) })}
              />
            </div>
          </>
        )}
      </div>

      <h3>Eigen beeld en geluid</h3>
      <div className="veldenrij">
        <div className="veld">
          <span className="veldnaam">Afbeelding</span>
          <div className="toetsvak">{tegel.image ?? 'geen afbeelding (emoji wordt gebruikt)'}</div>
          <div className="knoppenrij" style={{ marginTop: 0 }}>
            <button
              type="button"
              className="knop klein"
              onClick={() => afbeeldingVeld.current?.click()}
            >
              Afbeelding kiezen
            </button>
            {tegel.image && (
              <button
                type="button"
                className="knop klein gevaar"
                onClick={() => opMediaWeg('afbeelding')}
              >
                Verwijderen
              </button>
            )}
          </div>
          <input
            ref={afbeeldingVeld}
            type="file"
            accept="image/*"
            style={{ display: 'none' }}
            onChange={(event) => {
              const bestand = event.target.files?.[0];
              event.target.value = '';
              if (bestand) opAfbeelding(bestand);
            }}
          />
        </div>

        <div className="veld">
          <span className="veldnaam">Geluid</span>
          <div className="toetsvak">{tegel.action.audio ?? 'geen geluid'}</div>
          <div className="knoppenrij" style={{ marginTop: 0 }}>
            <button type="button" className="knop klein" onClick={() => audioVeld.current?.click()}>
              Geluid kiezen
            </button>
            {tegel.action.audio && (
              <button
                type="button"
                className="knop klein gevaar"
                onClick={() => opMediaWeg('audio')}
              >
                Verwijderen
              </button>
            )}
          </div>
          <input
            ref={audioVeld}
            type="file"
            accept="audio/*"
            style={{ display: 'none' }}
            onChange={(event) => {
              const bestand = event.target.files?.[0];
              event.target.value = '';
              if (bestand) opAudio(bestand);
            }}
          />
          <small>Ontbreekt het bestand, dan benoemt de app de keuze met spraak.</small>
        </div>

        <div className="veld">
          <span className="veldnaam">Voorbeeld</span>
          <div className="voorbeeldtegel" style={{ background: tegel.kleur ?? '#1e293b' }}>
            <span className="beeld">
              <Beeld verwijzing={tegel.image} emoji={tegel.emoji} />
            </span>
            <span>{tegel.label}</span>
          </div>
        </div>
      </div>

      <div className="aanvinken">
        <input
          id={`zichtbaar-${tegel.id}`}
          type="checkbox"
          checked={tegel.zichtbaar !== false}
          onChange={(event) => opWijzig({ ...tegel, zichtbaar: event.target.checked })}
        />
        <label htmlFor={`zichtbaar-${tegel.id}`}>Zichtbaar voor de leerling</label>
      </div>
      <p className="hulptekst">
        Tegel-id: <span className="eenregel">{tegel.id}</span>
        {alleTegelIds.filter((id) => id === tegel.id).length > 1 && (
          <>
            {' '}
            <span className="merk let-op">
              dit id komt meer dan één keer voor; gebruik "{uniekId(tegel.id, alleTegelIds)}"
            </span>
          </>
        )}
      </p>
    </div>
  );
}
