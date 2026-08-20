import streamlit as st
import pandas as pd
import sqlite3
import json
import hashlib
import base64
from datetime import datetime
from fpdf import FPDF

# -----------------------------------------
# 1. Database & Security Initialization
# -----------------------------------------
DB_FILE = "mine_secure_history.db"

def hash_password(password):
    """Encrypts the password before saving to the database."""
    return hashlib.sha256(password.encode()).hexdigest()

def init_db():
    """Creates secure SQLite database tables if they don't exist."""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    # Table for Inspections
    c.execute('''CREATE TABLE IF NOT EXISTS inspections
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  date TEXT,
                  shift TEXT,
                  mine_name TEXT,
                  inspector TEXT,
                  prod_per_day REAL,
                  ch4 REAL,
                  co REAL,
                  temperature REAL,
                  full_report_json TEXT)''')
                  
    # Table for Users
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (username TEXT PRIMARY KEY,
                  password TEXT)''')
                  
    conn.commit()
    conn.close()

def create_user(username, password):
    """Registers a new user."""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hash_password(password)))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False # Username already exists
    finally:
        conn.close()

def authenticate_user(username, password):
    """Checks if username and password match."""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT password FROM users WHERE username=?", (username,))
    result = c.fetchone()
    conn.close()
    if result and result[0] == hash_password(password):
        return True
    return False

def save_report_to_db(data):
    """Saves the submitted report to the secure database."""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''INSERT INTO inspections 
                 (date, shift, mine_name, inspector, prod_per_day, ch4, co, temperature, full_report_json)
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''', 
                 (data['date'], data['shift'], data['mine_name'], data['inspector'], 
                  data['prod_per_day'], data['ch4'], data['co'], data['temperature'], 
                  json.dumps(data)))
    conn.commit()
    conn.close()

def load_analytics_data():
    """Loads specific columns for the analytics dashboard."""
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query("SELECT date, shift, prod_per_day, ch4, co, temperature FROM inspections ORDER BY date", conn)
    conn.close()
    return df

def load_history_data():
    """Loads all records for the history log."""
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query("SELECT id, date, shift, mine_name, inspector, prod_per_day, full_report_json FROM inspections ORDER BY date DESC", conn)
    conn.close()
    return df

# Initialize the database on startup
init_db()

# -----------------------------------------
# 2. Custom PDF Class & PDF Viewer
# -----------------------------------------
class MinePDF(FPDF):
    def header(self):
        self.rect(x=5, y=5, w=200, h=287)
        logo_filename = "image(4).jpeg"
        try:
            self.image(logo_filename, x=8, y=7, w=25)
        except Exception:
            pass 

        self.set_font("Times", "B", 14)
        self.cell(0, 7, "Dostan Coal Company Darra Adam Khail, KPK", align="C", ln=True)
        self.set_font("Times", "B", 11)
        self.cell(0, 5, "Daily Mine Inspection report", align="C", ln=True)
        self.ln(6)

    def footer(self):
        self.set_y(-12)
        self.set_font("Times", "I", 8)
        self.cell(0, 10, f"Page {self.page_no()}/{{nb}}", align="C")

