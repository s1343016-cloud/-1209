import streamlit as st
import pandas as pd
import pydeck as pdk
import os

# ===============================================
#   全台捷運 / 輕軌＋車站人流 3D 視覺化（固定資料版）
#   讀取 data/mrt_ridership.csv
#   CSV 欄位：系統, 線名, 車站, 緯度, 經度, 日平均, 年總量
# ===============================================
st.title("🚇 全台捷運・輕軌 3D 車站人流地圖（固定資料）")

# 0. 檢查 Mapbox 金鑰
if "MAPBOX_API_KEY" not in st.secrets:
    st.error("Mapbox API Key (名稱需為 MAPBOX_API_KEY) 未設定！請在雲端 Secrets 中設定。")
    st.stop()

pdk.settings.mapbox_api_key = st.secrets["MAPBOX_API_KEY"]

# 顏色設定
LINE_COLOR_MAP = {
    "台北紅線":     [227, 0, 46, 200],
    "台中捷運":     [0, 160, 80, 200],
    "高雄輕軌":     [0, 166, 81, 200],
    "台北綠線":     [0, 148, 96, 200],
    "北捷環狀線":   [255, 222, 0, 200],
    "台北安坑輕軌": [0, 180, 120, 200],
    "台北文湖線":   [155, 118, 83, 200],
    "台北板南線":   [0, 112, 189, 200],
    "淡海輕軌":     [0, 170, 170, 200],
    "高捷紅線":     [226, 0, 26, 200],
    "高捷橘線":     [247, 148, 29, 200],
    "北捷o線":      [255, 210, 60, 200],
    "桃園機捷":     [140, 80, 180, 200],
}
DEFAULT_COLOR = [120, 120, 120, 200]

# 1. 讀取固定 CSV 檔
csv_path = os.path.join("data", "mrt_ridership.csv")
if not os.path.exists(csv_path):
    st.error(f"找不到資料檔：{csv_path}，請確認檔案存在且路徑正確。")
    st.stop()

df_raw = pd.read_csv(csv_path, encoding="utf-8-sig")

required_cols = {"系統", "線名", "車站", "緯度", "經度", "日平均", "年總量"}
if not required_cols.issubset(df_raw.columns):
    st.error(f"CSV 檔必須包含欄位：{required_cols}，目前欄位為：{set(df_raw.columns)}")
    st.stop()

st.subheader("1️⃣ 資料預覽（中文欄位）")
st.dataframe(df_raw)

# 2. 轉成內部英文欄位名稱
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
df["lat"] = pd.to_numeric(df["lat"], errors="coerce")
df["lon"] = pd.to_numeric(df["lon"], errors="coerce")
df["daily_avg"] = pd.to_numeric(df["daily_avg"], errors="coerce")
df["year_total"] = pd.to_numeric(df["year_total"], errors="coerce")

# 緯度、經度必須有；流量沒有就設 0
df = df.dropna(subset=["lat", "lon"])
df["daily_avg"] = df["daily_avg"].fillna(0)
df["year_total"] = df["year_total"].fillna(0)

if df.empty:
    st.error("所有列的緯度 / 經度都是空的或無法轉成數字，請檢查 CSV 資料內容。")
    st.stop()

# 線名 -> 顏色
def map_line_color(line_name: str):
    if pd.isna(line_name):
        return DEFAULT_COLOR
    return LINE_COLOR_MAP.get(str(line_name), DEFAULT_COLOR)

df["color"] = df["line"].apply(map_line_color)

# 3. 互動式選擇線路
st.subheader("2️⃣ 選擇要顯示的線路")

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

# 4. 視覺化設定
st.subheader("3️⃣ 視覺化設定")

metric_option = st.selectbox(
    "柱子高度使用的數字",
    ("日平均", "年總量"),
)
elevation_column = "daily_avg" if metric_option == "日平均" else "year_total"

elevation_scale = st.slider(
    "柱子高度倍率 (elevation_scale)",
    min_value=0.0001,
    max_value=0.5,
    value=0.01,
    step=0.0001,
)

# 5. 觀察視角設定
st.subheader("4️⃣ 觀察視角設定")

center_lat = df_view["lat"].mean()
center_lon = df_view["lon"].mean()

zoom = 9.0  # 固定 zoom，滑鼠仍可縮放

pitch = st.slider(
    "俯視角度（pitch）",
    min_value=0,
    max_value=85,
    value=50,
    step=1,
)

bearing = st.slider(
    "旋轉角度（bearing）",
    min_value=-180,
    max_value=180,
    value=0,
    step=1,
)

view_state = pdk.ViewState(
    latitude=center_lat,
    longitude=center_lon,
    zoom=zoom,
    pitch=pitch,
    bearing=bearing,
)

# 6. 建立 ColumnLayer
station_layer = pdk.Layer(
    "ColumnLayer",
    data=df_view,
    get_position="[lon, lat]",
    get_elevation=elevation_column,
    elevation_scale=elevation_scale,
    radius=150,
    pickable=True,
    extruded=True,
    get_fill_color="color",
)

# 7. 顯示地圖
r = pdk.Deck(
    layers=[station_layer],
    initial_view_state=view_state,
    map_style="mapbox://styles/mapbox/light-v10",
    tooltip={
        "text": (
            "系統：{system}\n"
            "線名：{line}\n"
            "車站：{station}\n"
            "日平均：{daily_avg}\n"
            "年總量：{year_total}"
        )
    },
)

st.subheader("5️⃣ 全台捷運・輕軌 3D 車站人流地圖")
st.pydeck_chart(r)
