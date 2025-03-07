import streamlit as st
import os
from dotenv import load_dotenv
import google.generativeai as genai
import pandas as pd
import plotly.express as px

# Load tax rules from PDF (simplified)
TAX_RULES = {
    "HRA": {
        "condition": lambda data: data["rent_paid"] > 0 and not data["hra_claimed"],
        "suggestion": lambda _: "Claim HRA exemption using rent receipts",
        "limit": "Actual HRA received, rent paid minus 10% of salary, or 50%/40%/30% of salary (metro/non-metro)"
    },
    "80C": {
        "condition": lambda data: data["investment_80c"] < 150000,
        "suggestion": lambda
            data: f"Invest ₹{150000 - data['investment_80c']} more in LIC/PPF/ELSS for full 80C benefit",
        "limit": "₹1.5 lakh"
    },
    "80D": {
        "condition": lambda data: data["health_insurance"] == 0,
        "suggestion": lambda _: "Buy health insurance to claim up to ₹25,000 deduction",
        "limit": "₹25,000 (₹50,000 for seniors)"
    },
    "87A": {
        "condition": lambda data: data["taxable_income"] <= 1200000,
        "suggestion": lambda _: "You qualify for Section 87A rebate - ₹12,500 tax relief!",
        "limit": "Taxable income ≤ ₹12L"
    }
}

TAX_GLOSSARY = {
    "80C": {
        "description": "Invest in savings plans & pay less tax!",
        "example": "Invest ₹1.5L in LIC, PPF, or ELSS to reduce taxable income",
        "limit": "₹1.5 lakh deduction"
    },
    "HRA": {
        "description": "Tax benefit for paying rent!",
        "example": "Claim deduction by submitting rent receipts to your employer",
        "limit": "Minimum of: Actual HRA, Rent paid - 10% salary, or 50%/40% salary (metro/non-metro)"
    },
    "TDS": {
        "description": "Tax Deducted at Source - prepaid tax by employer",
        "example": "₹5K deducted from ₹60K salary as advance tax payment",
        "limit": "As per income tax slabs"
    },
    "Section 87A": {
        "description": "Rebate for income under ₹12L",
        "example": "If taxable income is ₹10L, pay ₹0 tax!",
        "limit": "Available for incomes ≤ ₹12L"
    }
}

# Configure Gemini
load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
model = genai.GenerativeModel('gemini-pro')


# Custom CSS for dark mode
def set_dark_theme():
    st.markdown("""
    <style>
    .main {
        background-color: #1a1a1a;
        color: #ffffff;
    }
    .stNumberInput input, .stTextInput input {
        background-color: #2d2d2d;
        color: white;
    }
    .st-bb {
        background-color: transparent;
    }
    .st-cb {
        background-color: transparent;
    }
    .css-1aumxhk {
        background-color: #2d2d2d;
        color: white;
    }
    .st-b7 {
        color: white !important;
    }
    </style>
    """, unsafe_allow_html=True)


# Streamlit UI
st.set_page_config(page_title="Tax Guru", page_icon="💰", layout="wide")
theme = st.sidebar.toggle("🌙 Dark Mode", value=False)
if theme:
    set_dark_theme()

st.title("💰 Tax Guru - Smart Savings Assistant")
st.subheader("Your AI-Powered Tax Optimization Companion")

# Enhanced Sidebar
with st.sidebar:
    st.header("📚 Tax Dictionary")
    for term, details in TAX_GLOSSARY.items():
        with st.expander(f"What is {term}?"):
            st.markdown(f"""
            **📖 Description**: {details['description']}  
            **📝 Example**: {details['example']}  
            **🔢 Limit**: {details['limit']}
            """)
    st.markdown("---")
    st.markdown("💡 **Pro Tip**: Hover over input labels for more info!")

# User Input Form with Tooltips
with st.form("tax_info"):
    col1, col2, col3 = st.columns(3)
    with col1:
        income = st.number_input("💸 Annual Income (₹)",
                                 min_value=0,
                                 help="Total income from all sources including salary, business, etc.")
        rent_paid = st.number_input("🏠 Annual Rent Paid (₹)",
                                    min_value=0,
                                    help="Total rent paid during the financial year")
    with col2:
        investment_80c = st.number_input("📈 80C Investments (₹)",
                                         min_value=0,
                                         help="Total investments in LIC, PPF, ELSS, etc.")
        health_insurance = st.number_input("🩺 Health Insurance Premium (₹)",
                                           min_value=0,
                                           help="Include premiums for self, family, and parents")
    with col3:
        hra_claimed = st.checkbox("✅ Already claiming HRA",
                                  help="Check if you're already receiving HRA benefits")
        st.markdown("### Tax Slabs (FY 2023-24)")
        st.markdown("""
        - ₹0-3L: 0%  
        - ₹3-6L: 5%  
        - ₹6-9L: 10%  
        - ₹9-12L: 15%  
        - Above ₹12L: 30%
        """)

    submitted = st.form_submit_button("🚀 Optimize My Taxes", use_container_width=True)

if submitted:
    user_data = {
        "taxable_income": income,
        "rent_paid": rent_paid,
        "hra_claimed": hra_claimed,
        "investment_80c": investment_80c,
        "health_insurance": health_insurance
    }

    # Generate suggestions
    suggestions = []
    for section, rule in TAX_RULES.items():
        if rule["condition"](user_data):
            suggestion_text = rule["suggestion"](user_data)
            suggestions.append((section, suggestion_text, rule['limit']))

    # Visualization Section
    if suggestions:
        st.success("## 🎯 Tax Optimization Opportunities")
        cols = st.columns(2)
        with cols[0]:
            for section, text, limit in suggestions:
                st.markdown(f"""
                <div style="padding:15px;background-color:#2d2d2d;border-radius:10px;margin:10px 0">
                    <h4>💡 {section}</h4>
                    <p>{text}</p>
                    <small>💸 Limit: {limit}</small>
                </div>
                """, unsafe_allow_html=True)

        with cols[1]:
            tax_data = pd.DataFrame({
                "Category": ["80C Investments", "Health Insurance", "HRA", "Remaining Taxable"],
                "Amount": [investment_80c, health_insurance, rent_paid,
                           income - (investment_80c + health_insurance + rent_paid)]
            })
            fig = px.pie(tax_data, names="Category", values="Amount",
                         title="📊 Current Tax Breakdown",
                         color_discrete_sequence=px.colors.sequential.RdBu)
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("🎉 Great job! You're maximizing basic tax-saving options.")

st.markdown("---")
st.markdown("""
<div style="text-align:center">
    <p>📢 Note: This tool provides general guidance. Consult a CA for complex cases</p>
    <p>Made with ❤️ by Tax Guru • v2.0</p>
</div>
""", unsafe_allow_html=True)