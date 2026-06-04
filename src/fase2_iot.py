import random
from datetime import datetime, timedelta

import numpy as np
import pandas as pd

THRESHOLDS = {
    'ph_min': 5.5,
    'ph_max': 7.5,
    'umidade_min': 30.0,
    'umidade_max': 80.0,
    'N_min': 80.0,
    'temp_max': 38.0,
}


def gerar_leitura_sensor(seed=None) -> dict:
    if seed is not None:
        random.seed(seed)
        np.random.seed(seed)

    umidade = round(random.uniform(20.0, 90.0), 2)
    temperatura = round(random.uniform(18.0, 42.0), 2)
    ph = round(random.uniform(4.5, 8.5), 2)
    nivel_N = round(random.uniform(40.0, 300.0), 2)
    nivel_P = random.choice([True, False])
    nivel_K = random.choice([True, False])

    leitura = {
        'umidade': umidade,
        'temperatura': temperatura,
        'ph': ph,
        'nivel_N': nivel_N,
        'nivel_P': nivel_P,
        'nivel_K': nivel_K,
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    }
    leitura['bomba_ativa'] = deve_ligar_bomba(leitura)
    return leitura


def deve_ligar_bomba(leitura: dict) -> bool:
    # replica lógica do bomba_npk.ino:
    # irriga se umidade crítica OU nitrogênio baixo com pH fora do ideal
    umidade_critica = leitura['umidade'] < 40.0
    ph_fora = leitura['ph'] < THRESHOLDS['ph_min'] or leitura['ph'] > THRESHOLDS['ph_max']
    n_baixo = leitura['nivel_N'] < THRESHOLDS['N_min']
    return umidade_critica or (n_baixo and ph_fora)


def verificar_alertas(leitura: dict) -> list:
    alertas = []

    if leitura['ph'] < THRESHOLDS['ph_min']:
        alertas.append({
            'tipo': 'pH Baixo',
            'valor': leitura['ph'],
            'threshold': THRESHOLDS['ph_min'],
            'acao': 'Aplicar calcário para elevar o pH',
        })
    elif leitura['ph'] > THRESHOLDS['ph_max']:
        alertas.append({
            'tipo': 'pH Alto',
            'valor': leitura['ph'],
            'threshold': THRESHOLDS['ph_max'],
            'acao': 'Aplicar enxofre para reduzir o pH',
        })

    if leitura['umidade'] < THRESHOLDS['umidade_min']:
        alertas.append({
            'tipo': 'Umidade Baixa',
            'valor': leitura['umidade'],
            'threshold': THRESHOLDS['umidade_min'],
            'acao': 'Iniciar irrigação imediatamente',
        })
    elif leitura['umidade'] > THRESHOLDS['umidade_max']:
        alertas.append({
            'tipo': 'Umidade Alta',
            'valor': leitura['umidade'],
            'threshold': THRESHOLDS['umidade_max'],
            'acao': 'Verificar drenagem do solo',
        })

    if leitura['nivel_N'] < THRESHOLDS['N_min']:
        alertas.append({
            'tipo': 'Nitrogênio Baixo',
            'valor': leitura['nivel_N'],
            'threshold': THRESHOLDS['N_min'],
            'acao': 'Aplicar fertilizante nitrogenado',
        })

    if leitura['temperatura'] > THRESHOLDS['temp_max']:
        alertas.append({
            'tipo': 'Temperatura Alta',
            'valor': leitura['temperatura'],
            'threshold': THRESHOLDS['temp_max'],
            'acao': 'Aumentar frequência de irrigação e monitorar estresse hídrico',
        })

    return alertas


def gerar_historico(n: int = 50, horas_atras: int = 24) -> pd.DataFrame:
    agora = datetime.now()
    intervalo = timedelta(hours=horas_atras) / n
    registros = []
    for i in range(n):
        ts = agora - timedelta(hours=horas_atras) + intervalo * i
        leitura = gerar_leitura_sensor(seed=i)
        leitura['timestamp'] = ts
        registros.append(leitura)

    df = pd.DataFrame(registros)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    return df
