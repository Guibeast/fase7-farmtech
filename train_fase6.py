"""
Treino da Fase 6 — classificacao de saude da folha de cafe (YOLOv8-cls).

Pipeline completo:
  1. Baixa o dataset publico brainer-fp66/coffee-leaf-diseases (Hugging Face).
  2. Organiza no formato ImageFolder que o YOLOv8-cls espera (train/val/test).
  3. Treina via transfer learning a partir do yolov8n-cls.pt.
  4. Copia o melhor peso para models/fase6_cafe.pt.
  5. Salva metricas reais (results.png, confusion_matrix.png) em models/fase6_metrics/.

Uso:
    python train_fase6.py                 # 30 epocas, imgsz 224
    python train_fase6.py --epochs 60     # mais epocas
    python train_fase6.py --skip-download # reaproveita dataset ja baixado

Requer GPU NVIDIA para treino rapido (cai para CPU automaticamente se nao houver).
"""
import argparse
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / 'data' / 'fase6_cafe'
MODELS_DIR = ROOT / 'models'
HF_DATASET = 'brainer-fp66/coffee-leaf-diseases'


def preparar_dataset() -> None:
    from datasets import load_dataset

    if (DATA_DIR / 'train').exists() and any((DATA_DIR / 'train').rglob('*.jpg')):
        print(f"Dataset ja preparado em {DATA_DIR}, pulando download.")
        return

    print(f"Baixando {HF_DATASET} do Hugging Face...")
    ds = load_dataset(HF_DATASET)
    classes = ds['train'].features['label'].names

    split_map = {'train': 'train', 'validation': 'val', 'test': 'test'}
    for hf_split, yolo_split in split_map.items():
        if hf_split not in ds:
            continue
        for nome in classes:
            (DATA_DIR / yolo_split / nome.replace(' ', '_')).mkdir(parents=True, exist_ok=True)

        print(f"  Exportando split '{hf_split}' -> '{yolo_split}' ({len(ds[hf_split])} imgs)...")
        for i, ex in enumerate(ds[hf_split]):
            nome = classes[ex['label']].replace(' ', '_')
            ex['image'].convert('RGB').save(DATA_DIR / yolo_split / nome / f"{yolo_split}_{i:05d}.jpg")

    print(f"Dataset pronto em {DATA_DIR} — classes: {classes}")


def treinar(epochs: int, imgsz: int) -> None:
    from ultralytics import YOLO

    model = YOLO('yolov8n-cls.pt')
    resultados = model.train(
        data=str(DATA_DIR),
        epochs=epochs,
        imgsz=imgsz,
        project=str(MODELS_DIR / 'fase6_runs'),
        name='cafe',
        exist_ok=True,
    )

    run_dir = Path(model.trainer.save_dir)
    best = run_dir / 'weights' / 'best.pt'
    shutil.copy(best, MODELS_DIR / 'fase6_cafe.pt')

    metrics_dir = MODELS_DIR / 'fase6_metrics'
    metrics_dir.mkdir(parents=True, exist_ok=True)
    for nome in ('results.png', 'confusion_matrix.png', 'confusion_matrix_normalized.png'):
        origem = run_dir / nome
        if origem.exists():
            shutil.copy(origem, metrics_dir / nome)

    print("\n=== TREINO CONCLUIDO ===")
    print(f"Modelo:   {MODELS_DIR / 'fase6_cafe.pt'}")
    print(f"Metricas: {metrics_dir}")
    top1 = getattr(resultados, 'top1', None)
    if top1 is None:
        top1 = model.trainer.metrics.get('metrics/accuracy_top1', float('nan'))
    print(f"Acuracia top-1 (val): {top1:.4f}")


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument('--epochs', type=int, default=30)
    p.add_argument('--imgsz', type=int, default=224)
    p.add_argument('--skip-download', action='store_true')
    args = p.parse_args()

    if not args.skip_download:
        preparar_dataset()
    treinar(args.epochs, args.imgsz)


if __name__ == '__main__':
    main()
