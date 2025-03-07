import streamlit as st
import google.generativeai as genai
from pymongo import MongoClient
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()
import os
import pyttsx3
import numpy as np
from fpdf import FPDF
from gtts import gTTS
import os
import threading
import time
import speech_recognition as sr





# Session state setup
if 'is_speaking' not in st.session_state:
    st.session_state.is_speaking = False


# Modified TTS functions
def text_to_speech(text):
    if "speech_active" not in st.session_state:
        st.session_state.speech_active = False

    engine = pyttsx3.init()

    if st.session_state.speech_active:
        engine.stop()  # Stop the current speech
        st.session_state.speech_active = False
    else:
        st.session_state.speech_active = True
        engine.say(text)
        engine.runAndWait()
        st.session_state.speech_active = False
def stop_speech():
    """Stop ongoing speech"""
    if st.session_state.is_speaking:
        try:
            engine = pyttsx3.init()
            engine.stop()
            st.session_state.is_speaking = False
        except:
            pass
def speech_to_text():
    """Convert speech to text using Google's Speech Recognition"""
    r = sr.Recognizer()
    with sr.Microphone() as source:
        st.session_state.is_recording = True
        audio = r.listen(source)
        try:
            text = r.recognize_google(audio)
            st.session_state.user_audio_text = text
        except sr.UnknownValueError:
            st.error("Could not understand audio")
        except sr.RequestError as e:
            st.error(f"Speech recognition error: {str(e)}")
        finally:
            st.session_state.is_recording = False


def generate_pdf(financial_plan):
    pdf = FPDF()
    pdf.add_page()

    # Add Unicode font
    pdf.add_font('DejaVu', '', 'DejaVuSans.ttf', uni=True)
    pdf.set_font('DejaVu', '', 12)

    # Title with Rupee symbol
    pdf.cell(200, 10, txt="Financial Plan Report".encode('latin-1').decode('latin-1'), ln=True, align='C')
    pdf.ln(10)

    # Format content
    fields = [
        ("Name", financial_plan.get("name", "")),
        ("Monthly Income", f'₹{financial_plan.get("income", 0):,.2f}'),
        ("Monthly Expenses", f'₹{financial_plan.get("expenses", 0):,.2f}'),
        ("Financial Goal", financial_plan.get("goal_description", "")),
        ("Target Amount", f'₹{financial_plan.get("goal_amount", 0):,.2f}'),
        ("Adjusted Target", f'₹{financial_plan.get("adjusted_goal_amount", 0):,.2f}'),
        ("Timeframe", f'{financial_plan.get("timeframe", 0)} years'),
        ("Monthly Savings", f'₹{financial_plan.get("monthly_saving_amount", 0):,.2f}'),
        ("Plan Details", financial_plan.get("financial_plan", ""))
    ]

    for label, value in fields:
        text = f"{label}: {value}"
        # Handle Unicode characters properly
        pdf.multi_cell(0, 10, txt=text.encode('latin-1', 'replace').decode('latin-1'))
        pdf.ln(5)

    pdf_path = "financial_plan.pdf"
    pdf.output(pdf_path)
    return pdf_path


# MongoDB Configuration
MONGO_URI = "mongodb://localhost:27017"
DB_NAME = "demodb"
FINANCE_COLLECTION = "finance"
PLANS_COLLECTION = "financial"

client = MongoClient(MONGO_URI)
db = client[DB_NAME]
finance_col = db[FINANCE_COLLECTION]
plans_col = db[PLANS_COLLECTION]

# Initialize Gemini
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
model = genai.GenerativeModel('gemini-1.5-pro')

