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

def get_system_prompt(mode, ticker):
    if mode == "Agresif (Breakout & Bandarmology)":
        return f"Anda adalah ahli Bandarmology dan Price Action. Fokus pada saham {ticker}. Analisis volume dan breakout."
    elif mode == "Konservatif (Value Investing)":
        return f"Anda adalah Value Investor. Fokus pada fundamental {ticker}."
    else:
        return f"Anda adalah Growth Investor. Fokus pada masa depan {ticker}."

# --- UI UTAMA ---
st.title("📈 Gemini 3 Stock Analyzer")

# --- FITUR BARU: REKOMENDASI SAHAM HARI INI ---
if api_key:
    with st.expander("🚀 Cek Rekomendasi Saham Hari Ini"):
        if st.button("Generate Rekomendasi"):
            try:
                genai.configure(api_key=api_key)
                model = genai.GenerativeModel("gemini-flash-latest")
                
                # Daftar saham untuk dipindai
                watchlist = ["BBCA.JK", "ASII.JK", "TLKM.JK", "MBMA.JK", "BUMI.JK", "ERAA.JK"]
                scan_data = ""
                
                with st.spinner("Memindai pasar..."):
                    for t in watchlist:
                        s = yf.Ticker(t)
                        h = s.history(period="2d")
                        if not h.empty:
                            change = ((h['Close'].iloc[-1] - h['Close'].iloc[-2]) / h['Close'].iloc[-2]) * 100
                            scan_data += f"{t}: Harga {h['Close'].iloc[-1]:,.0f}, Perubahan {change:.2f}%\n"
                
                rekom_prompt = f"Berdasarkan data berikut, saham mana yang paling menarik untuk dipantau hari ini berdasarkan strategi {mode}?\n{scan_data}"
                res = model.generate_content(rekom_prompt)
                st.info(res.text)
            except Exception as e:
                st.error(f"Gagal memuat rekomendasi: {e}")
else:
    st.warning("Masukkan API Key di sidebar untuk melihat rekomendasi.")

st.divider()

# --- ANALISIS INDIVIDU ---
ticker_input = st.text_input("Masukkan Kode Saham untuk Analisis Detail (Tanpa .JK):", value="BBCA").upper()
full_ticker = f"{ticker_input}.JK"

if st.button("Mulai Analisis Detail"):
    if not api_key:
        st.error("❌ Masukkan API Key!")
    else:
        try:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel("gemini-flash-latest")

            with st.spinner(f"Menganalisis {ticker_input}..."):
                stock = yf.Ticker(full_ticker)
                hist = stock.history(period="6mo")
                
                if hist.empty:
                    st.error("⚠️ Data tidak ditemukan.")
                else:
                    # Metrik Harga Real-time
                    current_price = hist['Close'].iloc[-1]
                    prev_close = hist['Close'].iloc[-2]
                    price_diff = current_price - prev_close
                    percent_diff = (price_diff / prev_close) * 100

                    col1, col2, col3 = st.columns(3)
                    col1.metric("Harga Terakhir", f"Rp {current_price:,.0f}", f"{price_diff:+.0f} ({percent_diff:+.2f}%)")
                    col2.metric("Volume Hari Ini", f"{hist['Volume'].iloc[-1]:,.0f}")
                    col3.metric("Harga Tertinggi", f"Rp {hist['High'].iloc[-1]:,.0f}")
                    
                    # Indikator MA
                    hist['MA20'] = hist['Close'].rolling(window=20).mean()
                    hist['MA50'] = hist['Close'].rolling(window=50).mean()

                    # Grafik
                    fig = go.Figure(data=[
                        go.Candlestick(x=hist.index, open=hist['Open'], high=hist['High'], low=hist['Low'], close=hist['Close'], name="Price"),
                        go.Scatter(x=hist.index, y=hist['MA20'], line=dict(color='orange', width=1), name="MA20"),
                        go.Scatter(x=hist.index, y=hist['MA50'], line=dict(color='blue', width=1), name="MA50")
                    ])
                    st.plotly_chart(fig, use_container_width=True)

                    # Analisis AI
                    data_summary = f"Harga: {current_price}, Vol: {hist['Volume'].iloc[-1]}, PBV: {stock.info.get('priceToBook')}"
                    response = model.generate_content(f"{get_system_prompt(mode, ticker_input)}\n\nData: {data_summary}")
                    
                    st.subheader(f"🤖 Hasil Analisis {ticker_input}")
                    analysis_text = response.text
                    st.markdown(analysis_text)

                    # Fitur Download
                    st.download_button(
                        label="📥 Download Hasil Analisis",
                        data=analysis_text,
                        file_name=f"Analisis_{ticker_input}_{datetime.now().strftime('%Y%m%d')}.txt",
                        mime="text/plain"
                    )

        except Exception as e:
            st.error(f"Kesalahan: {e}")
