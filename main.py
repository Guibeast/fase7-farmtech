#!/usr/bin/env python
"""
FarmTech Solutions — Fase 7
Disparo dos serviços por terminal (alternativa ao dashboard Streamlit).

Uso:
    python main.py             # menu interativo
    python main.py <serviço>   # dispara um serviço direto

Serviços: culturas | sensor | banco | ml | clima | visao | alerta | dashboard
"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'src'))

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

import fase1_clima as fclima
import fase1_culturas as f1
import fase2_iot as f2
import fase3_banco as f3


def _titulo(txt):
    print(f"\n{'=' * 60}\n  {txt}\n{'=' * 60}")


def servico_culturas():
    _titulo("FASE 1 — Culturas cadastradas")
    culturas = f1.get_culturas()
    if not culturas:
        print("Nenhuma cultura cadastrada.")
    for c in culturas:
        print(f"  #{c['id']} {c['tipo_cultura']:6} {c['forma_area']:10} "
              f"{c['area_calculada_m2']:>10.2f} m²")
    print(f"\nTotal: {len(culturas)} cultura(s).")


def servico_sensor():
    _titulo("FASE 2 — Leitura da estação ESP32 (simulada)")
    leitura = f2.gerar_leitura_sensor()
    print(f"  Umidade do solo : {leitura['umidade']:.1f}%")
    print(f"  Temperatura     : {leitura['temperatura']:.1f}°C")
    print(f"  pH              : {leitura['ph']:.2f}")
    print(f"  Nitrogênio (N)  : {leitura['nivel_N']:.0f} ppm")
    print(f"  Bomba de irrig. : {'LIGADA' if leitura['bomba_ativa'] else 'desligada'}")

    alertas = f2.verificar_alertas(leitura)
    if alertas:
        print("\n  Alertas:")
        for a in alertas:
            print(f"   - {a['tipo']} ({a['valor']}) → {a['acao']}")
    else:
        print("\n  Sensores dentro dos limites normais.")
    return leitura


def servico_banco():
    _titulo("FASE 3 — Banco de dados (SQLite)")
    f3.init_db()
    leitura = f2.gerar_leitura_sensor()
    f3.inserir_leitura(leitura)
    print("Leitura simulada gravada em LEITURAS_SENSOR.")

    stats = f3.estatisticas_sql()
    print(f"\n  Total de registros : {int(stats['total'])}")
    print(f"  Umidade média      : {stats['avg_umidade']:.1f}%")
    print(f"  pH (mín/máx)       : {stats['min_ph']:.2f} / {stats['max_ph']:.2f}")

    print("\n  Últimas leituras:")
    df = f3.consultar_ultimas(5)
    print(df.to_string(index=False) if not df.empty else "  (vazio)")


def servico_ml():
    _titulo("FASE 4/5 — Predição de produtividade (Random Forest)")
    import joblib
    import pandas as pd

    modelo = ROOT / 'models' / 'regressor_model.pkl'
    dados = ROOT / 'data' / 'dados_agricolas.csv'
    if not modelo.exists():
        print("Modelo não encontrado. Rode: python models/train_model.py")
        return

    model = joblib.load(modelo)
    cols = ['Umidade_Solo', 'pH_Solo', 'Temperatura_Ambiente',
            'Nivel_N', 'Historico_Irrigacao_mm']
    exemplo = pd.DataFrame([[55.0, 6.5, 25.0, 150.0, 20.0]], columns=cols)
    pred = model.predict(exemplo)[0]
    print("  Entrada: umidade=55%, pH=6.5, temp=25°C, N=150ppm, irrig=20mm/sem")
    print(f"  Produtividade prevista: {pred:.0f} kg/ha")

    if dados.exists():
        from sklearn.metrics import mean_absolute_error, r2_score
        df = pd.read_csv(dados)
        y_pred = model.predict(df[cols])
        print(f"  R² = {r2_score(df['Produtividade_Esperada'], y_pred):.4f} | "
              f"MAE = {mean_absolute_error(df['Produtividade_Esperada'], y_pred):.1f} kg/ha")


def servico_clima():
    _titulo("FASE 1 — Clima & irrigação (Open-Meteo)")
    for i, cidade in enumerate(fclima.CIDADES, 1):
        print(f"  {i}. {cidade}")
    escolha = input("Escolha a cidade (Enter = 1): ").strip() or "1"
    try:
        cidade = list(fclima.CIDADES)[int(escolha) - 1]
    except (ValueError, IndexError):
        cidade = list(fclima.CIDADES)[0]

    lat, lon = fclima.CIDADES[cidade]
    clima = fclima.obter_previsao(lat, lon)
    if clima.get('erro'):
        print(clima['erro'])
        return

    print(f"\n  {cidade}")
    print(f"  Temperatura    : {clima['temperatura'] or 0:.1f}°C")
    print(f"  Umidade do ar  : {clima['umidade_ar'] or 0:.0f}%")
    print(f"  Chuva agora    : {clima['chuva_agora'] or 0:.1f} mm")

    leitura = f2.gerar_leitura_sensor()
    _, msg = fclima.recomendar_irrigacao(clima, leitura['umidade'])
    print(f"\n  Recomendação (umidade do solo {leitura['umidade']:.0f}%): {msg}")


def servico_visao():
    _titulo("FASE 6 — Visão computacional (YOLOv8-cls)")
    import fase6_visao as f6

    base = ROOT / 'data' / 'fase6_cafe' / 'test'
    if not base.exists():
        base = ROOT / 'data' / 'fase6_amostras'
    amostras = sorted(base.glob("**/*.jpg")) + sorted(base.glob("**/*.png"))
    if not amostras:
        print("Nenhuma imagem de exemplo encontrada.")
        return

    img = amostras[0]
    print(f"  Analisando: {img.parent.name}/{img.name}")
    try:
        r = f6.analisar_imagem(img.read_bytes())
    except FileNotFoundError as e:
        print(f"  {e}")
        return

    print(f"\n  Diagnóstico : {r['status']}")
    print(f"  Confiança   : {r['confianca'] * 100:.1f}%")
    print(f"  Ação        : {r['acao_recomendada']}")


def servico_alerta():
    _titulo("FASE 5 — Alerta AWS SNS")
    import aws_alertas as aws
    leitura = f2.gerar_leitura_sensor()
    ok, msg = aws.enviar_alerta(
        "TESTE VIA TERMINAL",
        f"pH={leitura['ph']:.2f}, Umidade={leitura['umidade']:.1f}%",
        "Verificar condições da lavoura",
    )
    print(f"  {'OK' if ok else 'FALHA'}: {msg}")
    if not ok:
        print("  (Configure .streamlit/secrets.toml com as credenciais do Learner Lab.)")


def servico_dashboard():
    _titulo("Abrindo o dashboard Streamlit")
    subprocess.run([sys.executable, "-m", "streamlit", "run", str(ROOT / "dashboard.py")])


SERVICOS = {
    '1': ("Culturas (Fase 1)",          servico_culturas),
    '2': ("Sensor ESP32 (Fase 2)",      servico_sensor),
    '3': ("Banco de dados (Fase 3)",    servico_banco),
    '4': ("Machine Learning (Fase 4/5)", servico_ml),
    '5': ("Clima & irrigação (Fase 1)", servico_clima),
    '6': ("Visão computacional (Fase 6)", servico_visao),
    '7': ("Alerta AWS SNS (Fase 5)",    servico_alerta),
    '8': ("Abrir dashboard Streamlit",  servico_dashboard),
}

ALIASES = {
    'culturas': '1', 'sensor': '2', 'banco': '3', 'ml': '4',
    'clima': '5', 'visao': '6', 'alerta': '7', 'dashboard': '8',
}


def menu():
    while True:
        _titulo("FarmTech Solutions — Fase 7 (terminal)")
        for k, (nome, _) in SERVICOS.items():
            print(f"  {k}. {nome}")
        print("  0. Sair")
        escolha = input("\nServiço: ").strip()
        if escolha == '0':
            break
        item = SERVICOS.get(escolha)
        if item:
            item[1]()
        else:
            print("Opção inválida.")


if __name__ == '__main__':
    if len(sys.argv) > 1:
        chave = ALIASES.get(sys.argv[1].lower(), sys.argv[1])
        item = SERVICOS.get(chave)
        if item:
            item[1]()
        else:
            print(f"Serviço desconhecido: {sys.argv[1]}")
            print(f"Disponíveis: {', '.join(ALIASES)}")
            sys.exit(1)
    else:
        menu()
