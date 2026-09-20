import streamlit as st
import pandas as pd
import plotly.express as px

# ⚠️ येथे तुमच्या Google Sheet चा ID टाका
SHEET_ID = "1TwkYiWbLR97PuwqK7w39YTx6ruQ3-ZFyLrtcNhg2kdM"

st.set_page_config(
    page_title="33/11 KV सरतोडी उपकेंद्र डॅशबोर्ड",
    page_icon="⚡",
    layout="wide"
)

st.markdown("<h2 style='text-align: center; color: #0f4c81;'>⚡ महावितरण - ३३/११ केव्ही सरतोडी उपकेंद्र (284619) ⚡</h2>", unsafe_allow_html=True)
st.markdown("<h4 style='text-align: center; color: #555;'>लाईव्ह ॲनालिटिक्स व परफॉर्मन्स डॅशबोर्ड</h4><hr>", unsafe_allow_html=True)

# Google Sheet मधून डेटा थेट लोड करणे
@st.cache_data(ttl=60)
def load_data():
    url_monthly = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Monthly_Summary"
    url_loss = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Substation_Loss_Data"
    url_master = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Feeder_Master"

    monthly_df = pd.read_csv(url_monthly)
    loss_df = pd.read_csv(url_loss)
    master_df = pd.read_csv(url_master)
    return monthly_df, loss_df, master_df

try:
    monthly_df, loss_df, master_df = load_data()

    # साइडबार फिल्टर्स
    st.sidebar.header("🔍 फिल्टर निवडा")
    years = sorted([int(y) for y in monthly_df['Year'].dropna().unique()], reverse=True)
    selected_year = st.sidebar.selectbox("📅 वर्ष निवडा:", years, index=0)

    available_months = monthly_df[monthly_df['Year'] == selected_year]['Month'].dropna().unique().tolist()
    selected_month = st.sidebar.selectbox("🗓️ महिना निवडा:", available_months, index=0)

    filtered_month_df = monthly_df[(monthly_df['Year'] == selected_year) & (monthly_df['Month'] == selected_month)]
    filtered_loss_df = loss_df[(loss_df['Year'] == selected_year) & (loss_df['Month'] == selected_month)]

    # १. मुख्य आकडेवारी (KPIs)
    st.subheader(f"📊 {selected_month} {selected_year} चा संक्षिप्त अहवाल")
    
    total_tripping = filtered_month_df['Total_Tripping_Nos'].sum()
    total_duration = filtered_month_df['Total_Duration_Min'].sum()
    max_load = filtered_month_df['Max_Load_Amp'].max()

    loss_val = "N/A"
    if not filtered_loss_df.empty:
        raw_loss = filtered_loss_df['Loss_%'].values[0]
        try:
            loss_val = f"{float(raw_loss):.2f} %"
        except:
            loss_val = str(raw_loss)

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("🔴 एकूण ट्रिपिंग", f"{int(total_tripping)} वेळा")
    k2.metric("⏱️ बंद कालावधी", f"{int(total_duration)} मिनिटे")
    k3.metric("📈 कमाल लोड (Peak)", f"{max_load} Amp")
    k4.metric("⚡ वीज हानी (Loss)", loss_val)

    st.write("---")

    # २. आलेख (Charts)
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### 🔌 फिडरनिहाय ट्रिपिंग")
        trip_data = filtered_month_df[filtered_month_df['Total_Tripping_Nos'] > 0]
        if not trip_data.empty:
            fig1 = px.bar(trip_data, x="Feeder_Name", y="Total_Tripping_Nos", text="Total_Tripping_Nos",
                          labels={"Feeder_Name": "फिडर", "Total_Tripping_Nos": "ट्रिपिंग"},
                          color="Total_Tripping_Nos", color_continuous_scale="Reds")
            fig1.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig1, use_container_width=True)
        else:
            st.info("या महिन्यासाठी ट्रिपिंग डेटा उपलब्ध नाही.")

    with col2:
        st.markdown("### ⏱️ बंद कालावधी (मिनिटे)")
        dur_data = filtered_month_df[filtered_month_df['Total_Duration_Min'] > 0]
        if not dur_data.empty:
            fig2 = px.bar(dur_data, x="Feeder_Name", y="Total_Duration_Min", text="Total_Duration_Min",
                          labels={"Feeder_Name": "फिडर", "Total_Duration_Min": "कालावधी"},
                          color="Total_Duration_Min", color_continuous_scale="Oranges")
            fig2.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("या महिन्यासाठी कालावधी डेटा उपलब्ध नाही.")

    # ३. फिडर मास्टर
    st.write("---")
    with st.expander("📑 फिडर मास्टर तपशील (CT Ratio, Meter No, Settings)"):
        st.dataframe(master_df, use_container_width=True)

except Exception as e:
    st.error("डेटा लोड करताना त्रुटी आली. कृपया गुगल शीटची लिंक/आयडी आणि शीटचे नाव (Tab Name) तपासा.")
