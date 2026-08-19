import streamlit as st
from datetime import datetime
from fpdf import FPDF

# -----------------------------------------
# 1. PDF Generation Function
# -----------------------------------------
def generate_pdf(data):
    pdf = FPDF()
    pdf.add_page()
    
    # 1. Add Outer Page Border (5mm margin from page edges)
    pdf.rect(x=5, y=5, w=200, h=287)
    
    # 2. Add Company Logo
    # Make sure this matches the EXACT filename in your GitHub repository!
    logo_filename = "image(4).jpeg" 
    
    try:
        pdf.image(logo_filename, x=10, y=8, w=30)
    except Exception:
        # Prints a red warning inside the PDF if the image isn't found
        pdf.set_font("helvetica", "I", 8)
        pdf.set_text_color(255, 0, 0)
        pdf.text(10, 10, f"[Logo file '{logo_filename}' not found]")
        pdf.set_text_color(0, 0, 0)

    # Header / Title
    pdf.set_font("helvetica", "B", 18)
    pdf.cell(0, 15, "Daily Mine Inspection Report", border=False, align="C", ln=True)
    pdf.ln(5) 
    
    # Meta Data Section
    pdf.set_font("helvetica", "B", 12)
    pdf.cell(0, 8, "General Information", ln=True)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y()) 
    pdf.ln(2)
    
    pdf.set_font("helvetica", "", 11)
    pdf.cell(0, 6, f"Date of Inspection: {data['date']}", ln=True)
    pdf.cell(0, 6, f"Time Generated: {datetime.now().strftime('%H:%M:%S')}", ln=True)
    pdf.cell(0, 6, f"Inspector Name: {data['inspector']}", ln=True)
    pdf.cell(0, 6, f"Shift: {data['shift']} | Active Laborers: {data['laborers']}", ln=True)
    pdf.ln(8)
    
    # Atmospheric Monitoring Section
    pdf.set_font("helvetica", "B", 12)
    pdf.cell(0, 8, "Atmospheric Monitoring", ln=True)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(2)
    
    pdf.set_font("helvetica", "", 11)
    pdf.cell(50, 6, f"Air Velocity:", border=False)
    pdf.cell(0, 6, f"{data['velocity']} m/s", ln=True)
    
    pdf.cell(50, 6, f"Methane (CH4):", border=False)
    
    if data['ch4'] > 1.0:
        pdf.set_text_color(255, 0, 0)
    pdf.cell(0, 6, f"{data['ch4']} %", ln=True)
    pdf.set_text_color(0, 0, 0) 
    
    pdf.cell(50, 6, f"Carbon Monoxide (CO):", border=False)
    pdf.cell(0, 6, f"{data['co']} ppm", ln=True)
    pdf.ln(8)

    # Converts raw PDF bytes cleanly for Streamlit
    return bytes(pdf.output())

# -----------------------------------------
# 2. Streamlit UI & Form
# -----------------------------------------
st.set_page_config(page_title="Mine Inspection", layout="centered")
st.title("Shift Inspection Form")

with st.form("daily_inspection_form"):
    inspector_name = st.text_input("Inspector Name")
    inspection_date = st.date_input("Date", datetime.today())
    shift = st.selectbox("Shift", ["Morning", "Evening", "Night"])
    labor_count = st.number_input("Number of Active Laborers", min_value=0, step=1)
    
    st.divider()
    
    air_velocity = st.number_input("Air Velocity (m/s)", min_value=0.0, format="%.2f")
    ch4_level = st.slider("Methane (CH4) %", min_value=0.0, max_value=5.0, step=0.1)
    co_level = st.number_input("Carbon Monoxide (CO) ppm", min_value=0, step=1)

    submitted = st.form_submit_button("Submit & Generate Report")

# -----------------------------------------
# 3. Handle Submission & Download
# -----------------------------------------
if submitted:
    if not inspector_name:
        st.error("Please enter the Inspector's name.")
    else:
        report_data = {
            "inspector": inspector_name,
            "date": inspection_date.strftime("%Y-%m-%d"),
            "shift": shift,
            "laborers": labor_count,
            "velocity": air_velocity,
            "ch4": ch4_level,
            "co": co_level
        }
        
        pdf_bytes = generate_pdf(report_data)
        
        st.success("Report generated successfully!")
        
        st.download_button(
            label="📄 Download PDF Report",
            data=pdf_bytes,
            file_name=f"Inspection_{inspection_date}_{shift}.pdf",
            mime="application/pdf"
        )
