/**
 * App - houdt de weergave bij (startscherm, leerlingmodus, begeleidersmodus),
 * laadt en bewaart de gegevens en verbindt de besturing met de interface.
 *
 * De besturing zelf zit in `modules/Besturing.ts`; deze component tekent
 * alleen wat daar gebeurt.
 */

import { useCallback, useEffect, useRef, useState } from 'react';
import type { AppData, Instellingen, Scherm, Sessie } from './types';
import { Besturing, type BesturingStatus } from './modules/Besturing';
import { SessionLogger } from './modules/SessionLogger';
import { standaardAppData } from './modules/ContentEditor';
import {
  bewaarAppData,
  bewaarSessie,
  isGeheugenopslag,
  laadAppData,
  laadSessies,
  wisAlleSessies,
} from './modules/opslag';
import { activeerLinkbescherming } from './modules/SafetyLayer';
import {
  isVolledigScherm,
  naarVolledigScherm,
  verlaatVolledigScherm,
} from './modules/bestanden';
import { omschrijfBinding } from './modules/toetsnamen';
import { Begeleidersmodus } from './componenten/Begeleidersmodus';
import { Leerlingmodus } from './componenten/Leerlingmodus';
import { Pincode } from './componenten/Pincode';

type Weergave = 'start' | 'leerling' | 'begeleider';

export function App() {
  const [appData, zetAppData] = useState<AppData | null>(null);
  const [status, zetStatus] = useState<BesturingStatus | null>(null);
  const [sessie, zetSessie] = useState<Sessie | null>(null);
  const [eerdereSessies, zetEerdereSessies] = useState<Sessie[]>([]);
  const [weergave, zetWeergave] = useState<Weergave>('start');
  const [pinOpen, zetPinOpen] = useState(false);
  const [opslagWaarschuwing, zetOpslagWaarschuwing] = useState<string | null>(null);

  const besturingRef = useRef<Besturing | null>(null);
  const bewaarTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Sessielogboek: één instantie voor de hele levensduur van de app.
  const loggerRef = useRef<SessionLogger | null>(null);
  if (!loggerRef.current) {
    loggerRef.current = new SessionLogger({
      opWijziging: (huidige) => {
        zetSessie({ ...huidige, gebeurtenissen: [...huidige.gebeurtenissen] });
        // Niet bij elke gebeurtenis naar de database schrijven.
        if (bewaarTimer.current) clearTimeout(bewaarTimer.current);
        bewaarTimer.current = setTimeout(() => {
          void bewaarSessie({ ...huidige, gebeurtenissen: [...huidige.gebeurtenissen] });
        }, 1200);
      },
    });
  }
  const logger = loggerRef.current;

  // --- Laden --------------------------------------------------------------

  useEffect(() => {
    let geldig = true;
    void (async () => {
      const bewaard = await laadAppData();
      const sessies = await laadSessies();
      if (!geldig) return;
      zetAppData(bewaard ?? standaardAppData());
      zetEerdereSessies(sessies);
      if (isGeheugenopslag()) {
        zetOpslagWaarschuwing(
          'De lokale database is niet beschikbaar. De app werkt wel, maar instellingen en sessies worden niet bewaard.',
        );
      }
    })();
    return () => {
      geldig = false;
    };
  }, []);

  // Externe links en slepen van bestanden blokkeren.
  useEffect(() => activeerLinkbescherming(document), []);

  // --- Besturing ----------------------------------------------------------

  useEffect(() => {
    if (!appData) return;
    if (!besturingRef.current) {
      const besturing = new Besturing({
        appData,
        logger,
        opStatus: (nieuw) => zetStatus(nieuw),
      });
      besturingRef.current = besturing;
      zetStatus(besturing.status());
      return;
    }
    besturingRef.current.zetAppData(appData);
  }, [appData, logger]);

  // Instellingen en inhoud bewaren zodra ze wijzigen.
  useEffect(() => {
    if (!appData) return;
    void bewaarAppData(appData);
  }, [appData]);

  // Verborgen toetscombinatie om de begeleidersmodus te openen.
  useEffect(() => {
    if (weergave !== 'leerling') return;
    const opKeydown = (event: KeyboardEvent) => {
      if (event.ctrlKey && event.shiftKey && (event.code === 'KeyB' || event.key === 'B' || event.key === 'b')) {
        event.preventDefault();
        zetPinOpen(true);
      }
    };
    window.addEventListener('keydown', opKeydown, true);
    return () => window.removeEventListener('keydown', opKeydown, true);
  }, [weergave]);

  // Staat het pincodevenster open, dan mogen toetsen niet tegelijk de
  // leerlingmodus bedienen: Enter zou anders ook een tegel kiezen.
  useEffect(() => {
    if (weergave !== 'leerling' || !pinOpen) return;
    const besturing = besturingRef.current;
    besturing?.stopLuisteren();
    return () => besturing?.luister(window);
  }, [pinOpen, weergave]);

  // --- Acties -------------------------------------------------------------

  const startLeerlingmodus = useCallback(
    async (schermId?: string) => {
      const besturing = besturingRef.current;
      if (!besturing || !appData) return;
      if (appData.settings.volledigSchermStarten) await naarVolledigScherm();
      zetWeergave('leerling');
      if (schermId) besturing.startVoorbeeld(schermId, window);
      else besturing.start(window);
    },
    [appData],
  );

  const naarBegeleider = useCallback(() => {
    besturingRef.current?.pauzeer();
    zetWeergave('begeleider');
    zetPinOpen(false);
  }, []);

  const stopSessie = useCallback(() => {
    besturingRef.current?.stop();
    const gestopt = logger.huidigeSessie;
    if (gestopt) {
      void bewaarSessie({ ...gestopt, gebeurtenissen: [...gestopt.gebeurtenissen] }).then(() =>
        laadSessies().then(zetEerdereSessies),
      );
    }
  }, [logger]);

  const resetSessie = useCallback(() => {
    besturingRef.current?.pauzeer();
    logger.reset();
    zetSessie(null);
  }, [logger]);

  const wijzigInstellingen = useCallback((instellingen: Instellingen) => {
    zetAppData((oud) => (oud ? { ...oud, settings: instellingen } : oud));
  }, []);

  const wijzigSchermen = useCallback((schermen: Scherm[]) => {
    zetAppData((oud) => (oud ? { ...oud, screens: schermen } : oud));
  }, []);

  const wisSessies = useCallback(() => {
    void wisAlleSessies().then(() => {
      zetEerdereSessies([]);
      logger.reset();
      zetSessie(null);
    });
  }, [logger]);

  const wisselVolledigScherm = useCallback(() => {
    if (isVolledigScherm()) void verlaatVolledigScherm();
    else void naarVolledigScherm();
  }, []);

  // --- Weergave -----------------------------------------------------------

  if (!appData || !status) {
    return (
      <div className="start">
        <div className="start-kaart">
          <h1>Bezig met laden…</h1>
          <p>De instellingen en de inhoud worden uit de lokale opslag gehaald.</p>
        </div>
      </div>
    );
  }

  if (weergave === 'leerling') {
    return (
      <>
        <Leerlingmodus
          status={status}
          instellingen={appData.settings}
          opTegelKlik={(index) => besturingRef.current?.klikTegel(index)}
          opActieKlik={() => besturingRef.current?.klikTegel(status.focusIndex)}
          opVerborgenHoek={() => zetPinOpen(true)}
        />
        {pinOpen && (
          <Pincode
            verwachtePincode={appData.settings.pincode}
            opGoed={naarBegeleider}
            opAfbreken={() => zetPinOpen(false)}
          />
        )}
      </>
    );
  }

  if (weergave === 'begeleider') {
    return (
      <Begeleidersmodus
        appData={appData}
        huidigeSessie={sessie}
        eerdereSessies={eerdereSessies}
        sessieActief={logger.isActief}
        opslagWaarschuwing={opslagWaarschuwing}
        mediaMeldingen={status.mediaMeldingen}
        opInstellingen={wijzigInstellingen}
        opSchermen={wijzigSchermen}
        opVolledigeData={(data) => zetAppData(data)}
        opSessieStart={() => void startLeerlingmodus()}
        opSessieStop={stopSessie}
        opSessieReset={resetSessie}
        opNotities={(tekst) => logger.zetNotities(tekst)}
        opWisSessies={wisSessies}
        opVolledigScherm={wisselVolledigScherm}
        opVoorbeeld={(schermId) => void startLeerlingmodus(schermId)}
        opSluiten={() => zetWeergave('start')}
      />
    );
  }

  return (
    <>
      <Startscherm
        appData={appData}
        opStart={() => void startLeerlingmodus()}
        opBegeleider={() => zetPinOpen(true)}
      />
      {pinOpen && (
        <Pincode
          verwachtePincode={appData.settings.pincode}
          opGoed={naarBegeleider}
          opAfbreken={() => zetPinOpen(false)}
        />
      )}
    </>
  );
}

