import pdfplumber
import pandas as pd
import re

def process_pdf(pdf_path):
    """
    Parses the KTU result PDF and extracts student data.
    Returns:
        tuple: (DataFrame of results, Dictionary of statistics)
    """
    data = []
    
    # KTU Register Number Format: <CollegeCode><Year><DeptCode><RollNo>
    # Example: BMC19CS046 -> BMC (College), 19 (Year), CS (Dept), 046 (RollNo)
    # We will use this to extract Dept and Year.
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            current_student = None
            current_reg_no = None
            
            for page in pdf.pages:
                text = page.extract_text()
                if not text:
                    continue
                
                lines = text.split('\n')
                for line in lines:
                    # Regex to find Register Number with groups
                    # Group 1: Full Reg No
                    # Group 2: College Code (3 chars)
                    # Group 3: Year (2 digits)
                    # Group 4: Dept Code (2-3 chars, e.g., CS, AD, CHE)
                    # Group 5: Roll No (3 digits)
                    reg_match = re.search(r'\b(([A-Z]{3})(\d{2})([A-Z]{2,3})(\d{3}))\b', line)
                    
                    if reg_match:
                        current_reg_no = reg_match.group(1)
                        year = reg_match.group(3)
                        dept = reg_match.group(4)
                        
                        # Set current student details
                        current_student = "" 
                    
                    if current_reg_no:
                        # Re-parse the current_reg_no to ensure we have the vars even if found in previous lines
                        # (Though current logic assumes reg_no is found on the same line or persists)
                        # To be safe, we re-extract from current_reg_no
                        sub_match = re.match(r'([A-Z]{3})(\d{2})([A-Z]{2,3})(\d{3})', current_reg_no)
                        if sub_match:
                            year = sub_match.group(2)
                            dept = sub_match.group(3)

                        # Look for course relationships on the line
                        # Matches: CODE(GRADE) e.g., MAT203(F) or CST203(Absent)
                        courses = re.findall(r'([A-Z]{3}\d{3})\(([\w\+]+)\)', line)
                        
                        # Filter for specific departments only: CS, CE, EE, EC, ME, AI/AD
                        # EEE corresponds to EE, ECE corresponds to EC
                        allowed_depts = {'CS', 'CE', 'EE', 'EC', 'ME', 'AI', 'AD'}
                        
                        if dept in allowed_depts:
                            for subject, grade in courses:
                                data.append({
                                    'Register No': current_reg_no,
                                    'Year': f"20{year}", # Assuming 20xx
                                    'Dept': dept,
                                    'Name': current_student,
                                    'Subject': subject,
                                    'Grade': grade
                                })

        df = pd.DataFrame(data)
        
        if df.empty:
            return None, None

        stats = generate_stats(df)
        return df, stats

    except Exception as e:
        print(f"Error processing PDF: {e}")
        return None, None

def generate_stats(df):
    """Generates statistics from a results DataFrame."""
    stats = {
        'total_students': df['Register No'].nunique(),
        'total_entries': len(df),
        'subjects': df['Subject'].unique().tolist(),
        'departments': sorted(df['Dept'].unique().tolist()),
        'dept_sub_stats': {}
    }
    
    # Structure: stats['dept_sub_stats'][dept][year][subject] = {pass: X, fail: Y}
    for dept in stats['departments']:
        stats['dept_sub_stats'][dept] = {}
        dept_df = df[df['Dept'] == dept]
        years = sorted(dept_df['Year'].unique().tolist())
        
        for year in years:
            stats['dept_sub_stats'][dept][year] = {}
            year_df = dept_df[dept_df['Year'] == year]
            dept_year_subjects = year_df['Subject'].unique().tolist()
            
            for subject in dept_year_subjects:
                subj_df = year_df[year_df['Subject'] == subject]
                fail_df = subj_df[subj_df['Grade'].isin(['F', 'FE', 'Absent'])]
                pass_count = len(subj_df) - len(fail_df)
                fail_count = len(fail_df)
                
                stats['dept_sub_stats'][dept][year][subject] = {
                    'pass': pass_count,
                    'fail': fail_count,
                    'total': len(subj_df)
                }

    # Department-wise overall stats
    stats['dept_summary'] = {}
    for dept in stats['departments']:
        dept_df = df[df['Dept'] == dept]
        stats['dept_summary'][dept] = {
            'count': dept_df['Register No'].nunique(),
            'entries': len(dept_df)
        }

    return stats
