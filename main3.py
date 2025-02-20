import streamlit as st
import google.generativeai as genai
from pymongo import MongoClient

# Initialize MongoDB connection
MONGO_URI = ""  # Update with your actual MongoDB URI
db_name = ""
collection_name = ""
client = MongoClient(MONGO_URI)
db = client[db_name]
collection = db[collection_name]

# Initialize Gemini
genai.configure(api_key="")# Create Your API key using google ai studios link : - https://aistudio.google.com/app/apikey
model = genai.GenerativeModel('gemini-pro')


# Function to save financial plan to MongoDB
def save_to_mongodb(data):
    try:
        collection.insert_one(data)
        st.success("Financial plan saved successfully! ✅")
    except Exception as e:
        st.error(f"Error saving to MongoDB: {e} ❌")


# Streamlit UI
st.title("💰 Personalized Financial Chatbot ")
st.markdown("Let's plan your financial future! ✨")

# User Input Fields
name = st.text_input("Your Name: 👤")
income = st.number_input("Monthly Income (₹): 💸", min_value=0.0)
expenses = st.number_input("Monthly Expenses (₹): 🧾", min_value=0.0)
goal_description = st.text_area("Goal Description: 🎯")
goal_amount = st.number_input("Goal Amount (₹): 🎯", min_value=0.0)
timeframe = st.number_input("Timeframe (Years): 🗓️", min_value=1, step=1, format="%d")

# Button to Generate Plan
if st.button("Generate Financial Plan 🚀"):
    if not all([name, income, expenses, goal_description, goal_amount, timeframe]):
        st.error("Please fill in all the fields. ⚠️")
    else:
        with st.spinner("Generating your personalized financial plan... ⏳"):
            prompt = f"""
            You are a financial advisor. Generate a detailed financial plan for {name}:
            * Monthly Income: ₹{income}
            * Monthly Expenses: ₹{expenses}
            * Goal: {goal_description}
            * Goal Amount: ₹{goal_amount}
            * Timeframe: {timeframe} years
            """
            try:
                response = model.generate_content(prompt)
                plan = response.text
                monthly_savings_needed = goal_amount / (timeframe * 12)

                # Save data to MongoDB
                data = {
                    "name": name,
                    "income": income,
                    "expenses": expenses,
                    "goal_description": goal_description,
                    "goal_amount": goal_amount,
                    "timeframe": timeframe,
                    "monthly_saving_amount": monthly_savings_needed,
                    "financial_plan": plan
                }
                save_to_mongodb(data)

                st.subheader("Your Personalized Financial Plan: 📝")
                st.markdown(plan)
                st.markdown(f'**Required Monthly Savings:** ₹{monthly_savings_needed:.2f} 📈')
            except Exception as e:
                st.error(f"Error generating plan: {e} ❌")
