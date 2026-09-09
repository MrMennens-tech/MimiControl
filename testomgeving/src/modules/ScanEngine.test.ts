/**
 * Tests voor de scanner: vaste scanvolgorde, automatisch scannen op tijd,
 * stoppen na een aantal rondes en de handmatige stapscan.
 */

import { beforeEach, describe, expect, it, vi } from 'vitest';
import { ScanEngine } from './ScanEngine';

/** Eenvoudige nepklok zodat de tests niet echt hoeven te wachten. */
function maakEngine(opties: { rondes?: number; willekeurig?: () => number } = {}) {
  const focus: number[] = [];
  const gestopt: number[] = [];
  const rondes: number[] = [];
  const engine = new ScanEngine({
    willekeurig: opties.willekeurig,
    opFocus: (index) => focus.push(index),
    opRondeAf: (nummer) => rondes.push(nummer),
    opGestopt: (aantal) => gestopt.push(aantal),
  });
  return { engine, focus, gestopt, rondes };
}

describe('handmatige stapscan (modus 2 en 3)', () => {
  it('loopt in vaste volgorde langs de tegels en begint daarna opnieuw', () => {
    const { engine, focus } = maakEngine();
    engine.configureer({
      aantal: 4,
      modus: 'handmatig',
      intervalMs: 1000,
      rondes: 0,
      startTegel: 'eerste',
    });
    expect(focus).toEqual([0]);

    engine.volgende();
    engine.volgende();
    engine.volgende();
    engine.volgende();

    expect(focus).toEqual([0, 1, 2, 3, 0]);
    expect(engine.huidigeIndex).toBe(0);
  });

  it('meldt een afgeronde ronde zodra de beginpositie weer bereikt is', () => {
    const { engine, rondes } = maakEngine();
    engine.configureer({
      aantal: 3,
      modus: 'handmatig',
      intervalMs: 1000,
      rondes: 0,
      startTegel: 'eerste',
    });
    engine.volgende();
    engine.volgende();
    expect(rondes).toEqual([]);
    engine.volgende();
    expect(rondes).toEqual([1]);
  });

  it('start bij een willekeurige tegel wanneer dat ingesteld is', () => {
    const { engine, focus } = maakEngine({ willekeurig: () => 0.6 });
    engine.configureer({
      aantal: 4,
      modus: 'handmatig',
      intervalMs: 1000,
      rondes: 0,
      startTegel: 'willekeurig',
    });
    expect(focus).toEqual([2]);
  });

  it('kan de markering op een vaste tegel zetten (bijv. na teruggaan)', () => {
    const { engine, focus } = maakEngine();
    engine.configureer({
      aantal: 4,
      modus: 'handmatig',
      intervalMs: 1000,
      rondes: 0,
      startTegel: 'eerste',
      startIndex: 2,
    });
    expect(focus).toEqual([2]);
    engine.zetIndex(1);
    expect(engine.huidigeIndex).toBe(1);
  });

  it('doet niets bij een scherm zonder tegels', () => {
    const { engine, focus } = maakEngine();
    engine.configureer({
      aantal: 0,
      modus: 'handmatig',
      intervalMs: 1000,
      rondes: 0,
      startTegel: 'eerste',
    });
    expect(focus).toEqual([]);
    expect(engine.volgende()).toBe(-1);
    expect(engine.huidigeIndex).toBe(-1);
  });
});

describe('automatische scan (modus 1)', () => {
  beforeEach(() => {
    vi.useFakeTimers();
    return () => vi.useRealTimers();
  });

  it('zet de markering na elke scantijd één tegel verder', () => {
    const { engine, focus } = maakEngine();
    engine.configureer({
      aantal: 3,
      modus: 'automatisch',
      intervalMs: 2000,
      rondes: 0,
      startTegel: 'eerste',
    });
    engine.start();
    expect(focus).toEqual([0]);

    vi.advanceTimersByTime(1999);
    expect(focus).toEqual([0]);

    vi.advanceTimersByTime(1);
    expect(focus).toEqual([0, 1]);

    vi.advanceTimersByTime(4000);
    expect(focus).toEqual([0, 1, 2, 0]);
  });

  it('stopt na het ingestelde aantal rondes', () => {
    const { engine, focus, gestopt } = maakEngine();
    engine.configureer({
      aantal: 2,
      modus: 'automatisch',
      intervalMs: 1000,
      rondes: 2,
      startTegel: 'eerste',
    });
    engine.start();

    vi.advanceTimersByTime(10000);

    // Twee volledige rondes: 0,1,0,1,0 en dan stoppen.
    expect(focus).toEqual([0, 1, 0, 1, 0]);
    expect(gestopt).toEqual([2]);
    expect(engine.isActief).toBe(false);
  });

  it('blijft doorscannen wanneer het aantal rondes 0 is', () => {
    const { engine, gestopt } = maakEngine();
    engine.configureer({
      aantal: 2,
      modus: 'automatisch',
      intervalMs: 500,
      rondes: 0,
      startTegel: 'eerste',
    });
    engine.start();
    vi.advanceTimersByTime(20000);
    expect(gestopt).toEqual([]);
    expect(engine.isActief).toBe(true);
  });

  it('stopt de timer bij stop() en begint bij herstart() opnieuw', () => {
    const { engine, focus } = maakEngine();
    engine.configureer({
      aantal: 3,
      modus: 'automatisch',
      intervalMs: 1000,
      rondes: 0,
      startTegel: 'eerste',
    });
    engine.start();
    vi.advanceTimersByTime(1000);
    engine.stop();
    vi.advanceTimersByTime(5000);
    expect(focus).toEqual([0, 1]);

    engine.herstart();
    expect(focus).toEqual([0, 1, 0]);
    vi.advanceTimersByTime(1000);
    expect(focus).toEqual([0, 1, 0, 1]);
  });

  it('start niet automatisch in de handmatige modus', () => {
    const { engine, focus } = maakEngine();
    engine.configureer({
      aantal: 3,
      modus: 'handmatig',
      intervalMs: 500,
      rondes: 0,
      startTegel: 'eerste',
    });
    engine.start();
    vi.advanceTimersByTime(5000);
    expect(focus).toEqual([0]);
  });
});
