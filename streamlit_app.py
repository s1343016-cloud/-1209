import streamlit as st
import pandas as pd
import pydeck as pdk

# ===============================================
#   全台捷運 / 輕軌＋車站人流 3D 視覺化
#   CSV 欄位：系統, 線名, 車站, 緯度, 經度, 日平均, 年總量
# ===============================================
st.title("🚇 全台捷運・輕軌 3D 車站人流地圖（可選線路）")

# 0. 檢查 Mapbox 金鑰
if "MAPBOX_API_KEY" not in st.secrets:
    st.error("Mapbox API Key (名稱需為 MAPBOX_API_KEY) 未設定！請在雲端 Secrets 中設定。")
    st.stop()

pdk.settings.mapbox_api_key = st.secrets["MAPBOX_API_KEY"]

# 顏色設定：依你給的 13 條線
LINE_COLOR_MAP = {
    "台北紅線":     [227, 0, 46, 200],    # 紅
    "台中捷運":     [0, 160, 80, 200],    # 綠
    "高雄輕軌":     [0, 166, 81, 200],    # 綠
    "台北綠線":     [0, 148, 96, 200],    # 綠
    "北捷環狀線":   [255, 222, 0, 200],  # 黃
    "台北安坑輕軌": [0, 180, 120, 200],  # 淺綠
    "台北文湖線":   [155, 118, 83, 200], # 棕
    "台北板南線":   [0, 112, 189, 200],  # 藍
