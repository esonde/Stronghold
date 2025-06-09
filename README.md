
# Fort Wars

Un prototipo minimale del gioco turn–based progettato per agenti di RL con interfaccia grafica interattiva.

## Caratteristiche principali
* Mappa bidimensionale generata proceduralmente (`terrain.py`).
* Regole di gioco complete (`game.py`).
* Salvataggio e caricamento partite in JSON (`save_load.py`).
* Interfaccia grafica `pygame` (`gui.py`):
  * Hover con info sul forte.
  * Checkbox/shortcut **I** per mostrare le aree di influenza (raggio *k*).
  * **S** per salvare la partita corrente.
* **P** o click destro per passare il turno (pass automatico se nessuna mossa).
* Click sinistro o **INVIO** piazza il forte.
  * Finestra ridimensionabile con griglia centrata e menu iniziale per caricare vecchie partite.
  * Replay: `python play.py --replay path_to_saved.json`.
  * Nel replay **SPAZIO** avanza di un’azione, **R** avvia/arresta autoplay.
* Forte non piazzabile sull'acqua e produzione aumentata se adiacente a un altro proprio forte.
* Il punteggio è la somma dei quadrati delle altezze dei propri forti.

## Installazione rapida

```bash
pip install -r requirements.txt
python play.py            # nuova partita
python play.py --replay fortwars_YYYYMMDD_HHMMSS.json   # replay
```

## Struttura

```
terrain.py      # generatore mappa
game.py         # logica di gioco + serializzazione
save_load.py    # utilità I/O JSON
gui.py          # interfaccia pygame + replay
play.py         # entry‑point
```

---

*Creato automaticamente da ChatGPT*.