def generate_pdf(data):
    pdf = MinePDF()
    pdf.alias_nb_pages()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    def section_header(title):
        pdf.set_font("Times", "B", 11)
        pdf.set_fill_color(230, 230, 230)
        pdf.cell(0, 6, f"  {title}", ln=True, fill=True)
        pdf.ln(2)

    def print_row(label, value, is_full_width=False):
        pdf.set_font("Times", "B", 9)
        pdf.cell(50 if not is_full_width else 60, 5, f"{label}:", border=False)
        pdf.set_font("Times", "", 9)
        pdf.cell(0, 5, str(value), ln=True)

    section_header("1. General & Inspection Details")
    print_row("Mine Name", data['mine_name'])
    print_row("Manager Permit No.", data['manager_permit'])
    print_row("Inspector Name", data['inspector'])
    print_row("Date", data['date'])
    print_row("Shift", f"{data['shift']} Shift")
    pdf.ln(3)

    section_header("2. Atmospheric & Gas Concentrations")
    print_row("Methane (CH4)", f"{data['ch4']}%")
    print_row("Carbon Monoxide (CO)", f"{data['co']} ppm")
    print_row("Hydrogen Sulfide (H2S)", f"{data['h2s']} ppm")
    print_row("Oxygen Level (O2)", f"{data['o2']}%")
    print_row("Mine Temperature", f"{data['temperature']} C")
    pdf.ln(3)

    section_header("3. Ventilation System")
    print_row("Type of Ventilation", data['vent_type'])
    print_row("Fans Condition", data['fans_cond'])
    print_row("Exhaust Condition", data['exhaust_cond'])
    print_row("Moisture Level", data['moisture'])
    print_row("Brattice Cloth Status", data['brattice'])
    print_row("Fire Stopping Condition", data['fire_stopping'])
    print_row("Spontaneous Combustion", data['spon_comb'])
    pdf.ln(3)

    section_header("4. Mechanical Equipment")
    print_row("Type of Engine", data['engine_type'])
    print_row("Engine Performance", data['engine_perf'])
    print_row("Last Oil Change Date", str(data['oil_change_date']))
    print_row("Rope Condition", data['rope_cond'])
    print_row("Gear System", data['gear_system'])
    print_row("Moving Parts Fences", data['fences_moving'])
    print_row("Drum Condition", data['drum_cond'])
    print_row("Hissa Status", data['hissa_status'])
    print_row("Cross-Section", data['cross_section'])
    pdf.ln(3)

    section_header("5. Incline Haulage & Track")
    print_row("Track Line Status", data['track_line'])
    print_row("Signals & Signal Rope", data['signals_rope'])
    print_row("Rollers & Pulleys", data['rollers_pulleys'])
    print_row("Pedestrian Ways", data['pedestrian_ways'])
    print_row("Side Fence / Rope", data['side_fence'])
    print_row("Refuge Holes", data['refuge_holes'])
    print_row("Support & Lagging", data['incline_support'])
    print_row("Direction & Grade", data['dir_grade'])
    pdf.ln(3)

    section_header("6. Coal Galleries & Production")
    print_row("Roof & Lagging Condition", data['roof_lagging'])
    print_row("Timber Support Type/Cond", data['timber_support'])
    print_row("Dust Levels", data['dust_level'])
    print_row("Goaf Areas Status", data['goaf_areas'])
    print_row("Total Working Levels", data['total_levels'])
    print_row("Production Per Day", f"{data['prod_per_day']} Tons")
    print_row("Swampy Condition", data['swampy_cond'])
    pdf.ln(3)

    section_header("7. Water Drainage System")
    print_row("Pumps & Horsepower", data['pumps_hp'])
    print_row("Drainage Amount", data['drainage_amount'])
    print_row("Delivery Pipe Diameter", data['pipe_dia'])
    print_row("Backup Pumps Available", data['drainage_backups'])
    pdf.ln(3)

    section_header("8. Electrical Systems")
    print_row("Cable Specification", data['cables_mm'])
    print_row("Earth Breakers", data['earth_breakers'])
    print_row("Floatless Relay", data['floatless_relay'])
    print_row("Buzzer Alarm", data['buzzer_alarm'])
    print_row("Zero Point Panel Board", data['panel_board'])
    print_row("Total Load", f"{data['total_load_amps']} Amps")
    print_row("Voltage at Mine", f"{data['voltage']} V")
    print_row("Earthing Status", data['earthing_status'])
    pdf.ln(3)

    section_header("9. PPE Compliance")
    print_row("Helmets Issued/Worn", data['ppe_helmets'])
    print_row("Ear Muffs / Plugs", data['ppe_ear_muffs'])
    print_row("Dust Masks", data['ppe_dust_masks'])
    print_row("Safety Shoes", data['ppe_shoes'])
    print_row("Gloves", data['ppe_gloves'])
    print_row("Safety Glasses", data['ppe_glasses'])
    pdf.ln(3)

    section_header("10. General Safety & Statutory Compliance")
    print_row("Rat Hole Mining", data['rat_hole'])
    print_row("Under-18 Minors", data['under_eighteen'])
    print_row("Crippled Workers", data['crippled_worker'])
    print_row("Drinking Water", data['drinking_water'])
    print_row("First Aid Box", data['first_aid'])
    print_row("Stretcher Available", data['stretcher'])
    print_row("Dispenser Status", data['dispenser'])
    print_row("Ambulance Status", data['ambulance'])
    print_row("Welfare Facilities", data['welfare'])
    print_row("Past Penalties", data['penalties_fines'])

    return bytes(pdf.output())

