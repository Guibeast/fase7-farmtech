from datetime import datetime

import boto3
import streamlit as st


def _get_client():
    try:
        return boto3.client(
            'sns',
            aws_access_key_id=st.secrets['AWS_ACCESS_KEY_ID'],
            aws_secret_access_key=st.secrets['AWS_SECRET_ACCESS_KEY'],
            aws_session_token=st.secrets.get('AWS_SESSION_TOKEN'),
            region_name=st.secrets.get('AWS_REGION', 'us-east-1'),
        )
    except KeyError:
        return None


def enviar_alerta(tipo_alerta: str, leitura_resumo: str, acao: str) -> tuple:
    client = _get_client()
    if client is None:
        return False, "Credenciais AWS não configuradas"

    agora = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    mensagem = (
        f"[FARMTECH AI4SUCCESS] ALERTA: {tipo_alerta}\n"
        f"Leitura: {leitura_resumo}\n"
        f"Ação: {acao}\n"
        f"Timestamp: {agora}\n"
        f"Sistema: FarmTech Solutions - Grupo AI4Success"
    )

    try:
        topic_arn = st.secrets['SNS_TOPIC_ARN']
        client.publish(
            TopicArn=topic_arn,
            Message=mensagem,
            Subject=f"FarmTech Alerta: {tipo_alerta}",
        )
        return True, "Alerta enviado!"
    except KeyError:
        return False, "Credenciais AWS não configuradas"
    except Exception as e:
        return False, f"Erro: {e}"


def testar_conexao() -> tuple:
    client = _get_client()
    if client is None:
        return False, "Credenciais AWS não configuradas"
    try:
        client.list_topics()
        return True, "Conexão AWS SNS estabelecida com sucesso"
    except Exception as e:
        return False, f"Falha na conexão: {e}"
