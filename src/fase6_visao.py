import io
from pathlib import Path

from PIL import Image

MODELO_PATH = Path(__file__).resolve().parent.parent / 'models' / 'fase6_cafe.pt'

# classe do modelo (nome da pasta) -> rotulo PT, cor do card e acao agronomica
CLASSES = {
    'Healthy': (
        'Folha saudável', 'green',
        'Manter manejo atual. Continuar monitoramento preventivo.',
    ),
    'Rust': (
        'Ferrugem (Hemileia vastatrix)', 'red',
        'Isolar área afetada. Aplicar fungicida cúprico ou triazol. Principal doença do cafeeiro.',
    ),
    'Miner': (
        'Bicho-mineiro (Leucoptera coffeella)', 'red',
        'Monitorar infestação. Aplicar inseticida específico ou controle biológico com vespas predadoras.',
    ),
    'Phoma': (
        'Mancha de Phoma', 'red',
        'Podar ramos afetados. Aplicar fungicida. Comum em períodos frios e ventosos.',
    ),
    'Red_Spider_Mite': (
        'Ácaro-vermelho (Oligonychus ilicis)', 'orange',
        'Aplicar acaricida. Favorecido por seca e poeira — avaliar irrigação e quebra-ventos.',
    ),
}

_modelo = None


def _get_modelo():
    global _modelo
    if _modelo is None:
        if not MODELO_PATH.exists():
            raise FileNotFoundError(
                f"Modelo nao encontrado em {MODELO_PATH}. "
                "Rode 'python train_fase6.py' para treinar a Fase 6."
            )
        from ultralytics import YOLO
        _modelo = YOLO(str(MODELO_PATH))
    return _modelo


def analisar_imagem(img_bytes: bytes) -> dict:
    img = Image.open(io.BytesIO(img_bytes)).convert('RGB')
    res = _get_modelo().predict(img, verbose=False)[0]

    nomes = res.names
    probs = res.probs
    idx_top = int(probs.top1)
    classe = nomes[idx_top]

    rotulo, cor, acao = CLASSES.get(
        classe, (classe, 'gray', 'Classe não mapeada. Avaliar manualmente.')
    )

    probabilidades = {
        CLASSES.get(nomes[i], (nomes[i],))[0]: float(p)
        for i, p in enumerate(probs.data.tolist())
    }

    return {
        'status':           rotulo,
        'classe':           classe,
        'cor_card':         cor,
        'confianca':        float(probs.top1conf),
        'acao_recomendada': acao,
        'probabilidades':   probabilidades,
        'saudavel':         classe == 'Healthy',
    }