def display_pdf(pdf_bytes):
    """Embeds the PDF directly into the Streamlit app layout."""
    base64_pdf = base64.b64encode(pdf_bytes).decode('utf-8')
    pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="800" type="application/pdf"></iframe>'
    st.markdown(pdf_display, unsafe_allow_html=True)

# -----------------------------------------
# 3. Security / Login & Registration System
# -----------------------------------------
st.set_page_config(page_title="Mine Management Portal", layout="wide")

if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'current_user' not in st.session_state:
    st.session_state['current_user'] = ""

if not st.session_state['logged_in']:
    st.title("🔒 Dostan Coal Company Portal")
    
    # Create Tabs for Login and Registration
    tab_login, tab_signup = st.tabs(["Sign In", "Create Account"])
    
    with tab_login:
        st.subheader("Login to your account")
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submit_login = st.form_submit_button("Login")
            
            if submit_login:
                if authenticate_user(username, password):
                    st.session_state['logged_in'] = True
                    st.session_state['current_user'] = username
                    st.rerun()
                else:
                    st.error("Invalid Username or Password.")
                    
    with tab_signup:
        st.subheader("Register a new user")
        with st.form("signup_form"):
            new_username = st.text_input("Choose a Username")
            new_password = st.text_input("Choose a Password", type="password")
            confirm_password = st.text_input("Confirm Password", type="password")
            submit_signup = st.form_submit_button("Sign Up")
            
            if submit_signup:
                if new_password != confirm_password:
                    st.error("Passwords do not match!")
                elif len(new_password) < 6:
                    st.error("Password must be at least 6 characters long.")
                else:
                    success = create_user(new_username, new_password)
                    if success:
                        st.success("Account created successfully! You can now log in using the 'Sign In' tab.")
                    else:
                        st.error("Username already exists. Please choose a different one.")
    
    st.stop() # Stops the rest of the app from running if not logged in

# -----------------------------------------
# 4. Main Application Navigation
# -----------------------------------------
st.sidebar.title(f"Welcome, {st.session_state['current_user']}")
page = st.sidebar.radio("Navigation Menu:", ["📋 Inspection Form", "📈 Analytics Dashboard", "🗄️ Secure History"])

# Logout Button
if st.sidebar.button("Log Out"):
    st.session_state['logged_in'] = False
    st.session_state['current_user'] = ""
    st.rerun()

