import streamlit as st
import google.generativeai as genai
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

# --- KONFIGURASI HALAMAN ---
st.set_page_config(page_title="Gemini Stock Analyzer", layout="wide", page_icon="📈")

st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stButton>button { width: 100%; border-radius: 5px; height: 3em; background-color: #007bff; color: white; }
    </style>
    """, unsafe_allow_html=True)

# --- SIDEBAR ---
with st.sidebar:
    st.title("⚙️ Konfigurasi")
    api_key = st.text_input("Gemini API Key:", type="password")
    st.divider()
    mode = st.selectbox(
        "Pilih Gaya Investasi:",
        ["Agresif (Breakout & Bandarmology)", "Konservatif (Value Investing)", "Jangka Panjang (Growth)"]
    )

# --- LOGIKA PROMPT (Point 2: Analisis Bandarmology) ---
def get_system_prompt(mode, ticker):
    if mode == "Agresif (Breakout & Bandarmology)":
        return f"""Anda adalah ahli Bandarmology dan Price Action. Fokus pada saham {ticker}.
        Analisis apakah kenaikan harga didukung lonjakan volume (indikasi akumulasi bandar) atau volume rendah (false breakout).
        Berikan instruksi Entry, TP, dan SL yang ketat."""
    elif mode == "Konservatif (Value Investing)":
        return f"""Anda adalah Value Investor. Fokus pada fundamental {ticker}. 
        Analisis Margin of Safety dan rasio keuangan penting."""
    else:
        return f"""Anda adalah Growth Investor. Fokus pada masa depan {ticker}."""

# --- UI UTAMA ---
st.title("📈 Gemini 3 Stock Analyzer")
ticker_input = st.text_input("Masukkan Kode Saham (Tanpa .JK):", value="BBCA").upper()
full_ticker = f"{ticker_input}.JK"

if st.button("Mulai Analisis"):
    if not api_key:
        st.error("❌ Masukkan API Key!")
    else:
        try:
            genai.configure(api_key=api_key)
            # Menggunakan model yang menurutmu stabil
            model = genai.GenerativeModel("gemini-flash-latest")

            with st.spinner(f"Menganalisis {ticker_input}..."):
                stock = yf.Ticker(full_ticker)
                hist = stock.history(period="6mo")
                
                if hist.empty:
                    st.error("⚠️ Data tidak ditemukan.")
                else:
                    # Point 1: Tambah Indikator MA
                    hist['MA20'] = hist['Close'].rolling(window=20).mean()
                    hist['MA50'] = hist['Close'].rolling(window=50).mean()

                    # Grafik Candlestick + MA
                    fig = go.Figure(data=[
                        go.Candlestick(x=hist.index, open=hist['Open'], high=hist['High'], low=hist['Low'], close=hist['Close'], name="Price"),
                        go.Scatter(x=hist.index, y=hist['MA20'], line=dict(color='orange', width=1), name="MA20"),
                        go.Scatter(x=hist.index, y=hist['MA50'], line=dict(color='blue', width=1), name="MA50")
                    ])
                    st.plotly_chart(fig, use_container_width=True)

                    # Analisis AI
                    data_summary = f"Harga: {hist['Close'].iloc[-1]}, Vol: {hist['Volume'].iloc[-1]}, PBV: {stock.info.get('priceToBook')}"
                    response = model.generate_content(f"{get_system_prompt(mode, ticker_input)}\n\nData: {data_summary}")
                    
                    st.subheader("🤖 Analisis Gemini")
                    analysis_text = response.text
                    st.markdown(analysis_text)

                    # Point 3: Fitur Download
                    st.divider()
                    st.download_button(
                        label="📥 Download Hasil Analisis",
                        data=analysis_text,
                        file_name=f"Analisis_{ticker_input}_{datetime.now().strftime('%Y%m%d')}.txt",
                        mime="text/plain"
                    )

        except Exception as e:
            st.error(f"Kesalahan: {e}")
