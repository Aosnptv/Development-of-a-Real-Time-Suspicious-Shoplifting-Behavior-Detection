import streamlit as st
import pandas as pd
import numpy as np
from dashboard.components import render_top_status_bar

def render_analytics():
    render_top_status_bar()
    st.title("Analytics")
    
    st.subheader("Alert Analytics")
    col_chart1, col_chart2 = st.columns(2)
    with col_chart1:
        st.write("Alerts per Day")
        chart_data_day = pd.DataFrame(np.random.randint(5, 25, size=(7, 1)), columns=["Alerts"], index=["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"])
        st.bar_chart(chart_data_day)
    with col_chart2:
        st.write("Alerts per Hour")
        chart_data_hour = pd.DataFrame(np.random.randint(0, 10, size=(24, 1)), columns=["Alerts"])
        st.line_chart(chart_data_hour)