# -----------------------------------------
# Page 1: Inspection Form
# -----------------------------------------
if page == "📋 Inspection Form":
    st.title("Daily Underground Mine Inspection")

    with st.form("full_mine_inspection_form"):
        # Section 1
        st.header("1. General & Manager Details")
        col1, col2 = st.columns(2)
        with col1:
            mine_name = st.text_input("Mine Name", value="Dostan Coal Company")
            manager_permit = st.text_input("Manager Permit Number")
            inspector = st.text_input("Inspector Name", value=st.session_state['current_user'])
        with col2:
            inspection_date = st.date_input("Inspection Date", datetime.today())
            shift = st.selectbox("Shift", ["Morning", "Evening", "Night"])

        st.divider()

        # Section 2
        st.header("2. Gas Monitoring & Atmospheric Conditions")
        col3, col4, col5 = st.columns(3)
        with col3:
            ch4 = st.number_input("CH4 - Methane (%)", min_value=0.0, max_value=10.0, step=0.1, format="%.2f")
            co = st.number_input("CO - Carbon Monoxide (ppm)", min_value=0, step=1)
        with col4:
            h2s = st.number_input("H2S - Hydrogen Sulfide (ppm)", min_value=0, step=1)
            o2 = st.number_input("Oxygen Level (%)", min_value=0.0, max_value=25.0, value=20.9, step=0.1)
        with col5:
            temperature = st.number_input("Temperature (°C)", min_value=0.0, max_value=60.0, value=25.0, step=0.5)

        st.divider()

        # Section 3
        st.header("3. Ventilation System")
        vent_type = st.selectbox("Type of Ventilation", ["Natural", "Mechanical Exhaust", "Mechanical Forcing", "Auxiliary"])
        fans_cond = st.selectbox("Fans Condition", ["Operational", "Suboptimal", "Out of Order"])
        exhaust_cond = st.selectbox("Exhaust Condition", ["Clear / Functional", "Partially Blocked", "Failed"])
        moisture = st.selectbox("Moisture Level", ["Normal", "High / Humid", "Excessive Dry Dust"])
        spon_comb = st.text_input("Spontaneous Combustion Symptoms", value="None observed")
        fire_stopping = st.selectbox("Fire Stopping Condition", ["Intact / Sealed", "Needs Repair", "Damaged"])
        brattice = st.selectbox("Brattice Cloth", ["Installed / Good", "Torn / Damaged", "Not Installed"])

        st.divider()

        # Section 4
        st.header("4. Mechanical Equipment")
        engine_type = st.text_input("Type of Engine / Haulage Drive")
        engine_perf = st.selectbox("Engine Performance", ["Satisfactory", "Requires Maintenance", "Critical Issue"])
        oil_change_date = st.date_input("Last Mobile Oil Changing Date")
        rope_condition = st.selectbox("Rope Condition", ["Good", "Worn / Frayed", "Critical Wear"])
        gear_system = st.selectbox("Gear System", ["Smooth", "Noisy / Worn", "Faulty"])
        fences_moving = st.selectbox("Fences at Moving Parts", ["Installed & Secure", "Missing", "Damaged"])
        cross_section = st.text_input("Cross-Section Details", value="Standard")
        drum_cond = st.selectbox("Drum Condition", ["Good", "Worn", "Cracked/Damaged"])
        hissa_status = st.text_input("Hissa Status", value="Normal")

        st.divider()

        # Section 5
        st.header("5. Incline Portion")
        track_line = st.selectbox("Track Line Condition", ["Clear & Aligned", "Misaligned", "Obstructed"])
        signals_rope = st.selectbox("Signals & Signal Rope", ["Functional", "Slack / Damaged", "Inoperative"])
        rollers_pulleys = st.selectbox("Rollers & Pulleys", ["Smooth / Greased", "Seized", "Missing"])
        pedestrian_ways = st.selectbox("Pedestrian Ways", ["Clear", "Obstructed", "Unsafe"])
        side_fence = st.selectbox("Side Fence / Rope", ["Intact", "Damaged", "Missing"])
        refuge_holes = st.selectbox("Refuge Holes", ["Clean & Clear", "Blocked", "Inadequate Depth"])
        incline_support = st.selectbox("Support System & Lagging", ["Secure", "Needs Maintenance", "Critical"])
        dir_grade = st.text_input("Direction and Grade", value="As per mine plan")

        st.divider()

        # Section 6
        st.header("6. Coal Galleries & Underground Working")
        roof_lagging = st.selectbox("Lagging and Roof Condition", ["Stable / Secure", "Minor Flaking", "Unstable / Dangerous"])
        timber_support = st.text_input("Timbers Support Type & Condition", value="Props/Chocks - Good")
        dust_level = st.selectbox("Coal Dust Status", ["Suppressed / Wet", "Dry / Needs Treatment", "Excessive"])
        goaf_areas = st.selectbox("Goaf Areas Condition", ["Sealed / Safe", "Requires Inspection", "Gas Accumulation"])
        total_levels = st.number_input("Total Levels Operating", min_value=1, step=1)
        prod_per_day = st.number_input("Production Per Day (Tons)", min_value=0.0, step=0.5)
        swampy_cond = st.selectbox("Swampy Condition", ["None", "Localized Mud", "Severe Water Accumulation"])

        st.divider()

        # Section 7
        st.header("7. Water Drainage System")
        pumps_hp = st.text_input("Pumps Quantity & HP", value="1 Pump - 10 HP")
        drainage_amount = st.text_input("Drainage Rate / Amount", value="Normal flow")
        pipe_dia = st.text_input("Delivery Pipes Diameter", value='3 inches')
        drainage_backups = st.selectbox("Backups Available", ["Yes - Standby Pump Ready", "No Backup"])

        st.divider()

        # Section 8
        st.header("8. Electrical Systems")
        cables_mm = st.text_input("Cables Specification (mm)", value="16 mm SQ")
        earth_breakers = st.selectbox("Earth Breakers", ["Operational", "Tripped / Faulty", "Not Installed"])
        floatless_relay = st.selectbox("Floatless Relay", ["Functional", "Faulty", "N/A"])
        buzzer_alarm = st.selectbox("Buzzer Alarm", ["Operational", "Inoperative", "Not Installed"])
        panel_board = st.selectbox("Panel Board Condition at Zero Point", ["Sealed & Clean", "Dusty / Open", "Hazardous"])
        total_load_amps = st.number_input("Total Electrical Load (Amps)", min_value=0.0, step=1.0)
        voltage = st.number_input("Voltage at Mine (Volts)", min_value=0, value=400, step=10)
        earthing_status = st.selectbox("Earthing Provided", ["Verified Effective", "Faulty", "Missing"])

        st.divider()

        # Section 9
        st.header("9. Personal Protective Equipment (PPEs)")
        ppe_helmets = st.selectbox("Safety Helmets", ["100% Compliant", "Partial Compliance", "Non-Compliant"])
        ppe_ear_muffs = st.selectbox("Ear Muffs / Plugs", ["In Use", "Available", "Missing"])
        ppe_dust_masks = st.selectbox("Dust Masks", ["In Use", "Missing"])
        ppe_shoes = st.selectbox("Safety Shoes / Boots", ["100% Compliant", "Non-Compliant"])
        ppe_gloves = st.selectbox("Safety Gloves", ["In Use", "Missing"])
        ppe_glasses = st.selectbox("Safety Glasses", ["In Use", "N/A"])

        st.divider()

        # Section 10
        st.header("10. General Safety & Statutory Compliance")
        rat_hole = st.selectbox("Rat Hole Mining Observed", ["No / Compliant", "Yes - Violation Detected"])
        under_eighteen = st.selectbox("Under-18 Minors Present", ["No / Compliant", "Yes - Illegal Labor Detected"])
        crippled_worker = st.selectbox("Disabled / Crippled Workers Handling Hazardous Tasks", ["No", "Yes"])
        drinking_water = st.selectbox("Clean Drinking Water Available", ["Yes", "No"])
        first_aid = st.selectbox("First Aid Kit Available & Stocked", ["Yes", "No - Incomplete"])
        stretcher = st.selectbox("Stretcher Available", ["Yes", "No"])
        dispenser = st.selectbox("Dispenser Available", ["Yes", "No"])
        ambulance = st.selectbox("Ambulance Standby Status", ["Available On-call", "Stationed at Site", "Unavailable"])
        welfare = st.text_input("Welfare Facilities Condition", value="Rest shelter available")
        penalties_fines = st.text_input("Penalties & Fines Outstanding/Recent", value="Nil")

        submitted = st.form_submit_button("Submit & Save Secure Report")

    # Handle Submission
    if submitted:
        if not mine_name or not inspector or not manager_permit:
            st.error("Please fill in Mine Name, Inspector Name, and Manager Permit Number.")
        else:
            report_data = {
                "mine_name": mine_name, "manager_permit": manager_permit, "inspector": inspector,
                "date": inspection_date.strftime("%Y-%m-%d"), "shift": shift,
                "ch4": ch4, "co": co, "h2s": h2s, "o2": o2, "temperature": temperature,
                "vent_type": vent_type, "fans_cond": fans_cond, "exhaust_cond": exhaust_cond,
                "moisture": moisture, "spon_comb": spon_comb, "fire_stopping": fire_stopping, "brattice": brattice,
                "engine_type": engine_type, "engine_perf": engine_perf, "oil_change_date": oil_change_date.strftime("%Y-%m-%d"),
                "rope_cond": rope_condition, "gear_system": gear_system, "fences_moving": fences_moving,
                "cross_section": cross_section, "drum_cond": drum_cond, "hissa_status": hissa_status,
                "track_line": track_line, "signals_rope": signals_rope, "rollers_pulleys": rollers_pulleys,
                "pedestrian_ways": pedestrian_ways, "side_fence": side_fence, "refuge_holes": refuge_holes,
                "incline_support": incline_support, "dir_grade": dir_grade, "roof_lagging": roof_lagging,
                "timber_support": timber_support, "dust_level": dust_level, "goaf_areas": goaf_areas,
                "total_levels": total_levels, "prod_per_day": prod_per_day, "swampy_cond": swampy_cond,
                "pumps_hp": pumps_hp, "drainage_amount": drainage_amount, "pipe_dia": pipe_dia, "drainage_backups": drainage_backups,
                "cables_mm": cables_mm, "earth_breakers": earth_breakers, "floatless_relay": floatless_relay,
                "buzzer_alarm": buzzer_alarm, "panel_board": panel_board, "total_load_amps": total_load_amps,
                "voltage": voltage, "earthing_status": earthing_status, "ppe_helmets": ppe_helmets,
                "ppe_ear_muffs": ppe_ear_muffs, "ppe_dust_masks": ppe_dust_masks, "ppe_shoes": ppe_shoes,
                "ppe_gloves": ppe_gloves, "ppe_glasses": ppe_glasses, "rat_hole": rat_hole,
                "under_eighteen": under_eighteen, "crippled_worker": crippled_worker, "drinking_water": drinking_water,
                "first_aid": first_aid, "stretcher": stretcher, "dispenser": dispenser, "ambulance": ambulance,
                "welfare": welfare, "penalties_fines": penalties_fines
            }
            
            # Save data to Secure SQLite Database
            save_report_to_db(report_data)
            pdf_bytes = generate_pdf(report_data)
            
            st.success("✅ Report securely saved to database!")
            st.download_button(
                label="📄 Download Full PDF Report",
                data=pdf_bytes,
                file_name=f"Mine_Report_{mine_name}_{inspection_date}.pdf",
                mime="application/pdf"
            )

