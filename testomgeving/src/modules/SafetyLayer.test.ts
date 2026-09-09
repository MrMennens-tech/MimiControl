/** Tests voor de veiligheidslaag: media, externe links en verdachte inhoud. */

import { describe, expect, it } from 'vitest';
import {
  bevatVerdachteInhoud,
  controleerAfbeelding,
  controleerAudio,
  formatteerBytes,
  isExterneLink,
  isVeiligeMediaVerwijzing,
  MAX_AFBEELDING_BYTES,
  MAX_AUDIO_BYTES,
  veiligeTekst,
} from './SafetyLayer';

describe('bestandscontrole', () => {
  it('aanvaardt een normale afbeelding', () => {
    expect(controleerAfbeelding({ type: 'image/png', size: 120000 }).goed).toBe(true);
  });

  it('weigert een te grote afbeelding', () => {
    const controle = controleerAfbeelding({ type: 'image/png', size: MAX_AFBEELDING_BYTES + 1 });
    expect(controle.goed).toBe(false);
    expect(controle.fout).toContain('te groot');
  });

  it('weigert een verkeerd bestandstype', () => {
    expect(controleerAfbeelding({ type: 'application/pdf', size: 100 }).goed).toBe(false);
    expect(controleerAudio({ type: 'video/mp4', size: 100 }).goed).toBe(false);
  });

  it('aanvaardt geluid tot de grens', () => {
    expect(controleerAudio({ type: 'audio/mpeg', size: MAX_AUDIO_BYTES }).goed).toBe(true);
    expect(controleerAudio({ type: 'audio/mpeg', size: MAX_AUDIO_BYTES + 1 }).goed).toBe(false);
  });

  it('geeft bestandsgroottes leesbaar weer', () => {
    expect(formatteerBytes(512)).toBe('512 B');
    expect(formatteerBytes(2048)).toBe('2 kB');
    expect(formatteerBytes(1572864)).toBe('1,5 MB');
  });
});

describe('mediaverwijzingen', () => {
  it('aanvaardt lokale uploads en relatieve paden', () => {
    expect(isVeiligeMediaVerwijzing('media:abc123')).toBe(true);
    expect(isVeiligeMediaVerwijzing('assets/hond.mp3')).toBe(true);
    expect(isVeiligeMediaVerwijzing('')).toBe(true);
  });

  it('weigert externe en gevaarlijke verwijzingen', () => {
    expect(isVeiligeMediaVerwijzing('https://voorbeeld.nl/a.mp3')).toBe(false);
    expect(isVeiligeMediaVerwijzing('//voorbeeld.nl/a.mp3')).toBe(false);
    expect(isVeiligeMediaVerwijzing('javascript:alert(1)')).toBe(false);
    expect(isVeiligeMediaVerwijzing('/etc/passwd')).toBe(false);
    expect(isVeiligeMediaVerwijzing('../../geheim.mp3')).toBe(false);
    expect(isVeiligeMediaVerwijzing('media:met ruimte')).toBe(false);
  });
});

describe('verdachte inhoud', () => {
  it('herkent HTML, scripts en gevaarlijke adressen', () => {
    expect(bevatVerdachteInhoud('<script>alert(1)</script>')).toBe(true);
    expect(bevatVerdachteInhoud('<iframe src="x">')).toBe(true);
    expect(bevatVerdachteInhoud('onclick=doe()')).toBe(true);
    expect(bevatVerdachteInhoud('javascript:alert(1)')).toBe(true);
    expect(bevatVerdachteInhoud('data:text/html,<b>x</b>')).toBe(true);
  });

  it('laat gewone tekst door', () => {
    expect(bevatVerdachteInhoud('Muziek kiezen')).toBe(false);
    expect(bevatVerdachteInhoud('Hond & kat')).toBe(false);
  });

  it('verwijdert stuurtekens en kort te lange tekst af', () => {
    expect(veiligeTekst('  hallo\u0000wereld  ')).toBe('hallowereld');
    expect(veiligeTekst('a'.repeat(500), 10)).toHaveLength(10);
    expect(veiligeTekst(42)).toBe('');
  });
});

describe('externe links', () => {
  it('herkent adressen die de app verlaten', () => {
    expect(isExterneLink('https://voorbeeld.nl')).toBe(true);
    expect(isExterneLink('http://voorbeeld.nl')).toBe(true);
    expect(isExterneLink('mailto:iemand@voorbeeld.nl')).toBe(true);
    expect(isExterneLink('//voorbeeld.nl')).toBe(true);
  });

  it('laat interne verwijzingen door', () => {
    expect(isExterneLink('#tabblad')).toBe(false);
    expect(isExterneLink('')).toBe(false);
  });
});
