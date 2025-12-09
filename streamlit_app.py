import streamlit as st
import pandas as pd
import pydeck as pdk

# ===============================================
#   台北捷運站：人流 3D 視覺化 (上傳 CSV 版)
#   CSV 欄位：車站, 緯度, 經度, 日平均, 年總量
# ===============================================
st.title("🚇 台北捷運站人流 3D 地圖（上傳 CSV）")

# 0. 檢查 Mapbox 金鑰
if "MAPBOX_API_KEY" not in st.secrets:
    st.error("Mapbox API Key (名稱需為 MAPBOX_API_KEY) 未設定！請在雲端 Secrets 中設定。")
    st.stop()

pdk.settings.mapbox_api_key = st.secrets["MAPBOX_API_KEY"]

# 1. 上傳 CSV 檔
st.subheader("1️⃣ 上傳捷運站人流資料（CSV）")
uploaded_file = st.file_uploader(
    "請上傳包含 車站, 緯度, 經度, 日平均, 年總量 欄位的 CSV 檔",
    type=["csv"]
)

if uploaded_file is None:
    st.info("尚未上傳檔案，請先上傳 CSV 才會顯示地圖。")
    st.stop()

# 2. 讀取原始資料（保留中文欄位給使用者看）
df_raw = pd.read_csv(uploaded_file)

required_cols = {"車站", "緯度", "經度", "日平均", "年總量"}
if not required_cols.issubset(df_raw.columns):
    st.error(f"CSV 檔必須包含欄位：{required_cols}，目前欄位為：{set(df_raw.columns)}")
    st.stop()

st.subheader("2️⃣ 原始資料預覽（中文欄位）")
st.dataframe(df_raw)

# 3. 轉成內部英文欄位名稱給 pydeck 使用
df = df_raw.rename(columns={
    "車站": "station",
    "緯度": "lat",
    "經度": "lon",
    "日平均": "daily_avg",
    "年總量": "year_total",
})

# 4. 視覺化參數：選擇高度用日平均或年總量
st.subheader("3️⃣ 視覺化參數設定")

metric_option = st.selectbox(
    "選擇要用哪個數字當柱子高度",
    ("日平均", "年總量")
)

if metric_option == "日平均":
    elevation_column = "daily_avg"
else:
    elevation_column = "year_total"

elevation_scale = st.slider(
    "柱子高度倍率 (elevation_scale)",
    min_value=0.0001,
    max_value=0.5,
    value=0.01,
    step=0.0001,
    help="如果柱子太高或太矮，可以調整這個倍率。"
)

# 5. 建立 ColumnLayer（每一站一根 3D 柱子）
layer_column = pdk.Layer(
    "ColumnLayer",
    data=df,
    get_position="[lon, lat]",          # 內部已改成 lon, lat
    get_elevation=elevation_column,     # 根據選擇使用日平均或年總量
    elevation_scale=elevation_scale,
    radius=150,                         # 每個柱子的底面半徑 (公尺)
    pickable=True,
    extruded=True,
    get_fill_color="[255, 140, 0, 200]",  # 橘色半透明
)

# 6. 設定視角（以台北車站附近為中心）
view_state = pdk.ViewState(
    latitude=25.0478,
    longitude=121.5170,
    zoom=11,
    pitch=50,
    bearing=0,
)

# 7. 顯示地圖
r = pdk.Deck(
    layers=[layer_column],
    initial_view_state=view_state,
    map_style="mapbox://styles/mapbox/light-v10",
    tooltip={
        "text": (
            "車站：{station}\n"
            "日平均：{daily_avg}\n"
            "年總量：{year_total}"
        )
    },
)

st.subheader("4️⃣ 3D 人流地圖")
st.pydeck_chart(r)
