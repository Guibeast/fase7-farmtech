import sqlite3
from datetime import datetime
from pathlib import Path

import pandas as pd

DB_PATH = Path(__file__).resolve().parent.parent / 'data' / 'farmtech.db'


def _connect():
    return sqlite3.connect(str(DB_PATH))


def init_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with _connect() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS LEITURAS_SENSOR (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp  TEXT,
                umidade    REAL,
                temperatura REAL,
                ph         REAL,
                nivel_N    REAL,
                nivel_P    INTEGER,
                nivel_K    INTEGER,
                bomba_ativa INTEGER
            )
        """)
        conn.commit()


def inserir_leitura(leitura: dict):
    with _connect() as conn:
        conn.execute(
            """
            INSERT INTO LEITURAS_SENSOR
                (timestamp, umidade, temperatura, ph, nivel_N, nivel_P, nivel_K, bomba_ativa)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                leitura.get('timestamp', datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
                leitura['umidade'],
                leitura['temperatura'],
                leitura['ph'],
                leitura['nivel_N'],
                int(leitura['nivel_P']),
                int(leitura['nivel_K']),
                int(leitura['bomba_ativa']),
            ),
        )
        conn.commit()


def consultar_ultimas(n: int = 20) -> pd.DataFrame:
    with _connect() as conn:
        df = pd.read_sql_query(
            "SELECT * FROM LEITURAS_SENSOR ORDER BY id DESC LIMIT ?",
            conn,
            params=(int(n),),
        )
    return df


def estatisticas_sql() -> dict:
    with _connect() as conn:
        cur = conn.execute("""
            SELECT
                AVG(umidade)     AS avg_umidade,
                MAX(ph)          AS max_ph,
                MIN(ph)          AS min_ph,
                AVG(temperatura) AS avg_temp,
                COUNT(*)         AS total,
                AVG(nivel_N)     AS avg_N
            FROM LEITURAS_SENSOR
        """)
        row = cur.fetchone()

    if row is None or row[4] == 0:
        return {'avg_umidade': 0, 'max_ph': 0, 'min_ph': 0, 'avg_temp': 0, 'total': 0, 'avg_N': 0}

    return {
        'avg_umidade': row[0] or 0,
        'max_ph':      row[1] or 0,
        'min_ph':      row[2] or 0,
        'avg_temp':    row[3] or 0,
        'total':       row[4] or 0,
        'avg_N':       row[5] or 0,
    }
