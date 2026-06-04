import json
import math
from pathlib import Path

JSON_PATH = Path(__file__).resolve().parent.parent / 'data' / 'farmtech_dados.json'


def get_culturas() -> list:
    if not JSON_PATH.exists():
        return []
    with open(JSON_PATH, 'r', encoding='utf-8') as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []


def salvar_culturas(culturas: list):
    JSON_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(JSON_PATH, 'w', encoding='utf-8') as f:
        json.dump(culturas, f, ensure_ascii=False, indent=2)


def calcular_area(forma: str, dimensoes: dict) -> float:
    if forma == 'retangulo':
        return dimensoes['comprimento'] * dimensoes['largura']
    if forma == 'circulo':
        return math.pi * dimensoes['raio'] ** 2
    raise ValueError(f"Forma desconhecida: {forma}")


def adicionar_cultura(tipo: str, forma: str, dimensoes: dict, insumos: list) -> dict:
    culturas = get_culturas()
    novo_id = max((c['id'] for c in culturas), default=0) + 1
    cultura = {
        'id': novo_id,
        'tipo_cultura': tipo,
        'forma_area': forma,
        'dimensoes': dimensoes,
        'area_calculada_m2': round(calcular_area(forma, dimensoes), 2),
        'insumos': insumos,
    }
    culturas.append(cultura)
    salvar_culturas(culturas)
    return cultura


def deletar_cultura(id_cultura: int) -> bool:
    culturas = get_culturas()
    novas = [c for c in culturas if c['id'] != id_cultura]
    if len(novas) == len(culturas):
        return False
    salvar_culturas(novas)
    return True