# Chat UI CSS
# Custom CSS
st.markdown("""
<style>
    /* Main background */
    body {
        background-color: #1a1a1a;
        color: #ffffff;
        font-family: Arial, sans-serif;
    }

    .chat-container {
        max-width: 800px;
        margin: auto;
        padding: 20px;
        background: #2d2d2d;
        border-radius: 10px;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
    }

    /* Bot message bubble */
    .bot-bubble {
        background: #3d3d3d;
        color: #ffffff;
        border-radius: 15px;
        padding: 15px;
        margin: 10px 0;
        max-width: 70%;
        float: left;
    }

    /* User message bubble */
    .user-bubble {
        background: #1a73e8;
        color: white;
        border-radius: 15px;
        padding: 15px;
        margin: 10px 0;
        max-width: 70%;
        float: right;
    }
    .stProgress > div > div > div > div {
    background-color: #1a73e8;
}
.st-bb { border-color: #1a73e8; }
    /* Fix markdown text visibility in bubbles */
    .bot-bubble p, .bot-bubble ul, .bot-bubble ol {
        color: #ffffff !important;
    }
    .sidebar .sidebar-content {
        background-color: #2d2d2d;

</style>
""", unsafe_allow_html=True)
with st.sidebar:
    st.markdown("""
    <h2 style="color:#1a73e8; text-align:center;">⚙️ FinFlow</h2>
    <hr style="border: 2px solid #1a73e8; border-radius: 5px; margin: 10px 0;">
    """, unsafe_allow_html=True)

    st.markdown("### 🌟 Model Capabilities")
    st.markdown("""
    - 📈 *Investment Strategies*: Optimize your portfolio for better returns.
    - 💰 *Wealth Management*: Smart allocation of funds for financial growth.
    - 🏡 *Retirement Planning*: Secure your future with a tailored savings plan.
    - 💳 *Budgeting & Saving*: Track expenses and achieve financial discipline.
    - 📊 *Risk Assessment*: Understand and manage financial risks effectively.
    - 🏦 *Debt Management*: Strategies for reducing and handling debt efficiently.
    """, unsafe_allow_html=True)

    st.markdown("""
    <hr style="border: 2px solid #1a73e8; border-radius: 5px; margin: 10px 0;">
    <h4 style="color:#1a73e8; text-align:center;">🚀 Your Financial Companion</h4>
    """, unsafe_allow_html=True)


# Session State Management
if "messages" not in st.session_state:
    st.session_state.messages = []
if "step" not in st.session_state:
    st.session_state.step = 0
if "plan_data" not in st.session_state:
    st.session_state.plan_data = {}

st.sidebar.markdown("### 🗓️ Progress Tracker")
steps = ["Profile Setup", "Goal Entry", "Plan Generation", "Finalization"]
current_step = st.session_state.get('step', 0)
for i, step in enumerate(steps):
    st.sidebar.markdown(f"{'▶️' if i == current_step else '✔️'} {step}")
def save_financial_data():
    try:
        finance_col.update_one(
            {"name": st.session_state.plan_data["name"]},
            {"$set": {
                "income": st.session_state.plan_data["income"],
                "expenses": st.session_state.plan_data["expenses"],
                "last_updated": datetime.now()
            }},
            upsert=True
        )
    except Exception as e:
        st.error(f"Error saving financial data: {e}")


def save_plan_data():
    inflation_amount = st.session_state.plan_data["goal_amount"]*(1.03)**st.session_state.plan_data["timeframe"]
    try:
        plans_col.update_one(
            {"name": st.session_state.plan_data["name"]},
            {"$set": {
                "goal": st.session_state.plan_data["goal_description"],
                "amount": st.session_state.plan_data["goal_amount"],
                "timeframe": st.session_state.plan_data["timeframe"],
                "inflation_amount":inflation_amount,
                "monthly_saving": st.session_state.plan_data["monthly_saving_amount"],
                "plan": st.session_state.plan_data["financial_plan"],
                "created_at": datetime.now()
            }},
            upsert=True
        )
    except Exception as e:
        st.error(f"Error saving plan data: {e}")


def generate_financial_plan():
    # Calculate inflation-adjusted goal amount
    inflation_rate = 0.03
    current_goal = st.session_state.plan_data['goal_amount']
    timeframe = st.session_state.plan_data['timeframe']
    adjusted_goal = current_goal * (1 + inflation_rate) ** timeframe

    # Store adjusted value
    st.session_state.plan_data['adjusted_goal_amount'] = adjusted_goal

    prompt = f"""
    Create a comprehensive financial plan considering 3% annual inflation for {st.session_state.plan_data['name']}:
    - Current Monthly Income: ₹{st.session_state.plan_data['income']:,.2f}
    - Monthly Expenses: ₹{st.session_state.plan_data['expenses']:,.2f}
    - Financial Goal: {st.session_state.plan_data['goal_description']}
    - Current Target Amount: ₹{current_goal:,.2f}
    - Inflation-adjusted Target ({timeframe} years): ₹{adjusted_goal:,.2f}
    - Timeframe: {timeframe} years

    Include:
    1. Inflation-adjusted savings strategy
    2. Investment recommendations accounting for inflation
    3. Expense optimization tips
    4. Risk management strategies
    5. Progress tracking considering inflation
    6. Alternative scenarios
    """

    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error generating plan: {str(e)}"



