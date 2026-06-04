# models/train_model.py
import pandas as pd
import joblib
import numpy as np
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

# --- CONFIGURAÇÃO DE CAMINHOS ---
CAMINHO_RAIZ = Path(__file__).resolve().parent.parent
ARQUIVO_DADOS = CAMINHO_RAIZ / 'data' / 'dados_agricolas.csv'
CAMINHO_MODELO = CAMINHO_RAIZ / 'models' / 'regressor_model.pkl'

# 1. Carregar Dados
try:
    df = pd.read_csv(ARQUIVO_DADOS)
except FileNotFoundError:
    print("ERRO: Arquivo csv não encontrado. Execute 'python models/gerar_dados.py'")
    exit()

features = ['Umidade_Solo', 'pH_Solo', 'Temperatura_Ambiente', 'Nivel_N', 'Historico_Irrigacao_mm']
X = df[features]
y = df['Produtividade_Esperada']

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

model = RandomForestRegressor(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

y_pred = model.predict(X_test)
mae = mean_absolute_error(y_test, y_pred)
mse = mean_squared_error(y_test, y_pred)
rmse = np.sqrt(mse)
r2 = r2_score(y_test, y_pred)

print("--- MÉTRICAS DO MODELO ---")
print(f"R2:   {r2:.4f}")
print(f"MAE:  {mae:.2f}")

joblib.dump(model, CAMINHO_MODELO)
print(f"✅ Modelo salvo em: {CAMINHO_MODELO}")