import streamlit as st
import pandas as pd
import random
import json
import os

# -----------------------
# Utility Functions
# -----------------------

@st.cache_data
def load_data(filepath: str) -> pd.DataFrame:
    """
    Load a CSV file and clean its column names by stripping whitespace.
    """
    df = pd.read_csv(filepath)
    df.columns = df.columns.str.strip()
    return df

def load_records(json_file: str) -> dict:
    """
    Load user records from a JSON file. Initialize if the file doesn't exist.
    """
    if os.path.exists(json_file):
        with open(json_file, "r") as f:
            return json.load(f)
    else:
        return {"records": {}, "next_record_id": 1}

def save_records(records: dict, json_file: str) -> None:
    """
    Save user records to a JSON file.
    """
    with open(json_file, "w") as f:
        json.dump(records, f, indent=4)

# -----------------------
# Data Loading
# -----------------------

exercise_data = load_data("cleaned_exercise_data_refined.csv")
food_data = load_data("cleaned_food_data_refined.csv")
records_file = "records.json"
records = load_records(records_file)

# -----------------------
# Recommendation Functions
# -----------------------

def recommend_meal(health_goal: str) -> str:
    """
    Recommend a meal based on the health goal using columns from the food CSV.
    For lose weight: Calories <= 500, Total Fat <= 20, Protein >= 10.
    For gain weight: Calories >= 300.
    For maintain weight: Calories <= 600, Total Fat <= 25, Protein >= 10.
    """
    goal = health_goal.lower()
    if goal == "lose weight":
        filtered = food_data[
            (food_data['Calories'] <= 500) &
            (food_data['Total Fat'] <= 20) &
            (food_data['Protein'] >= 10)
        ]
    elif goal == "gain weight":
        filtered = food_data[food_data['Calories'] >= 300]
    elif goal == "maintain weight":
        filtered = food_data[
            (food_data['Calories'] <= 600) &
            (food_data['Total Fat'] <= 25) &
            (food_data['Protein'] >= 10)
        ]
    else:
        filtered = food_data

    if not filtered.empty:
        meal = random.choice(filtered['Food Name'].tolist())
        return f"Meal: {meal}"
    else:
        return "No suitable meal found."

def recommend_exercise(health_goal: str, bmi: float) -> str:
    """
    Recommend an exercise based on the health goal and BMI using columns from the exercise CSV.
    If the goal is lose weight and BMI >= 25, suggest exercises with 'stretch' in the Equipment Type.
    Otherwise, randomly select an exercise.
    """
    goal = health_goal.lower()
    filtered = exercise_data
    if goal == "lose weight" and bmi >= 25:
        filtered = filtered[filtered['Equipment Type'].str.contains("stretch", case=False, na=False)]
    if not filtered.empty:
        exercise = random.choice(filtered['Equipment Type'].tolist())
        return f"Exercise: {exercise}"
    else:
        return "No suitable exercise found."

def generate_plan(user: dict) -> dict:
    """
    Generate a daily plan of meal and exercise recommendations for the given number of days.
    """
    plan = {}
    days = user["Plan_Days"]
    health_goal = user["Health_Goal"]
    bmi = user["BMI"]
    for day in range(1, days + 1):
        meal = recommend_meal(health_goal)
        exercise = recommend_exercise(health_goal, bmi)
        plan[f"Day {day}"] = {
            "Meal Recommendation": meal,
            "Exercise Recommendation": exercise
        }
    return plan

# -----------------------
# Streamlit User Interface
# -----------------------

st.title("Nutrunist AI Chatbot")

st.markdown("Welcome to Nutrunist AI! Please enter your details below:")

with st.form("user_details_form"):
    name = st.text_input("Name")
    age = st.number_input("Age", min_value=1, step=1)
    gender = st.selectbox("Gender", options=["Male", "Female", "Other"])
    height = st.number_input("Height (in cm)", min_value=0.0, step=0.1)
    weight = st.number_input("Weight (in kg)", min_value=0.0, step=0.1)
    health_goal = st.selectbox("Desired Health Goal", options=["lose weight", "gain weight", "maintain weight"])
    plan_days = st.number_input("For how many days do you want a plan?", min_value=1, step=1)
    submit_button = st.form_submit_button("Submit")

if submit_button:
    if height > 0:
        bmi = weight / ((height / 100) ** 2)
        bmi = round(bmi, 2)
    else:
        bmi = 0
    st.write(f"Calculated BMI: **{bmi}**")

    # Create a user record with consistent keys
    user_record = {
        "Name": name,
        "Age": age,
        "Gender": gender,
        "Height_cm": height,
        "Weight_kg": weight,
        "BMI": bmi,
        "Health_Goal": health_goal,
        "Plan_Days": plan_days
    }
    
    # Save the user record into records.json
    record_id = records["next_record_id"]
    records["records"][str(record_id)] = user_record
    records["next_record_id"] += 1
    save_records(records, records_file)
    st.success("User data saved successfully!")
    
    # Generate and display the personalized plan
    plan = generate_plan(user_record)
    st.subheader("Your Personalized Plan")
    for day, details in plan.items():
        st.markdown(f"**{day}:**")
        st.write(f"- {details['Meal Recommendation']}")
        st.write(f"- {details['Exercise Recommendation']}")