def display_chat():
    st.markdown('<div class="chat-container">', unsafe_allow_html=True)
    for msg in st.session_state.messages:
        if msg["type"] == "bot":
            st.markdown(f'<div class="bot-bubble">🤖 {msg["content"]}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="user-bubble">👤 {msg["content"]}</div>', unsafe_allow_html=True)
    st.markdown('</div><div class="clearfix"></div>', unsafe_allow_html=True)


# Main Application
st.title("💬 AI Financial Advisor")
display_chat()

# Conversation Flow
if st.session_state.step == 0:
    name = st.text_input("Please enter your name to begin:", key="name_input")
    if name:
        user_data = finance_col.find_one({"name": name})
        st.session_state.plan_data["name"] = name

        if user_data:
            st.session_state.plan_data.update({
                "income": user_data.get("income", 0),
                "expenses": user_data.get("expenses", 0)
            })
            st.session_state.messages.append({
                "type": "bot",
                "content": f"Welcome back {name}! Found your existing data:\n\n"
                           f"• Income: ₹{user_data.get('income', 0):,.2f}\n"
                           f"• Expenses: ₹{user_data.get('expenses', 0):,.2f}\n\n"
                           "Use these values? (yes/no)"
            })
            st.session_state.step = 1
        else:
            st.session_state.messages.append({
                "type": "bot",
                "content": f"Hello {name}! Let's start with your financial details."
            })
            st.session_state.step = 2
        st.rerun()

elif st.session_state.step == 1:
    response = st.text_input("Your response:", key="step1_res")
    if response.lower() in ["yes", "no"]:
        st.session_state.messages.append({
            "type": "user",
            "content": response.capitalize()
        })
        if response.lower() == "yes":
            save_financial_data()
            st.session_state.step = 3
        else:
            st.session_state.messages.append({
                "type": "bot",
                "content": "Let's update your financial details"
            })
            st.session_state.step = 2
        st.rerun()

elif st.session_state.step == 2:
    if "income" not in st.session_state.plan_data:
        income = st.number_input("Enter monthly income (₹):",
                                 min_value=0.0,
                                 key="income_input")
        if income:
            st.session_state.plan_data["income"] = income
            st.session_state.messages.append({
                "type": "user",
                "content": f"₹{income:,.2f}"
            })
            st.session_state.messages.append({
                "type": "bot",
                "content": "Enter monthly expenses (₹):"
            })
            st.rerun()
    else:
        expenses = st.number_input("Enter monthly expenses (₹):",
                                   min_value=0.0,
                                   key="expenses_input")
        if expenses:
            st.session_state.plan_data["expenses"] = expenses
            st.session_state.messages.append({
                "type": "user",
                "content": f"₹{expenses:,.2f}"
            })
            save_financial_data()
            st.session_state.step = 3
            st.rerun()

elif st.session_state.step == 3:
    st.session_state.messages.append({
        "type": "bot",
        "content": "What financial goal would you like to achieve? (e.g., Buy a house, Retirement)"
    })
    st.session_state.step = 4
    st.rerun()

elif st.session_state.step == 4:
    goal = st.text_input("Financial goal:", key="goal_input")
    if goal:
        st.session_state.plan_data["goal_description"] = goal
        st.session_state.messages.append({
            "type": "user",
            "content": goal
        })
        st.session_state.messages.append({
            "type": "bot",
            "content": "How much money do you need to achieve this goal? (₹)"
        })
        st.session_state.step = 5
        st.rerun()

elif st.session_state.step == 5:
    amount = st.number_input("Goal amount (₹):",
                             min_value=0.0,
                             key="amount_input")
    if amount:
        st.session_state.plan_data["goal_amount"] = amount
        st.session_state.messages.append({
            "type": "user",
            "content": f"₹{amount:,.2f}"
        })
        st.session_state.messages.append({
            "type": "bot",
            "content": "In how many years do you want to achieve this goal?"
        })
        st.session_state.step = 6
        st.rerun()