# -----------------------------------------
# Page 2: Analytics Dashboard
# -----------------------------------------
elif page == "📈 Analytics Dashboard":
    st.title("Mine Performance & Safety Analytics")
    
    df = load_analytics_data()
    
    if not df.empty:
        df['date'] = pd.to_datetime(df['date'])
        
        # --- Top Level Metrics ---
        st.subheader("Key Performance Indicators (Overall)")
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Inspections Logged", len(df))
        col2.metric("Total Coal Produced (Tons)", f"{df['prod_per_day'].sum():.1f}")
        col3.metric("Highest Temp Recorded (°C)", f"{df['temperature'].max():.1f}")
        
        st.divider()

        # --- Chart 1: Production ---
        st.subheader("📊 Coal Production Trend (Daily Basis)")
        prod_data = df.groupby('date')['prod_per_day'].sum()
        st.bar_chart(prod_data, color="#2E86C1")
        
        st.divider()

        # --- Chart 2: Gases Monitoring ---
        st.subheader("⚠️ Hazardous Gases Monitoring (Max Levels)")
        gas_data = df.groupby('date')[['ch4', 'co']].max()
        st.line_chart(gas_data, color=["#E74C3C", "#F1C40F"])
        
        st.divider()

        # --- Chart 3: Temperature ---
        st.subheader("🌡️ Mine Temperature Trend (°C)")
        temp_data = df.groupby('date')['temperature'].mean()
        st.line_chart(temp_data, color="#D35400")

    else:
        st.info("No data available yet. Please submit an inspection form first to generate graphs.")

