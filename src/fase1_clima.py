"""
Fase 1 — integração com API meteorológica (Open-Meteo).

Open-Meteo é gratuita e não exige chave de API. Usada para cruzar a previsão
de chuva e a evapotranspiração (ET0) com a umidade do solo (Fase 2) e
recomendar irrigação por balanço hídrico.
"""
import requests

ENDPOINT = 'https://api.open-meteo.com/v1/forecast'

# Polos agrícolas brasileiros (café/soja/milho/algodão/fruticultura) com coordenadas.
CIDADES = {
    'Ribeirão Preto - SP':            (-21.1775, -47.8103),
    'Franca - SP':                    (-20.5386, -47.4008),
    'Patrocínio - MG':                (-18.9436, -46.9925),
    'Guaxupé - MG':                   (-21.3050, -46.7128),
    'Uberlândia - MG':                (-18.9186, -48.2772),
    'Londrina - PR':                  (-23.3045, -51.1696),
    'Maringá - PR':                   (-23.4253, -51.9386),
    'Cascavel - PR':                  (-24.9555, -53.4552),
    'Passo Fundo - RS':               (-28.2576, -52.4091),
    'Chapecó - SC':                   (-27.1004, -52.6152),
    'Sorriso - MT':                   (-12.5450, -55.7211),
    'Sinop - MT':                     (-11.8642, -55.5025),
    'Campo Verde - MT':               (-15.5453, -55.1628),
    'Rio Verde - GO':                 (-17.7973, -50.9189),
    'Dourados - MS':                  (-22.2231, -54.8120),
    'Barreiras - BA':                 (-12.1528, -44.9900),
    'Luís Eduardo Magalhães - BA':    (-12.0917, -45.7975),
    'Petrolina - PE':                 (-9.3891, -40.5030),
}

# Solo abaixo deste valor é considerado seco (mesmo critério da bomba na Fase 2).
UMIDADE_SECO = 40.0
# Chuva acumulada (mm) a partir da qual vale a pena adiar a irrigação.
CHUVA_RELEVANTE = 5.0

# Códigos WMO (weather_code) -> (emoji, descrição PT).
WMO = {
    0:  ('☀️', 'Céu limpo'),
    1:  ('🌤️', 'Predominantemente limpo'),
    2:  ('⛅', 'Parcialmente nublado'),
    3:  ('☁️', 'Nublado'),
    45: ('🌫️', 'Névoa'),
    48: ('🌫️', 'Névoa com geada'),
    51: ('🌦️', 'Garoa fraca'),
    53: ('🌦️', 'Garoa moderada'),
    55: ('🌦️', 'Garoa intensa'),
    56: ('🌧️', 'Garoa congelante'),
    57: ('🌧️', 'Garoa congelante intensa'),
    61: ('🌧️', 'Chuva fraca'),
    63: ('🌧️', 'Chuva moderada'),
    65: ('🌧️', 'Chuva forte'),
    66: ('🌧️', 'Chuva congelante'),
    67: ('🌧️', 'Chuva congelante forte'),
    71: ('❄️', 'Neve fraca'),
    73: ('❄️', 'Neve moderada'),
    75: ('❄️', 'Neve forte'),
    77: ('❄️', 'Grãos de neve'),
    80: ('🌦️', 'Pancadas de chuva fracas'),
    81: ('🌦️', 'Pancadas de chuva'),
    82: ('⛈️', 'Pancadas de chuva fortes'),
    85: ('🌨️', 'Pancadas de neve'),
    86: ('🌨️', 'Pancadas de neve fortes'),
    95: ('⛈️', 'Trovoada'),
    96: ('⛈️', 'Trovoada com granizo'),
    99: ('⛈️', 'Trovoada com granizo forte'),
}


def descrever_tempo(codigo) -> tuple:
    """Retorna (emoji, descrição) para um código WMO."""
    if codigo is None:
        return ('❓', 'Indisponível')
    return WMO.get(int(codigo), ('🌡️', 'Condição desconhecida'))


def obter_previsao(lat: float, lon: float) -> dict:
    params = {
        'latitude': lat,
        'longitude': lon,
        'current': ','.join([
            'temperature_2m', 'apparent_temperature', 'relative_humidity_2m',
            'precipitation', 'weather_code', 'wind_speed_10m',
            'wind_direction_10m', 'soil_moisture_0_to_1cm', 'soil_temperature_0cm',
        ]),
        'daily': ','.join([
            'weather_code', 'temperature_2m_max', 'temperature_2m_min',
            'precipitation_sum', 'precipitation_probability_max',
            'et0_fao_evapotranspiration', 'wind_speed_10m_max', 'uv_index_max',
        ]),
        'timezone': 'auto',
        'forecast_days': 7,
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
        'temperatura':        atual.get('temperature_2m'),
        'sensacao':           atual.get('apparent_temperature'),
        'umidade_ar':         atual.get('relative_humidity_2m'),
        'chuva_agora':        atual.get('precipitation'),
        'codigo_tempo':       atual.get('weather_code'),
        'vento':              atual.get('wind_speed_10m'),
        'vento_dir':          atual.get('wind_direction_10m'),
        'umidade_solo_api':   atual.get('soil_moisture_0_to_1cm'),
        'temp_solo':          atual.get('soil_temperature_0cm'),
        'datas':              diario.get('time', []),
        'codigos_dia':        diario.get('weather_code', []),
        'chuva_prevista':     diario.get('precipitation_sum', []),
        'chuva_prob':         diario.get('precipitation_probability_max', []),
        'temp_max':           diario.get('temperature_2m_max', []),
        'temp_min':           diario.get('temperature_2m_min', []),
        'et0':                diario.get('et0_fao_evapotranspiration', []),
        'vento_max':          diario.get('wind_speed_10m_max', []),
        'uv_max':             diario.get('uv_index_max', []),
    }


def recomendar_irrigacao(previsao: dict, umidade_solo: float) -> tuple:
    """Retorna (nivel, mensagem) por balanço hídrico simples.

    nivel: 'ok' | 'irrigar' | 'adiar'. Compara a chuva prevista para 48h com a
    demanda de evapotranspiração (ET0) do mesmo período.
    """
    chuva = previsao.get('chuva_prevista') or []
    et0 = previsao.get('et0') or []
    chuva_48h = sum(chuva[:2])
    demanda_48h = sum(et0[:2]) if et0 else 0.0
    saldo = chuva_48h - demanda_48h

    if chuva_48h >= CHUVA_RELEVANTE and saldo >= 0:
        return ('adiar',
                f"Chuva prevista de {chuva_48h:.1f} mm nas próximas 48h supera a "
                f"demanda hídrica (ET0 {demanda_48h:.1f} mm) — adiar irrigação e economizar água.")
    if umidade_solo < UMIDADE_SECO:
        return ('irrigar',
                f"Solo seco ({umidade_solo:.0f}%), chuva de apenas {chuva_48h:.1f} mm "
                f"e demanda de ET0 {demanda_48h:.1f} mm em 48h — iniciar irrigação.")
    return ('ok',
            f"Umidade do solo adequada ({umidade_solo:.0f}%); chuva {chuva_48h:.1f} mm "
            f"vs ET0 {demanda_48h:.1f} mm em 48h — manter o manejo atual.")
