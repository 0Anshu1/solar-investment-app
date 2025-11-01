import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from fpdf import FPDF, XPos, YPos
import requests
import time
from streamlit_lottie import st_lottie

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
# Changed 'results' to 'results_data' to handle both single (dict) and compare (list)
if 'results_data' not in st.session_state:
    st.session_state.results_data = None

def clear_results():
    st.session_state.results_data = None

# --- 3. PDF GENERATOR FUNCTION ---
# (No changes to this function)
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

    # --- NEW: COMPARE MODE TOGGLE ---
    compare_mode = st.toggle("Compare Mode", on_change=clear_results, help="Select multiple cities within one country to compare ROI.")

    selected_country = st.selectbox(
        "Select Country", 
        df['Country'].unique(), 
        on_change=clear_results
    )
    
    cities_in_country = df[df['Country'] == selected_country]['City'].tolist()
    
    # --- NEW: CONDITIONAL CITY SELECTOR ---
    if compare_mode:
        selected_cities = st.multiselect(
            "Select Cities to Compare", 
            cities_in_country,
            on_change=clear_results
        )
        selected_city = None # Not used in compare mode
    else:
        selected_city = st.selectbox(
            "Select City", 
            cities_in_country,
            on_change=clear_results
        )
        selected_cities = [] # Not used in single mode

    # --- NEW: AUTO-FILL EXAMPLES (for GHI) ---
    if not compare_mode and selected_city:
        city_data_for_example = df[df['City'] == selected_city].iloc[0]
        ghi_example = city_data_for_example['GHI_Daily']
        st.caption(f"ℹ️ **Info for {selected_city}:**\n- GHI: {ghi_example} kWh/m²/day\n- *Add 'Avg_Cost_per_kW' to your CSV to show cost examples.*")


    country_data = df[df['Country'] == selected_country].iloc[0]
    local_code = country_data['Local_Currency_Code']
    local_symbol = country_data['Local_Currency_Symbol']
    local_rate = country_data['USD_to_Local_Rate']

    system_size_kw = st.number_input(
        "System Size (kW)", 
        min_value=1.0, value=5.0, step=0.5,
        on_change=clear_results,
        # --- NEW: TOOLTIP ---
        help="Total panel capacity you plan to install (e.g., 5 kW)."
    )
    system_cost_usd = st.number_input(
        "Total System Cost (USD)", 
        min_value=1000, value=6000, step=100,
        on_change=clear_results,
        # --- NEW: TOOLTIP ---
        help="Your estimated total cost for panels, inverter, and installation, in USD."
    )

    display_currency = st.selectbox(
        "Display Currency",
        ["USD", local_code],
        on_change=clear_results
    )

    calculate_button = st.button("Calculate ROI", use_container_width=True)
    st.caption(f"Note: Exchange rates are static. 1 USD = {local_rate:.2f} {local_code}")
    
    st.divider()
    
    # --- NEW: RESET BUTTON ---
    st.button("Reset / Clear Results", on_click=clear_results, use_container_width=True)


# --- 5. MAIN APP UI ---
st.title("🌞 Cross-Border Solar Investment Platform")
st.write("A simple tool to compare solar investment opportunities.")

# --- 6. ROI CALCULATION ---
# --- UPDATED: Handles both single and compare mode ---
if calculate_button:
    # --- ADDED SPINNER ---
    with st.spinner("Calculating your ROI..."):
        time.sleep(1) # Added a tiny delay to make the spinner visible
        
        cities_to_process = []
        if compare_mode:
            if not selected_cities:
                st.warning("Please select at least one city in Compare Mode.")
            cities_to_process = selected_cities
        elif selected_city:
            cities_to_process = [selected_city]
        else:
             st.warning("Please select a city.")

        # Common display settings
        if display_currency == "USD":
            display_rate = 1.0
            display_symbol = "$"
        else:
            display_rate = local_rate
            display_symbol = local_symbol
            
        PERFORMANCE_RATIO = 0.75 
        
        all_results = []
        
        for city_name in cities_to_process:
            city_data = df[df['City'] == city_name].iloc[0]
            
            ghi = city_data['GHI_Daily']
            tariff = city_data['Tariff_USD_kWh']
            incentive_type = city_data['Incentive_Type']
            incentive_value_usd = city_data['Incentive_Value_USD']
            policy_summary = city_data['Policy_Summary']

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
            
            # PDF is only created in single mode for simplicity
            pdf_bytes = None
            if not compare_mode:
                pdf_bytes = create_pdf(
                    country=selected_country,
                    city=city_name,
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
            
            result_dict = {
                "country": selected_country,
                "city": city_name,
                "payback": payback_period_years,
                "net_cost": display_net_cost,
                "revenue": display_revenue,
                "energy": annual_energy_kwh,
                "pdf_bytes": pdf_bytes,
                "file_name": f"Solar_Report_{selected_country}_{city_name}.pdf",
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
            all_results.append(result_dict)
        
        # Save results to session state
        if all_results:
            if compare_mode:
                st.session_state.results_data = all_results # Save as list
            else:
                st.session_state.results_data = all_results[0] # Save as single dict
    
    # --- ADDED TOAST ---
    st.toast(f"Success! Calculation complete.", icon="✅")

# --- 7. DISPLAY RESULTS (NO TABS) ---
# --- UPDATED: Handles both single (dict) and compare (list) ---

if st.session_state.results_data:
    
    # --- NEW: COMPARE MODE DISPLAY ---
    if isinstance(st.session_state.results_data, list):
        st.header("📊 Comparison Results")
        st.write(f"Based on a {system_size_kw} kW system.")
        
        df_display = pd.DataFrame(st.session_state.results_data)
        
        # Get symbol from first result (it's the same for all in compare mode)
        symbol = st.session_state.results_data[0]['symbol']
        
        # Create a clean DataFrame for display
        df_display_formatted = df_display[['city', 'payback', 'net_cost', 'revenue', 'energy']].copy()
        df_display_formatted.columns = ["City", "Payback (Years)", f"Net Cost ({symbol})", f"Annual Revenue ({symbol})", "Annual Energy (kWh)"]
        
        st.dataframe(
            df_display_formatted,
            column_config={
                "Payback (Years)": st.column_config.NumberColumn(format="%.2f"),
                f"Net Cost ({symbol})": st.column_config.NumberColumn(format=f"{symbol}%.2f"),
                f"Annual Revenue ({symbol})": st.column_config.NumberColumn(format=f"{symbol}%.2f"),
                "Annual Energy (kWh)": st.column_config.NumberColumn(format="%d kWh"),
            },
            use_container_width=True,
            hide_index=True
        )

    # --- EXISTING: SINGLE MODE DISPLAY ---
    elif isinstance(st.session_state.results_data, dict):
        res = st.session_state.results_data
        
        st.header(f"📊 Results for {res['city']}, {res['country']}")
        
        st.subheader(f"Simple Payback Period: {res['payback']:.2f} Years")
        st.progress(1.0 / max(1.0, res['payback'])) # Simple progress bar

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
            st.write(f"- **Solar Potential (GHI):** {res['ghi']} kWh/m²/day")
            st.write(f"- **Electricity Tariff (Est.):** {res['symbol']}{res['tariff']:.2f}/kWh")
            st.write(f"- **Performance Ratio:** {res['ratio'] * 100}% (Assumed)")

# --- NO RESULTS YET ---
elif not calculate_button:
    st.info("Please enter your system details in the sidebar and click 'Calculate ROI'.")

# --- 8. DATA OVERVIEW (NO TABS) ---
st.divider()
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
    ).add_to(m)
st_folium(m, width=725, height=500)