# -----------------------------------------
# Page 3: Secure History Archive & PDF Viewer
# -----------------------------------------
elif page == "🗄️ Secure History":
    st.title("Secure Reports Archive")
    st.write("View past inspections and open PDF reports.")
    
    df_history = load_history_data()
    
    if not df_history.empty:
        # Show data table for reference
        st.dataframe(df_history[['date', 'shift', 'mine_name', 'inspector', 'prod_per_day']], use_container_width=True)
        
        st.divider()
        st.subheader("Open a Past Report")
        
        # Format a clean list of filenames for the user to click/select
        report_filenames = ["-- Select a File to Open --"] + df_history.apply(
            lambda x: f"Mine_Report_{x['date']}_{x['shift']}.pdf (ID: {x['id']})", axis=1
        ).tolist()
        
        selected_file = st.selectbox("Click a file name to open it:", report_filenames)
        
        if selected_file != "-- Select a File to Open --":
            # Extract ID from the selected filename text
            selected_id = int(selected_file.split("(ID: ")[1].replace(")", ""))
            
            # Fetch the specific JSON data for that report
            json_str = df_history.loc[df_history['id'] == selected_id, 'full_report_json'].values[0]
            report_data_dict = json.loads(json_str)
            
            # Recreate PDF
            recreated_pdf_bytes = generate_pdf(report_data_dict)
            
            # Download Button
            st.download_button(
                label=f"⬇️ Download {selected_file.split(' (ID:')[0]}",
                data=recreated_pdf_bytes,
                file_name=selected_file.split(" (ID:")[0],
                mime="application/pdf"
            )
            
            st.write("### Document Preview:")
            # Display PDF directly in the app
            display_pdf(recreated_pdf_bytes)

    else:
        st.info("No past reports found in the secure database.")
