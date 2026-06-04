# models/gerar_dados.py
import pandas as pd
import numpy as np
from pathlib import Path

# --- CONFIGURAÇÃO DE CAMINHOS ---
# Pega a pasta onde este script está (models), sobe um nível (raiz)
CAMINHO_RAIZ = Path(__file__).resolve().parent.parent
ARQUIVO_SAIDA = CAMINHO_RAIZ / 'data' / 'dados_agricolas.csv'

# Cria a pasta data se não existir
(CAMINHO_RAIZ / 'data').mkdir(parents=True, exist_ok=True)

# Definição do número de amostras
N_AMOSTRAS = 1000
np.random.seed(42)

# --- GERAÇÃO DOS DADOS (Mantendo a lógica de alto R2) ---
data = {
    'ID_Talhao': np.random.randint(1, 11, N_AMOSTRAS),
    'Umidade_Solo': np.random.uniform(30.0, 90.0, N_AMOSTRAS),
    'pH_Solo': np.random.uniform(4.0, 9.0, N_AMOSTRAS),
    'Temperatura_Ambiente': np.random.uniform(15.0, 40.0, N_AMOSTRAS),
    'Nivel_N': np.random.uniform(30.0, 300.0, N_AMOSTRAS),
    'Historico_Irrigacao_mm': np.random.uniform(0.0, 70.0, N_AMOSTRAS),
}
df = pd.DataFrame(data)

# Lógica de Produtividade
ideal_moisture_min, ideal_moisture_max = 50.0, 70.0
ideal_ph_min, ideal_ph_max = 6.0, 7.0
ideal_temp_min, ideal_temp_max = 20.0, 30.0
produtividade_base = 2500

umidade_score = np.where((df['Umidade_Solo'] >= ideal_moisture_min) & (df['Umidade_Solo'] <= ideal_moisture_max), 1, (1 - np.abs(df['Umidade_Solo'] - (ideal_moisture_min + ideal_moisture_max) / 2) / (ideal_moisture_max - ideal_moisture_min) * 0.5).clip(0, 1))
ph_score = np.where((df['pH_Solo'] >= ideal_ph_min) & (df['pH_Solo'] <= ideal_ph_max), 1, (1 - np.abs(df['pH_Solo'] - (ideal_ph_min + ideal_ph_max) / 2) / (ideal_ph_max - ideal_ph_min) * 0.5).clip(0, 1))
temp_score = np.where((df['Temperatura_Ambiente'] >= ideal_temp_min) & (df['Temperatura_Ambiente'] <= ideal_temp_max), 1, (1 - np.abs(df['Temperatura_Ambiente'] - (ideal_temp_min + ideal_temp_max) / 2) / (ideal_temp_max - ideal_temp_min) * 0.5).clip(0, 1))

produtividade_influencia = (umidade_score * 3000 + ph_score * 2000 + temp_score * 500 + df['Nivel_N'] * 10 + df['Historico_Irrigacao_mm'] * 20)
ruido = np.random.normal(0, 150, N_AMOSTRAS)
produtividade = produtividade_base + produtividade_influencia + ruido
df['Produtividade_Esperada'] = produtividade.clip(lower=1000, upper=10000).round(2)

# Salvando
df.to_csv(ARQUIVO_SAIDA, index=False)
print(f"✅ Arquivo gerado em: {ARQUIVO_SAIDA}")