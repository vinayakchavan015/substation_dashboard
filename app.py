import os

import pandas as pd
import plotly.express as px
import streamlit as st

DEFAULT_SHEET_ID = "1TwkYiWbLR97PuwqK7w39YTx6ruQ3-ZFyLrtcNhg2kdM"


def get_sheet_id():
    """Allow overriding the Google Sheet ID without hardcoding a production value."""
    return os.getenv("SHEET_ID") or os.getenv("GOOGLE_SHEET_ID") or DEFAULT_SHEET_ID


SHEET_ID = get_sheet_id()


@st.cache_data(ttl=60)
def load_data():
    """Load all required Google Sheet tabs and return the DataFrames."""
    urls = {
        "monthly": f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Monthly_Summary",
        "loss": f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Substation_Loss_Data",
        "master": f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Feeder_Master",
    }

    try:
        monthly_df = pd.read_csv(urls["monthly"])
        loss_df = pd.read_csv(urls["loss"])
        master_df = pd.read_csv(urls["master"])
    except Exception as exc:  # pragma: no cover - exercised via runtime integration
        raise ValueError(
            "डेटा लोड करताना त्रुटी आली. कृपया Google Sheet ID/लिंक आणि शीटचे नाव तपासा."
        ) from exc

    return monthly_df, loss_df, master_df


def run_dashboard():
    st.set_page_config(
        page_title="33/11 KV सरतोडी उपकेंद्र डॅशबोर्ड",
        page_icon="⚡",
        layout="wide",
    )

    st.markdown(
        "<h2 style='text-align: center; color: #0f4c81;'>⚡ महावितरण - ३३/११ केव्ही सरतोडी उपकेंद्र (284619) ⚡</h2>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<h4 style='text-align: center; color: #555;'>लाईव्ह ॲनालिटिक्स व परफॉर्मन्स डॅशबोर्ड</h4><hr>",
        unsafe_allow_html=True,
    )

    try:
        monthly_df, loss_df, master_df = load_data()
    except ValueError as exc:
        st.error(str(exc))
        return

    required_cols = {"Year", "Month", "Feeder_Name", "Total_Tripping_Nos", "Total_Duration_Min"}
    missing_cols = required_cols - set(monthly_df.columns)
    if missing_cols:
        st.error(f"Monthly_Summary शीटमध्ये आवश्यक कॉलम गहाळ आहेत: {sorted(missing_cols)}")
        return

    if monthly_df.empty:
        st.warning("Monthly_Summary शीट रिकामी आहे. डेटा उपलब्ध नाही.")
        return

    st.sidebar.header("🔍 फिल्टर निवडा")
    years = sorted(pd.to_numeric(monthly_df["Year"], errors="coerce").dropna().unique().astype(int), reverse=True)
    if not years:
        st.warning("Year डेटा उपलब्ध नाही. कृपया शीटची संरचना तपासा.")
        return

    selected_year = st.sidebar.selectbox("📅 वर्ष निवडा:", years, index=0)
    available_months = (
        monthly_df.loc[monthly_df["Year"] == selected_year, "Month"].dropna().astype(str).unique().tolist()
    )
    if not available_months:
        st.warning(f"{selected_year} साठी महिना ड��टा उपलब्ध नाही.")
        return

    selected_month = st.sidebar.selectbox("🗓️ महिना निवडा:", available_months, index=0)
    filtered_month_df = monthly_df[(monthly_df["Year"] == selected_year) & (monthly_df["Month"].astype(str) == selected_month)]
    filtered_loss_df = loss_df[(loss_df["Year"] == selected_year) & (loss_df["Month"].astype(str) == selected_month)]

    st.subheader(f"📊 {selected_month} {selected_year} चा संक्षिप्त अहवाल")

    total_tripping = pd.to_numeric(filtered_month_df["Total_Tripping_Nos"], errors="coerce").sum()
    total_duration = pd.to_numeric(filtered_month_df["Total_Duration_Min"], errors="coerce").sum()
    max_load = pd.to_numeric(filtered_month_df["Max_Load_Amp"], errors="coerce").max()

    loss_val = "N/A"
    if not filtered_loss_df.empty and "Loss_%" in filtered_loss_df.columns:
        raw_loss = filtered_loss_df["Loss_%"].iloc[0]
        try:
            loss_val = f"{float(raw_loss):.2f} %"
        except (TypeError, ValueError):
            loss_val = str(raw_loss)

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("🔴 एकूण ट्रिपिंग", f"{int(total_tripping)} वेळा")
    k2.metric("⏱️ बंद कालावधी", f"{int(total_duration)} मिनिटे")
    k3.metric("📈 कमाल लोड (Peak)", f"{max_load} Amp" if pd.notna(max_load) else "N/A")
    k4.metric("⚡ वीज हानी (Loss)", loss_val)

    st.write("---")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### 🔌 फिडरनिहाय ट्रिपिंग")
        trip_data = filtered_month_df[pd.to_numeric(filtered_month_df["Total_Tripping_Nos"], errors="coerce") > 0]
        if not trip_data.empty:
            fig1 = px.bar(
                trip_data,
                x="Feeder_Name",
                y="Total_Tripping_Nos",
                text="Total_Tripping_Nos",
                labels={"Feeder_Name": "फिडर", "Total_Tripping_Nos": "ट्रिपिंग"},
                color="Total_Tripping_Nos",
                color_continuous_scale="Reds",
            )
            fig1.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig1, use_container_width=True)
        else:
            st.info("या महिन्यासाठी ट्रिपिंग डेटा उपलब्ध नाही.")

    with col2:
        st.markdown("### ⏱️ बंद कालावधी (मिनिटे)")
        dur_data = filtered_month_df[pd.to_numeric(filtered_month_df["Total_Duration_Min"], errors="coerce") > 0]
        if not dur_data.empty:
            fig2 = px.bar(
                dur_data,
                x="Feeder_Name",
                y="Total_Duration_Min",
                text="Total_Duration_Min",
                labels={"Feeder_Name": "फिडर", "Total_Duration_Min": "कालावधी"},
                color="Total_Duration_Min",
                color_continuous_scale="Oranges",
            )
            fig2.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("या महिन्यासाठी कालावधी डेटा उपलब्ध नाही.")

    st.write("---")
    with st.expander("📑 फिडर मास्टर तपशील (CT Ratio, Meter No, Settings)"):
        st.dataframe(master_df, use_container_width=True)


def main():
    run_dashboard()


if __name__ == "__main__":
    main()
