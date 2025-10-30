import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from fpdf import FPDF, XPos, YPos
import requests  # New import
import time       # New import
from streamlit_lottie import st_lottie # New import

# --- 1. SETTINGS & DATA LOADING ---
st.set_page_config(
    page_title="Solar Investment Platform",
    page_icon="🌞",
    layout="wide"
)

@st.cache_data
def load_data():
    df = pd.read_csv('data.csv')
    return df

# --- NEW LOTTIE FUNCTION ---
@st.cache_data
def load_lottie_url(url: str):
    r = requests.get(url)
    if r.status_code != 200:
        return None
    return r.json()

df = load_data()

# --- 2. SESSION STATE INITIALIZATION ---
if 'results' not in st.session_state:
    st.session_state.results = None

def clear_results():
    st.session_state.results = None

# --- 3. PDF GENERATOR FUNCTION ---
def create_pdf(country, city, size, cost, net_cost, revenue, payback, energy, policy, symbol, currency_code):
    pdf = FPDF()
    pdf.add_page()
    
    # Title
    pdf.set_font("Helvetica", 'B', 16)
    pdf.cell(0, 10, f"Solar Investment Summary: {city}, {country}", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
    pdf.ln(10) 
    
    # Key Metrics
    pdf.set_font("Helvetica", 'B', 12)
    pdf.cell(0, 10, "Key Metrics", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("Helvetica", '', 12)
    pdf.cell(0, 8, f"  - Payback Period: {payback:.2f} Years", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.cell(0, 8, f"  - Net System Cost: {net_cost:,.2f} {currency_code}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.cell(0, 8, f"  - Est. Annual Revenue: {revenue:,.2f} {currency_code}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(5)

    # Input Assumptions
    pdf.set_font("Helvetica", 'B', 12)
    pdf.cell(0, 10, "Input Assumptions", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("Helvetica", '', 12)
    pdf.cell(0, 8, f"  - Location: {city}, {country}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.cell(0, 8, f"  - System Size: {size} kW", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.cell(0, 8, f"  - Initial Cost (Est.): {cost:,.2f} {currency_code}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.cell(0, 8, f"  - Est. Annual Energy: {energy:,.0f} kWh", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(5)
    
    # Policy Notes
    pdf.set_font("Helvetica", 'B', 12)
    pdf.cell(0, 10, "Policy & Incentives", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("Helvetica", '', 12)
    pdf.multi_cell(0, 8, f"  - {policy}") 
    
    return bytes(pdf.output())


# --- 4. SIDEBAR ---
with st.sidebar:
    st.header("🌞 Input Your System Details")
    
    # --- ADDED LOTTIE ANIMATION ---
    lottie_url = "https://lottie.host/7e00e238-0331-4a11-b1e1-11d7f1e72e12/T5vBf3Yx2N.json"
    lottie_json = load_lottie_url(lottie_url)
    if lottie_json:
        st_lottie(lottie_json, height=150, key="solar_lottie")
    
    selected_country = st.selectbox(
        "Select Country", 
        df['Country'].unique(), 
        on_change=clear_results
    )

    cities_in_country = df[df['Country'] == selected_country]['City'].tolist()
    selected_city = st.selectbox(
        "Select City", 
        cities_in_country,
        on_change=clear_results
    )

    country_data = df[df['Country'] == selected_country].iloc[0]
    local_code = country_data['Local_Currency_Code']
    local_symbol = country_data['Local_Currency_Symbol']
    local_rate = country_data['USD_to_Local_Rate']

    system_size_kw = st.number_input(
        "System Size (kW)", 
        min_value=1.0, value=5.0, step=0.5,
        on_change=clear_results
    )
    system_cost_usd = st.number_input(
        "Total System Cost (USD)", 
        min_value=1000, value=6000, step=100,
        on_change=clear_results,
        help="All cost inputs must be in USD. We will convert it for you."
    )

    display_currency = st.selectbox(
        "Display Currency",
        ["USD", local_code],
        on_change=clear_results
    )

    calculate_button = st.button("Calculate ROI")
    st.caption(f"Note: Exchange rates are static. 1 USD = {local_rate:.2f} {local_code}")


# --- 5. MAIN APP UI ---
st.title("🌞 Cross-Border Solar Investment Platform")
st.write("A simple tool to compare solar investment opportunities.")

# --- 6. ROI CALCULATION ---
if calculate_button:
    # --- ADDED SPINNER ---
    with st.spinner("Calculating your ROI..."):
        time.sleep(1) # Added a tiny delay to make the spinner visible
        
        city_data = df[df['City'] == selected_city].iloc[0]
        
        ghi = city_data['GHI_Daily']
        tariff = city_data['Tariff_USD_kWh']
        incentive_type = city_data['Incentive_Type']
        incentive_value_usd = city_data['Incentive_Value_USD']
        policy_summary = city_data['Policy_Summary']

        if display_currency == "USD":
            display_rate = 1.0
            display_symbol = "$"
        else:
            display_rate = local_rate
            display_symbol = local_symbol

        PERFORMANCE_RATIO = 0.75 
        annual_energy_kwh = system_size_kw * ghi * 365 * PERFORMANCE_RATIO
        annual_revenue_usd = annual_energy_kwh * tariff
        
        if incentive_type == "CAPEX_Subsidy":
            net_system_cost_usd = system_cost_usd - incentive_value_usd
        else:
            net_system_cost_usd = system_cost_usd
        
        payback_period_years = net_system_cost_usd / max(0.01, annual_revenue_usd)
        
        display_cost = system_cost_usd * display_rate
        display_net_cost = net_system_cost_usd * display_rate
        display_revenue = annual_revenue_usd * display_rate
        
        pdf_bytes = create_pdf(
            country=selected_country,
            city=selected_city,
            size=system_size_kw,
            cost=display_cost,
            net_cost=display_net_cost,
            revenue=display_revenue,
            payback=payback_period_years,
            energy=annual_energy_kwh,
            policy=policy_summary,
            symbol=display_symbol,
            currency_code=display_currency
        )
        
        st.session_state.results = {
            "country": selected_country,
            "city": selected_city,
            "payback": payback_period_years,
            "net_cost": display_net_cost,
            "revenue": display_revenue,
            "energy": annual_energy_kwh,
            "pdf_bytes": pdf_bytes,
            "file_name": f"Solar_Report_{selected_country}_{selected_city}.pdf",
            "incentive_value": incentive_value_usd * display_rate,
            "incentive_type": incentive_type,
            "ghi": ghi,
            "tariff": tariff * display_rate,
            "size": system_size_kw,
            "cost": display_cost,
            "ratio": PERFORMANCE_RATIO,
            "symbol": display_symbol,
            "currency_code": display_currency
        }
    
    # --- ADDED TOAST ---
    st.toast(f"Success! Calculated for {selected_city}.", icon="✅")

# --- 7. DISPLAY RESULTS (NO TABS) ---
if st.session_state.results:
    res = st.session_state.results
    
    st.header(f"📊 Results for {res['city']}, {res['country']}")
    
    st.subheader(f"Simple Payback Period: {res['payback']:.2f} Years")
    st.progress(1.0 / max(1.0, res['payback']))

    col1, col2, col3 = st.columns(3)
    col1.metric("Net System Cost", f"{res['symbol']}{res['net_cost']:,.2f} {res['currency_code']}")
    col2.metric("Annual Revenue", f"{res['symbol']}{res['revenue']:,.2f} {res['currency_code']}")
    col3.metric("Annual Energy", f"{res['energy']:,.0f} kWh")
    
    st.subheader("Download Your Report")
    
    st.download_button(
        label="Download Investment Summary (PDF)",
        data=res['pdf_bytes'],
        file_name=res['file_name'],
        mime="application/pdf"
    )
    
    with st.expander("Show Calculation Details"):
        st.write(f"- **Inputs:** {res['size']} kW system, {res['symbol']}{res['cost']:,.2f} {res['currency_code']} cost")
        st.write(f"- **Incentive:** {res['symbol']}{res['incentive_value']:,.2f} ({res['incentive_type']})")
        st.write(f"- **Solar Potential (GHI):** {res['ghi']} kWh/f²/day")
        st.write(f"- **Electricity Tariff (Est.):** {res['symbol']}{res['tariff']:.2f}/kWh")
        st.write(f"- **Performance Ratio:** {res['ratio'] * 100}% (Assumed)")
else:
    st.info("Please enter your system details in the sidebar and click 'Calculate ROI'.")

# --- 8. DATA OVERVIEW (NO TABS) ---
st.header("📈 Data Overview (All Cities)")
st.dataframe(df)

# --- 9. MAP (NO TABS) ---
st.header("🗺️ Solar Potential Map (All Cities)")
m = folium.Map(location=[10.0, 55.0], zoom_start=3)
for idx, row in df.iterrows():
    popup_text = (
        f"Tariff: ${row['Tariff_USD_kWh']}/kWh<br>"
        f"Policy: {row['Policy_Summary']}<br>"
        f"Rate: 1 USD = {row['USD_to_Local_Rate']} {row['Local_Currency_Code']}"
    )
    folium.Marker(
        location=[row['Latitude'], row['Longitude']],
        tooltip=f"{row['City']}, {row['Country']}<br>GHI: {row['GHI_Daily']} kWh/m²/day",
        popup=popup_text,
        icon=folium.Icon(color="red", icon="info-sign")
    )..add_to(m)
st_folium(m, width=725, height=500)