elif st.session_state.step == 6:
    timeframe = st.number_input(
        "Timeframe for Goal Achievement (in years):",
        min_value=1,
        max_value=50,
        step=1,
        help="Enter the number of years you plan to save for this goal",
        key="timeframe_input"
    )

    col1, col2 = st.columns([1, 3])
    with col1:
        if st.button("Submit Timeframe"):
            if timeframe:
                # Add validation checks
                income = st.session_state.plan_data["income"]
                expenses = st.session_state.plan_data["expenses"]

                if expenses >= income:
                    st.error("⚠️ Expenses cannot exceed income! Please review your financial details.")
                    st.session_state.step = 2
                    st.rerun()

                st.session_state.plan_data["timeframe"] = timeframe

                # Calculate inflation-adjusted monthly savings
                adjusted_goal = st.session_state.plan_data["goal_amount"] * (1.03) ** timeframe
                monthly_savings = adjusted_goal / (timeframe * 12)

                # Validation checks
                warning = ""
                if monthly_savings > income:
                    st.error("🚨 Impossible to save more than your income! Please adjust your goal or timeframe.")
                    st.session_state.step = 5
                    st.rerun()

                if monthly_savings > (income * 0.5):
                    warning = "\n\n⚠️ Warning: Monthly savings exceed 50% of your income - this may not be sustainable long-term!"

                if st.session_state.plan_data['goal_amount'] < 1000:
                    st.warning("❗ Very small goal amount - are you sure this is correct?")

                # Generate plan
                with st.spinner("Generating inflation-adjusted plan..."):
                    plan = generate_financial_plan()
                    if "Error" in plan:
                        st.error(plan)
                        st.session_state.step = 5
                        st.rerun()

                    st.session_state.plan_data["financial_plan"] = plan + warning
                    st.session_state.plan_data["monthly_saving_amount"] = monthly_savings

                    # Add buttons after plan display
                    st.session_state.messages.append({
                        "type": "bot",
                        "content": f"*Your Inflation-Adjusted Financial Plan*\n\n{plan}\n\n"
                                   f"Required Monthly Savings: ₹{monthly_savings:,.2f}\n"
                                   f"(Includes 3% annual inflation adjustment){warning}\n\n"
                                   "Are you satisfied with this plan? (yes/no)"
                    })

                    # Add PDF and TTS buttons
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("Read Aloud"):
                            text_to_speech(str(st.session_state.plan_data["financial_plan"]))
                    with col2:
                        if st.button("Download PDF"):
                            pdf_path = generate_pdf(st.session_state.plan_data)
                            st.success(f"PDF generated! [Download here]({pdf_path})")

                    save_plan_data()
                    st.session_state.step = 7
                st.rerun()


    with col2:
        st.markdown("""
        <div style="background: #3d3d3d; padding: 15px; border-radius: 10px; margin-top: 10px;">
            <h4 style="color: #1a73e8; margin-bottom: 10px;">Typical Timeframes</h4>
            <ul style="color: #ffffff;">
                <li>Short-term: 1-3 years</li>
                <li>Medium-term: 3-7 years</li>
                <li>Long-term: 7+ years</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

elif st.session_state.step == 7:
    # Display the financial plan
    plan = st.session_state.plan_data.get("financial_plan", "")
    if plan:

        # Create button columns
        col1, col2, col3, col4 = st.columns([2, 2, 1, 1])

        with col1:
            if st.session_state.is_speaking:
                if st.button("⏹️ Stop Speech"):
                    stop_speech()
            else:
                if st.button("🔊 Read Aloud"):
                    text_to_speech(str(plan))
        with col2:
            if st.button("📥 Generate PDF"):
                pdf_path = generate_pdf(st.session_state.plan_data)
                st.success(f"PDF generated! Saved to {pdf_path}")

        with col3:
            if st.button("✅ Yes"):
                st.session_state.messages.append({"type": "user", "content": "Yes"})
                st.session_state.messages.append({
                    "type": "bot",
                    "content": "🎉 Great choice! Your plan has been saved."
                })
                st.session_state.step = 7
                st.rerun()

        with col4:
            if st.button("❌ No"):
                st.session_state.messages.append({"type": "user", "content": "No"})
                st.session_state.messages.append({
                    "type": "bot",
                    "content": "What would you like to adjust?\n1. Timeframe\n2. Goal amount\n3. Both"
                })
                st.session_state.step = 8
                st.rerun()

    # Add validation checks
    monthly_savings = st.session_state.plan_data.get("monthly_saving_amount", 0)
    income = st.session_state.plan_data.get("income", 1)  # Prevent division by zero

    if monthly_savings > income:
        st.error("🚨 Impossible plan! Savings exceed income")
    elif monthly_savings > income * 0.5:
        st.warning("⚠️ Warning: Savings exceed 50% of income")

    if st.session_state.plan_data.get("goal_amount", 0) < 1000:
        st.warning("❗ Small goal amount detected - verify your target")

elif st.session_state.step == 8:
    adjustment = st.text_input("Enter choice (1-3):", key="adjustment_choice")
    if adjustment in ["1", "2", "3"]:
        st.session_state.messages.append({
            "type": "user",
            "content": adjustment
        })
        if adjustment == "1":
            st.session_state.messages.append({
                "type": "bot",
                "content": "Enter new timeframe (years):"
            })
            st.session_state.adjust_type = "timeframe"
            st.session_state.step = 9
        elif adjustment == "2":
            st.session_state.messages.append({
                "type": "bot",
                "content": "Enter new goal amount (₹):"
            })
            st.session_state.adjust_type = "amount"
            st.session_state.step = 9
        else:
            st.session_state.messages.append({
                "type": "bot",
                "content": "Enter new amount (₹) and timeframe (years) separated by comma:"
            })
            st.session_state.adjust_type = "both"
            st.session_state.step = 9
        st.rerun()

elif st.session_state.step == 9:
    new_value = st.text_input("Enter adjustment:", key="final_adjustment")
    if new_value:
        try:
            if st.session_state.adjust_type == "timeframe":
                new_timeframe = int(new_value)
                st.session_state.plan_data["timeframe"] = new_timeframe
            elif st.session_state.adjust_type == "amount":
                new_amount = float(new_value)
                st.session_state.plan_data["goal_amount"] = new_amount
            else:
                new_amount, new_timeframe = map(float, new_value.split(','))
                st.session_state.plan_data["goal_amount"] = new_amount
                st.session_state.plan_data["timeframe"] = new_timeframe

            with st.spinner("Generating your personalized financial plan..."):
                try:
                    plan = generate_financial_plan()
                    st.session_state.plan_data["financial_plan"] = plan
                    adjusted_goal = st.session_state.plan_data["goal_amount"] * (1.03) ** st.session_state.plan_data["timeframe"]
                    monthly_savings = adjusted_goal / (
                            st.session_state.plan_data["timeframe"] * 12
                    )
                    st.session_state.plan_data["monthly_saving_amount"] = monthly_savings

                    # Add buttons to main interface
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("Read Aloud 🔊"):
                            text_to_speech(str(st.session_state.plan_data["financial_plan"]))
                    with col2:
                        if st.button("Download PDF 📥"):
                            pdf_path = generate_pdf(st.session_state.plan_data)
                            st.success(f"PDF saved to {pdf_path}")

                    # Add profile tracker to sidebar
                    with st.sidebar:
                        st.subheader("Profile Progress")
                        steps = ["Personal Info", "Financial Data", "Goal Setup", "Plan Generated"]
                        current_step = 3  # Update based on your step system
                        for i, step in enumerate(steps):
                            st.write(f"{'▶️' if i == current_step else '✅'} {step}")

                    st.session_state.messages.append({
                        "type": "bot",
                        "content": f"*Your Financial Plan*\n\n{plan}\n\n"
                                   f"Required Monthly Savings: ₹{monthly_savings:,.2f}\n\n"
                                   "Are you satisfied with this plan? (yes/no)"
                    })
                    save_plan_data()
                    st.session_state.step = 7

                except Exception as e:
                    st.error(f"Error generating plan: {e}")
            st.rerun()
        except:
            st.error("Invalid input format. Please try again.")