import streamlit as st
import google.generativeai as genai
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta

# --- KONFIGURASI HALAMAN ---
st.set_page_config(page_title="Gemini Stock Analyzer", layout="wide", page_icon="📈")

# Custom CSS untuk mempercantik tampilan
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stButton>button { width: 100%; border-radius: 5px; height: 3em; background-color: #007bff; color: white; }
    .reportview-container .main .block-container { padding-top: 2rem; }
    </style>
    """, unsafe_allow_html=True)

# --- SIDEBAR ---
with st.sidebar:
    st.title("⚙️ Konfigurasi")
    api_key = st.text_input("Gemini API Key:", type="password", help="Dapatkan di Google AI Studio")
    
    st.divider()
    
    st.header("Strategi Analisis")
    mode = st.selectbox(
        "Pilih Gaya Investasi:",
        ["Agresif (Breakout & Momentum)", "Konservatif (Bluechip & Value)", "Jangka Panjang (Growth)"]
    )
    
    st.info("""
    **Tips:** - Gunakan kode saham dengan akhiran **.JK** untuk IHSG (Contoh: BBCA.JK, MBMA.JK).
    - Pastikan API Key valid untuk menggunakan model Gemini 3.
    """)

# --- LOGIKA SISTEM ANALISIS ---
def get_system_prompt(mode, ticker):
    if mode == "Agresif (Breakout & Momentum)":
        return f"""Anda adalah Day Trader & Swing Trader ahli. Fokus pada konfirmasi 'Breakout' saham {ticker}.
        Gunakan indikator volume, candlestick pattern, dan kekuatan trend. 
        Waspadai 'False Breakout'. Berikan instruksi Entry, TP, dan SL yang ketat."""
    
    elif mode == "Konservatif (Bluechip & Value)":
        return f"""Anda adalah Value Investor ala Warren Buffett. Fokus pada fundamental saham {ticker}.
        Analisis rasio P/E, PBV, Dividen, dan Margin of Safety. 
        Berikan opini apakah harga saat ini sudah 'Undervalued' atau 'Overvalued'."""
    
    else:
        return f"""Anda adalah Growth Investor. Fokus pada prospek masa depan saham {ticker}.
        Lihat pertumbuhan pendapatan (Revenue Growth) dan potensi market share di masa depan."""

# --- UI UTAMA ---
st.title("📈 Gemini 3 Stock Analyzer")
st.subheader("Analisis Teknikal & Fundamental Berbasis AI")

col_input, col_empty = st.columns([2, 2])
with col_input:
    ticker_input = st.text_input("Masukkan Kode Saham (Tanpa .JK):", value="BBCA").upper()
    full_ticker = f"{ticker_input}.JK"

if st.button("Mulai Analisis"):
    if not api_key:
        st.error("❌ Mohon masukkan Gemini API Key di sidebar!")
    else:
        try:
            # 1. Inisialisasi Gemini 3
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-1.5-flash') # Gunakan gemini-1.5-flash atau gemini-2.0-flash-exp jika tersedia

            with st.spinner(f"Mengambil data {ticker_input}..."):
                # 2. Ambil Data dari Yahoo Finance
                stock = yf.Ticker(full_ticker)
                hist = stock.history(period="6mo") # Data 6 bulan terakhir
                info = stock.info
                
                if hist.empty:
                    st.error("⚠️ Data tidak ditemukan. Periksa kembali kode sahamnya.")
                else:
                    # Tampilkan Harga Real-time
                    current_price = hist['Close'].iloc[-1]
                    prev_close = hist['Close'].iloc[-2]
                    pct_change = ((current_price - prev_close) / prev_close) * 100
                    
                    c1, c2, c3, c4 = st.columns(4)
                    c1.metric("Harga Terakhir", f"Rp {current_price:,.0f}", f"{pct_change:.2f}%")
                    c2.metric("P/E Ratio", f"{info.get('trailingPE', 'N/A')}")
                    c3.metric("PBV Ratio", f"{info.get('priceToBook', 'N/A')}")
                    c4.metric("Volume", f"{hist['Volume'].iloc[-1]:,.0f}")

                    # 3. Grafik Candlestick
                    fig = go.Figure(data=[go.Candlestick(
                        x=hist.index,
                        open=hist['Open'], high=hist['High'],
                        low=hist['Low'], close=hist['Close'],
                        name="Harga"
                    )])
                    fig.update_layout(title=f"Chart Harga {ticker_input}", xaxis_rangeslider_visible=False, template="plotly_white")
                    st.plotly_chart(fig, use_container_width=True)

                    # 4. Analisis AI
                    st.divider()
                    st.subheader("🤖 Hasil Analisis Gemini AI")
                    
                    # Siapkan Data untuk AI
                    resistance = hist['High'].iloc[-20:].max()
                    support = hist['Low'].iloc[-20:].min()
                    
                    data_summary = f"""
                    Saham: {ticker_input}
                    Harga Sekarang: {current_price}
                    Resistance (20 Hari): {resistance}
                    Support (20 Hari): {support}
                    P/E: {info.get('trailingPE')}
                    PBV: {info.get('priceToBook')}
                    Market Cap: {info.get('marketCap')}
                    """
                    
                    system_instruction = get_system_prompt(mode, ticker_input)
                    full_prompt = f"{system_instruction}\n\nBerikut data terbarunya:\n{data_summary}\n\nBerikan analisis mendalam dan trading plan."

                    response = model.generate_content(full_prompt)
                    st.markdown(response.text)

        except Exception as e:
            st.error(f"Terjadi kesalahan teknis: {e}")

st.divider()

st.caption("Aplikasi ini dibuat untuk tujuan edukasi. Keputusan investasi ada di tangan Anda sendiri (DYOR).")
