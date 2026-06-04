"""
Fase 1 — integração com API meteorológica (Open-Meteo).

Open-Meteo é gratuita e não exige chave de API. Usada para cruzar a previsão
de chuva com a umidade do solo (Fase 2) e recomendar irrigação.
"""
import requests

ENDPOINT = 'https://api.open-meteo.com/v1/forecast'

# Polos agrícolas brasileiros (café/soja) com coordenadas embutidas.
CIDADES = {
    'Ribeirão Preto - SP': (-21.1775, -47.8103),
    'Patrocínio - MG':     (-18.9436, -46.9925),
    'Sorriso - MT':        (-12.5450, -55.7211),
    'Londrina - PR':       (-23.3045, -51.1696),
}

# Solo abaixo deste valor é considerado seco (mesmo critério da bomba na Fase 2).
UMIDADE_SECO = 40.0
# Chuva acumulada (mm) a partir da qual vale a pena adiar a irrigação.
CHUVA_RELEVANTE = 5.0


def obter_previsao(lat: float, lon: float) -> dict:
    params = {
        'latitude': lat,
        'longitude': lon,
        'current': 'temperature_2m,relative_humidity_2m,precipitation',
        'daily': 'precipitation_sum,temperature_2m_max,temperature_2m_min',
        'timezone': 'auto',
        'forecast_days': 3,
    }
    try:
        resp = requests.get(ENDPOINT, params=params, timeout=10)
        resp.raise_for_status()
        dados = resp.json()
    except requests.RequestException as e:
        return {'erro': f"Não foi possível consultar a previsão: {e}"}

    atual = dados.get('current', {})
    diario = dados.get('daily', {})
    return {
        'temperatura':       atual.get('temperature_2m'),
        'umidade_ar':        atual.get('relative_humidity_2m'),
        'chuva_agora':       atual.get('precipitation'),
        'datas':             diario.get('time', []),
        'chuva_prevista':    diario.get('precipitation_sum', []),
        'temp_max':          diario.get('temperature_2m_max', []),
        'temp_min':          diario.get('temperature_2m_min', []),
    }


def recomendar_irrigacao(previsao: dict, umidade_solo: float) -> tuple:
    """Retorna (nivel, mensagem). nivel: 'ok' | 'irrigar' | 'adiar'."""
    chuva = previsao.get('chuva_prevista') or []
    chuva_48h = sum(chuva[:2])

    if chuva_48h >= CHUVA_RELEVANTE:
        return ('adiar',
                f"Chuva prevista de {chuva_48h:.1f} mm nas próximas 48h — adiar irrigação e economizar água.")
    if umidade_solo < UMIDADE_SECO:
        return ('irrigar',
                f"Solo seco ({umidade_solo:.0f}%) e sem chuva relevante prevista — iniciar irrigação.")
    return ('ok',
            "Umidade do solo adequada e sem chuva forte prevista — manter o manejo atual.")
