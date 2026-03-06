import streamlit as st
import pandas as pd
import zlib
import base64

# Set page configuration
st.set_page_config(page_title="Competency Tracker", layout="wide")

# Helper functions for encoding and decoding the status string
def encode_status(raw_status: str) -> str:
    """Compresses and base64 encodes the raw string."""
    compressed = zlib.compress(raw_status.encode('utf-8'))
    return base64.urlsafe_b64encode(compressed).decode('ascii')

def decode_status(short_code: str) -> str:
    """Decodes and decompresses the short code back to the raw string."""
    try:
        # Pad the string if equals signs were accidentally truncated
        padded = short_code + '=' * (-len(short_code) % 4)
        decoded = base64.urlsafe_b64decode(padded.encode('ascii'))
        return zlib.decompress(decoded).decode('utf-8')
    except Exception:
        return ""

st.title("🎓 Student Competency Status Dashboard")
st.markdown("""
This dashboard helps you understand your progress based on your competency rubric. 
Enter your short status code below to instantly load your detailed rubric view.
""")

# Categorize LOs for visual grouping (columns remain fixed)
lo_groups = {
    "Domain 1 (Orange)": ["LO1.1", "LO1.2", "LO1.3", "LO1.4", "LO1.5", "LO1.6", "LO1.7"],
    "Domain 2 (Blue)": ["LO2.1", "LO2.2", "LO2.3"],
    "Domain 3 (Yellow)": ["LO3.1", "LO3.2", "LO3.3"]
}

all_los = lo_groups["Domain 1 (Orange)"] + lo_groups["Domain 2 (Blue)"] + lo_groups["Domain 3 (Yellow)"]
num_los = len(all_los)

# Default raw tokenized code matching the exact state of the provided image
default_raw_code = (
    "PIC 1:1000000000000|"
    "PIC 2:2000020000200|"
    "PIC 3:2000020220000|"
    "PAH 1:2200000220000|"
    "PAH 2:0200022220200|"
    "PAH 3:0200022220200|"
    "PIL 1:0202000220202|"
    "PIL 2:0202022220222|"
    "PIL 3:0333033330333|"
    "Project 1:2222220222222|"
    "Project 2:2022202220222"
)
# Generate the short version automatically for the default input
default_short_code = encode_status(default_raw_code)

st.subheader("🔑 Enter Status Code")
st.write("Input the short status code provided by your instructor.")

status_code = st.text_area("Student Status Code:", value=default_short_code, height=68)

# Decode the status code
raw_status_code = decode_status(status_code.strip())

# Parse and validate the decoded status
parsed_assessments = []
is_valid_code = True
error_message = ""

if not status_code.strip():
    is_valid_code = False
    error_message = "Status code cannot be empty."
elif not raw_status_code:
    is_valid_code = False
    error_message = "Invalid status code. Please ensure you copied the entire string correctly."
else:
    assessment_blocks = raw_status_code.strip().split('|')
    for block in assessment_blocks:
        if not block.strip():
            continue # Skip empty blocks caused by trailing pipes
            
        if ':' not in block:
            is_valid_code = False
            error_message = "Corrupted format inside the decoded string. Missing ':' separator."
            break
        
        name, code = block.split(':', 1)
        name = name.strip()
        code = code.strip()
        
        if len(code) != num_los:
            is_valid_code = False
            error_message = f"Decoded assessment '{name}' must have exactly {num_los} digits, but got {len(code)}."
            break
            
        if not all(c in '0123' for c in code):
            is_valid_code = False
            error_message = f"Decoded assessment '{name}' contains invalid characters."
            break
            
        parsed_assessments.append((name, code))

if not is_valid_code:
    st.error(f"⚠️ {error_message}")
elif len(parsed_assessments) == 0:
    st.warning("Please enter at least one valid assessment block.")

# Build a tabular view to replicate the original rubric look
st.header("📋 Detailed Rubric View")
st.markdown("""
**Legend:**
* ☑️ **Assessed & Achieved:** The student demonstrated mastery of the LO in this assessment.
* ◻️ **Assessed but Not Achieved:** The LO was evaluated, but the student hasn't mastered it yet.
* ⏳ **Pending Assessment:** The LO will be evaluated in this assessment, but it has not been graded yet.
* *(Blank)* **Not Assessed:** This LO is not covered in this particular assessment.
""")

matrix_data = []
lo_totals = {lo: 0 for lo in all_los}

# Build the grid using the parsed assessments
if is_valid_code and len(parsed_assessments) > 0:
    for name, code in parsed_assessments:
        row = {"Assessment": name}
        for i, lo in enumerate(all_los):
            cell_state = code[i]
            
            if cell_state == '2':
                row[lo] = "☑️"
                lo_totals[lo] += 1
            elif cell_state == '1':
                row[lo] = "◻️"
            elif cell_state == '3':
                row[lo] = "⏳"
            else:
                row[lo] = ""
                
        matrix_data.append(row)

    # Append the totals row at the bottom
    totals_row = {"Assessment": "🏆 TOTAL ACHIEVED"}
    for lo in all_los:
        totals_row[lo] = f"⭐ {lo_totals[lo]}"
    matrix_data.append(totals_row)

    df = pd.DataFrame(matrix_data)
    st.dataframe(df, use_container_width=True, hide_index=True)

st.write("---")

# Instructor code generator
with st.expander("🛠️ Instructor Tools: Generate a Short Code"):
    st.write("Enter the long, raw format (`Assessment Name:Quaternary|...`) below to generate a short, encrypted code to give to a student.")
    st.markdown(f"*(Reminder: Quaternary requires {num_los} digits of `0`, `1`, `2`, or `3` after each colon)*")
    
    instructor_input = st.text_area("Raw Quaternary Format:", value=default_raw_code, height=150)
    
    if instructor_input.strip():
        try:
            new_short_code = encode_status(instructor_input.strip())
            st.success("✅ Short Code Generated Successfully!")
            st.code(new_short_code, language="text")
        except Exception as e:
            st.error(f"Failed to generate code: {e}")
