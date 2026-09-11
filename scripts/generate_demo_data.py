import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os

np.random.seed(42)

def generate_demo_data(num_projects=1000):
    states = ["Maharashtra", "Bihar", "West Bengal", "Uttar Pradesh", "Kerala"]
    categories = ["Roads", "Drinking Water", "Education", "Health", "Sanitation"]
    agencies = ["Gram Panchayat", "PWD", "Municipal Corporation", "Zila Parishad"]
    vendors = ["ABC Construction", "XYZ Builders", "MNO Contractors", "PQR Engineering"]
    statuses = ["Completed", "In Progress", "Not Started", "Delayed"]
    
    # Realistic Indian MP names (49 representatives across states)
    mp_names = [
        "Narayan Rane", "Supriya Sule", "Sanjay Raut", "Piyush Goyal", "Nana Patole",
        "Lalu Prasad Yadav", "Nitish Kumar", "Ram Vilas Paswan", "Chirag Paswan", "Pappu Yadav",
        "Mamata Banerjee", "Sudip Bandyopadhyay", "Mimi Chakraborty", "Nusrat Jahan", "Sougata Ray",
        "Mulayam Singh Yadav", "Akhilesh Yadav", "Dimple Yadav", "Ram Gopal Yadav", "Jaya Bachchan",
        "Shashi Tharoor", "K. C. Venugopal", "A. K. Antony", "V. Muraleedharan", "Rajmohan Unnithan",
        "Rajnath Singh", "Smriti Irani", "Uma Bharti", "Yogi Adityanath", "Hema Malini",
        "Amit Shah", "Anandiben Patel", "Hardik Patel", "Paresh Rawal", "Devusinh Chauhan",
        "Sharad Pawar", "Uddhav Thackeray", "Priyanka Chaturvedi", "Milind Deora", "Anil Desai",
        "Manoj Tiwari", "Gautam Gambhir", "Ramvir Singh Bidhuri", "Parvesh Verma", "Hans Raj Hans",
        "Mallikarjun Kharge", "Sonia Gandhi", "Rahul Gandhi", "Priyanka Gandhi", "P. Chidambaram",
    ]
    constituencies = [
        "Mumbai North", "Baramati", "Mumbai North West", "Mumbai North East", "Nagpur",
        "Saran", "Nalanda", "Hajipur", "Jamui", "Madhepura",
        "Kolkata South", "Kolkata North", "Jadavpur", "Basirhat", "Dum Dum",
        "Mainpuri", "Azamgarh", "Firozabad", "Sambhal", "Amroha",
        "Thiruvananthapuram", "Alappuzha", "Pathanamthitta", "Thrissur", "Kasaragod",
        "Lucknow", "Amethi", "Jhansi", "Gorakhpur", "Mathura",
        "Gandhinagar", "Anand", "Jamnagar", "Ahmedabad East", "Amreli",
        "Satara", "Mumbai South", "Mumbai South Central", "Mumbai North Central", "Mumbai East",
        "North East Delhi", "East Delhi", "South Delhi", "West Delhi", "North West Delhi",
        "Gulbarga", "Wayanad", "Rae Bareli", "Varanasi", "Sivaganga",
    ]
    districts = [
        "Mumbai", "Pune", "Nashik", "Aurangabad", "Nagpur",
        "Saran", "Nalanda", "Vaishali", "Jamui", "Madhepura",
        "Kolkata", "North 24 Parganas", "South 24 Parganas", "Nadia", "Howrah",
        "Mainpuri", "Azamgarh", "Firozabad", "Sambhal", "Amroha",
        "Thiruvananthapuram", "Alappuzha", "Pathanamthitta", "Thrissur", "Kasaragod",
        "Lucknow", "Amethi", "Jhansi", "Gorakhpur", "Mathura",
        "Gandhinagar", "Anand", "Jamnagar", "Ahmedabad", "Amreli",
        "Satara", "Mumbai", "Mumbai", "Mumbai", "Mumbai",
        "East Delhi", "East Delhi", "South Delhi", "West Delhi", "North West Delhi",
        "Gulbarga", "Wayanad", "Rae Bareli", "Varanasi", "Sivaganga",
    ]
    
    data = []
    for i in range(num_projects):
        mp_idx = np.random.randint(0, len(mp_names))
        mp_name = mp_names[mp_idx]
        constituency = constituencies[mp_idx]
        district = districts[mp_idx]
        state = np.random.choice(states)

        category = np.random.choice(categories)
        work_name = f"Construction of {category} at location {np.random.randint(1, 1000)}"
        
        rec_date = datetime(2023, 1, 1) + timedelta(days=np.random.randint(0, 365))
        rec_amount = round(np.random.uniform(500000, 20000000), 2)
        
        # Some works might not be sanctioned
        is_sanctioned = np.random.random() > 0.1
        sanc_date = rec_date + timedelta(days=np.random.randint(10, 100)) if is_sanctioned else pd.NaT
        sanc_amount = round(rec_amount * np.random.uniform(0.9, 1.1), 2) if is_sanctioned else None
        
        # Inject anomalies
        anomaly_type = np.random.choice(["None", "Cost Overrun", "Delay", "Under Utilization"], p=[0.85, 0.05, 0.05, 0.05])
        
        status = np.random.choice(statuses)
        amount_spent = 0
        
        if is_sanctioned:
            if anomaly_type == "Cost Overrun":
                amount_spent = round(sanc_amount * np.random.uniform(1.3, 1.8), 2)
            elif anomaly_type == "Under Utilization":
                amount_spent = round(sanc_amount * np.random.uniform(0.0, 0.1), 2)
                sanc_date = sanc_date - timedelta(days=300) # Ensure it's old enough
                status = "In Progress"
            else:
                # Normal spending
                if status == "Completed":
                    amount_spent = round(sanc_amount * np.random.uniform(0.95, 1.05), 2)
                elif status == "In Progress":
                    amount_spent = round(sanc_amount * np.random.uniform(0.2, 0.8), 2)
                    
            if anomaly_type == "Delay":
                sanc_date = sanc_date - timedelta(days=400)
                status = "In Progress"
                
        # Trust/Society compliance anomaly
        agency = np.random.choice(agencies)
        if np.random.random() < 0.02:
            agency = "Trust"
            sanc_amount = 15000000 # 1.5 Cr, over the 1 Cr cap
        
        data.append({
            "unique_work_number": f"W-{i+1000}",
            "mp_name": mp_name,
            "state": state,
            "district": district,
            "constituency": constituency,
            "work_name": work_name,
            "work_category": category,
            "recommended_amount": rec_amount,
            "date_recommended": rec_date.strftime("%Y-%m-%d"),
            "sanction_amount": sanc_amount,
            "sanction_date": sanc_date.strftime("%Y-%m-%d") if not pd.isnull(sanc_date) else None,
            "work_status": status,
            "implementing_agency": agency,
            "amount_spent": amount_spent if is_sanctioned else None,
            "vendor_name": np.random.choice(vendors) if amount_spent > 0 else None
        })

    df = pd.DataFrame(data)
    
    # Split into required CSVs
    rec_df = df[["unique_work_number", "mp_name", "state", "constituency", "work_name", "work_category", "recommended_amount", "date_recommended", "implementing_agency"]]
    sanc_df = df.dropna(subset=["sanction_amount"])[["unique_work_number", "sanction_amount", "sanction_date", "work_status", "implementing_agency", "district"]]
    
    # Payments (simplified: 1 row per project if amount_spent > 0)
    pay_df = df[df["amount_spent"] > 0][["unique_work_number", "amount_spent", "vendor_name"]].copy()
    pay_df["payment_date"] = "2024-01-01"
    pay_df["payment_status"] = "Success"
    
    # Inject Duplicate Anomaly
    # Copy a row and change unique_work_number but keep work_name, district, etc.
    dup_row = rec_df.iloc[0].copy()
    dup_row["unique_work_number"] = "W-9999"
    rec_df = pd.concat([rec_df, pd.DataFrame([dup_row])], ignore_index=True)
    
    dup_sanc = sanc_df.iloc[0].copy()
    dup_sanc["unique_work_number"] = "W-9999"
    sanc_df = pd.concat([sanc_df, pd.DataFrame([dup_sanc])], ignore_index=True)
    
    dup_pay = pay_df.iloc[0].copy()
    dup_pay["unique_work_number"] = "W-9999"
    pay_df = pd.concat([pay_df, pd.DataFrame([dup_pay])], ignore_index=True)

    rec_df.to_csv("data/raw/recommended_works.csv", index=False)
    sanc_df.to_csv("data/raw/sanctioned_works.csv", index=False)
    pay_df.to_csv("data/raw/payments.csv", index=False)
    
    print("Generated synthetic dataset in data/raw/")

if __name__ == "__main__":
    generate_demo_data(1000)
