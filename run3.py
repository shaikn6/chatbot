import streamlit as st
import pandas as pd
import random
import json
import os
import requests

# Set your Groqcloud API key (use an environment variable for security)
GROQCLOUD_API_KEY = os.getenv("GROQCLOUD_API_KEY", "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")

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
# Recommendation Functions (ML Placeholder)
# -----------------------

def recommend_meal_ml(user_record: dict) -> str:
    """
    Recommend a meal using a simple filtering approach.
    Later, you can replace this with a trained ML model.
    """
    health_goal = user_record["Health_Goal"].lower()
    if health_goal == "lose weight":
        filtered = food_data[
            (food_data['Calories'] <= 500) &
            (food_data['Total Fat'] <= 20) &
            (food_data['Protein'] >= 10)
        ]
    elif health_goal == "gain weight":
        filtered = food_data[food_data['Calories'] >= 300]
    elif health_goal == "maintain weight":
        filtered = food_data[
            (food_data['Calories'] <= 600) &
            (food_data['Total Fat'] <= 25) &
            (food_data['Protein'] >= 10)
        ]
    else:
        filtered = food_data

    if not filtered.empty:
        return f"Meal: {random.choice(filtered['Food Name'].tolist())}"
    else:
        return "No suitable meal found."

def recommend_exercise_ml(user_record: dict) -> str:
    """
    Recommend an exercise using a simple filtering approach.
    Later, you can replace this with a more sophisticated model.
    """
    health_goal = user_record["Health_Goal"].lower()
    bmi = user_record["BMI"]
    filtered = exercise_data
    if health_goal == "lose weight" and bmi >= 25:
        filtered = filtered[filtered['Equipment Type'].str.contains("stretch", case=False, na=False)]
    if not filtered.empty:
        return f"Exercise: {random.choice(filtered['Equipment Type'].tolist())}"
    else:
        return "No suitable exercise found."

def generate_plan_ml(user_record: dict) -> dict:
    """
    Generate a daily plan using ML-based recommendation functions.
    """
    plan = {}
    days = user_record["Plan_Days"]
    for day in range(1, days + 1):
        meal = recommend_meal_ml(user_record)
        exercise = recommend_exercise_ml(user_record)
        plan[f"Day {day}"] = {
            "Meal Recommendation": meal,
            "Exercise Recommendation": exercise
        }
    return plan

# -----------------------
# Advanced Chatbot Functions (Using Groqcloud)
# -----------------------

def get_ai_response(user_message: str, context: list) -> str:
    """
    Generate a dynamic response using Groqcloud's API.
    (This is a simulated integration; adjust the endpoint and payload as needed.)
    """
    payload = {
        "model": "groq-1",  # Hypothetical model identifier; replace as needed.
        "messages": context + [{"role": "user", "content": user_message}],
        "max_tokens": 150,
        "temperature": 0.7,
    }
    headers = {
        "Authorization": f"Bearer {GROQCLOUD_API_KEY}",
        "Content-Type": "application/json"
    }
    try:
        response = requests.post("https://api.groqcloud.com/v1/chat", headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
        # Assuming Groqcloud returns a structure similar to OpenAI:
        return data["choices"][0]["message"]["content"].strip()
    except Exception as e:
        return f"Error: {str(e)}"

# Initialize conversation state in session_state if not present.
if "chat_history" not in st.session_state:
    st.session_state["chat_history"] = []
if "conversation_context" not in st.session_state:
    st.session_state["conversation_context"] = []
if "chat_active" not in st.session_state:
    st.session_state["chat_active"] = True

def update_dynamic_chat(user_message: str):
    """
    Update conversation context and chat history.
    Ends conversation if user types 'exit' or 'end'.
    """
    msg = user_message.lower().strip()
    if msg in ["exit", "end"]:
        st.session_state.chat_history.append({
            "sender": "Bot",
            "message": "Conversation ended. Thank you for chatting!"
        })
        st.session_state.chat_active = False
        return
    # Append user's message to context.
    st.session_state.conversation_context.append({
        "role": "user", "content": user_message
    })
    # Get AI response via Groqcloud's API.
    response = get_ai_response(user_message, st.session_state.conversation_context)
    # Append the response to the conversation context and history.
    st.session_state.conversation_context.append({
        "role": "assistant", "content": response
    })
    st.session_state.chat_history.append({
        "sender": "User", "message": user_message
    })
    st.session_state.chat_history.append({
        "sender": "Bot", "message": response
    })

# -----------------------
# Streamlit User Interface
# -----------------------

st.title("Nutrunist AI Chatbot")

# Sidebar: Advanced Dynamic Chat
st.sidebar.header("Live Chat with Nutrunist AI")
if st.session_state.chat_active:
    chat_input = st.sidebar.text_input("Type your message here:", key="chat_input")
    if st.sidebar.button("Send", key="send_btn"):
        if chat_input:
            update_dynamic_chat(chat_input)
            st.experimental_rerun()  # Rerun to update chat display
else:
    st.sidebar.write("Chat has ended. Refresh the page to restart.")

st.sidebar.markdown("### Conversation")
for chat in st.session_state.chat_history:
    if chat["sender"] == "User":
        st.sidebar.markdown(f"**You:** {chat['message']}")
    else:
        st.sidebar.markdown(f"**Nutrunist AI:** {chat['message']}")

# Main Area: User Details & Plan Generation
st.markdown("## Enter Your Details for Your Personalized Plan")

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
    
    # Save the record.
    record_id = records["next_record_id"]
    records["records"][str(record_id)] = user_record
    records["next_record_id"] += 1
    save_records(records, records_file)
    st.success("User data saved successfully!")
    
    # Generate plan (using ML placeholder functions).
    plan = generate_plan_ml(user_record)
    st.subheader("Your Personalized Plan")
    for day, details in plan.items():
        st.markdown(f"**{day}:**")
        st.write(f"- {details['Meal Recommendation']}")
        st.write(f"- {details['Exercise Recommendation']}")