// ---------------------------------------------------------------------------
// Startscherm
// ---------------------------------------------------------------------------

interface StartschermProps {
  appData: AppData;
  opStart: () => void;
  opBegeleider: () => void;
}

function Startscherm({ appData, opStart, opBegeleider }: StartschermProps) {
  const { settings } = appData;
  return (
    <div className="start">
      <div className="start-kaart">
        <h1>Toetsentestomgeving</h1>
        <p>
          Een rustige omgeving om te kijken hoe iemand met één, twee of drie toetsen keuzes maakt.
          Alles blijft op dit apparaat: geen server, geen account, geen trackers.
        </p>

        <div className="samenvatting-instellingen">
          <div>
            <span>Bedieningsmodus</span>
            {settings.controlMode} toets(en)
          </div>
          <div>
            <span>Scantijd</span>
            {settings.scanIntervalMs} ms
          </div>
          <div>
            <span>Invoerblokkade</span>
            {settings.selectionCooldownMs} ms
          </div>
          <div>
            <span>Selecteren met</span>
            {omschrijfBinding(settings.keys.select)}
          </div>
          {settings.controlMode >= 2 && (
            <div>
              <span>Volgende met</span>
              {omschrijfBinding(settings.keys.next)}
            </div>
          )}
          {settings.controlMode === 3 && (
            <div>
              <span>Terug met</span>
              {omschrijfBinding(settings.keys.back)}
            </div>
          )}
        </div>

        <div className="start-knoppen">
          <button type="button" className="knop primair" onClick={opStart}>
            Leerlingmodus starten
          </button>
          <button type="button" className="knop" onClick={opBegeleider}>
            Begeleidersmodus
          </button>
        </div>

        <p className="hulptekst">
          In de leerlingmodus opent de begeleidersmodus met Ctrl + Shift + B of met drie klikken in
          de linkerbovenhoek.
        </p>
      </div>
    </div>
  );
}
