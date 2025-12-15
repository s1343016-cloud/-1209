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
    "台北紅線":   [227, 0, 46, 200],    # 紅
    "台中捷運":   [0, 160, 80, 200],    # 綠
    "高雄輕軌":   [0, 166, 81, 200],    # 綠
    "台北綠線":   [0, 148, 96, 200],    # 綠
    "北捷環狀線": [255, 222, 0, 200],  # 黃
    "台北安坑輕軌": [0, 180, 120, 200],# 淺綠
    "台北文湖線": [155, 118, 83, 200], # 棕
    "台北板南線": [0, 112, 189, 200],  # 藍
    "淡海輕軌":   [0, 170, 170, 200],  # 藍綠
    "高捷紅線":   [226, 0, 26, 200],   # 紅
    "高捷橘線":   [247, 148, 29, 200], # 橘
    "北捷o線":   [255, 210, 60, 200],  # 黃橘
    "桃園機捷":   [140, 80, 180, 200], # 紫
}
DEFAULT_COLOR = [120, 120, 120, 200]

# 1. 上傳 CSV 檔
st.subheader("1️⃣ 上傳車站人流資料（CSV）")
uploaded_file = st.file_uploader(
    "請上傳包含 系統, 線名, 車站, 緯度, 經度, 日平均, 年總量 欄位的 CSV 檔",
    type=["csv"],
)

if uploaded_file is None:
    st.info("尚未上傳檔案，請先上傳 CSV 才會顯示地圖。")
    st.stop()

# 2. 讀取 CSV（處理常見編碼）
decode_success = False
encodings_to_try = ["utf-8", "utf-8-sig", "big5", "cp950"]

for enc in encodings_to_try:
    try:
        uploaded_file.seek(0)
        df_raw = pd.read_csv(uploaded_file, encoding=enc)
        decode_success = True
        st.info(f"CSV 以編碼 {enc} 成功讀取")
        break
    except UnicodeDecodeError:
        continue

if not decode_success:
    st.error("CSV 檔案解碼失敗，請嘗試將檔案另存為 UTF-8 或 Big5 再上傳。")
    st.stop()

required_cols = {"系統", "線名", "車站", "緯度", "經度", "日平均", "年總量"}
if not required_cols.issubset(df_raw.columns):
    st.error(f"CSV 檔必須包含欄位：{required_cols}，目前欄位為：{set(df_raw.columns)}")
    st.stop()

st.subheader("2️⃣ 原始資料預覽（中文欄位）")
st.dataframe(df_raw)

# 3. 轉成內部英文欄位名稱
df = df_raw.rename(columns={
    "系統": "system",
    "線名": "line",
    "車站": "station",
    "緯度": "lat",
    "經度": "lon",
    "日平均": "daily_avg",
    "年總量": "year_total",
})

# 數值欄位轉 float
for col in ["lat", "lon", "daily_avg", "year_total"]:
    df[col] = pd.to_numeric(df[col], errors="coerce")

df = df.dropna(subset=["lat", "lon", "daily_avg", "year_total"])
if df.empty:
    st.error("所有列的數值欄位皆無法轉成數字，請檢查 CSV 資料內容。")
    st.stop()

# 線名 -> 顏色
def map_line_color(line_name: str):
    if pd.isna(line_name):
        return DEFAULT_COLOR
    return LINE_COLOR_MAP.get(str(line_name), DEFAULT_COLOR)

df["color"] = df["line"].apply(map_line_color)

# 4. 互動式選擇線路
st.subheader("3️⃣ 選擇要顯示的線路")

all_lines = sorted(df["line"].dropna().unique())
selected_lines = st.multiselect(
    "選擇線路（可多選）",
    options=all_lines,
    default=all_lines,
)

if not selected_lines:
    st.warning("尚未選擇任何線路，請至少選一條線。")
    st.stop()

df_view = df[df["line"].isin(selected_lines)]

# 5. 選擇高度使用日平均 / 年總量
metric_option = st.selectbox(
    "柱子高度使用的數字",
    ("日平均", "年總量"),
)
elevation_col_
