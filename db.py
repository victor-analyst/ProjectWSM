"""
db.py — engine compartilhado e cacheado entre todos os módulos.
Usar @st.cache_resource garante que a conexão seja criada UMA VEZ
por sessão do servidor, eliminando o overhead de reconectar ao banco
a cada troca de aba.
"""

import streamlit as st
from sqlalchemy import create_engine


_SERVER   = r"18.229.240.86\DW_SALOG,1004"
_USERNAME = "DW_SALOG"
_PASSWORD = "pr4RFGTG0Ovtt567"
_DATABASE = "db_visual_SALOG"


@st.cache_resource(show_spinner=False)
def get_engine():
    """Retorna o engine SQLAlchemy cacheado (criado apenas uma vez)."""
    conn_str = (
        f"mssql+pyodbc://{_USERNAME}:{_PASSWORD}@{_SERVER}/{_DATABASE}"
        f"?driver=ODBC+Driver+18+for+SQL+Server&TrustServerCertificate=yes"
    )
    return create_engine(
        conn_str,
        # Pool otimizado: mantém conexões abertas e reutiliza-as
        pool_size=5,
        max_overflow=10,
        pool_pre_ping=True,   # valida conexão antes de usar (evita erros de timeout)
        pool_recycle=1800,    # recicla conexões a cada 30min (evita drops do servidor)
        connect_args={"timeout": 15},
    )
