import streamlit as st
import requests
import html
from datetime import datetime
from typing import List, Dict, Optional

# Configuration
API_URL = "http://localhost:8000"

# Page configuration
st.set_page_config(
    page_title="Community Helpdesk",
    page_icon="🏘️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    * {
        font-family: 'Inter', sans-serif;
    }
    
    .main {
        padding: 1rem 2rem;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        min-height: 100vh;
    }
    
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    .main > div {
        animation: fadeIn 0.5s ease-in;
    }
    
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .header-container {
        background: white;
        padding: 2rem;
        border-radius: 20px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        margin-bottom: 2rem;
        text-align: center;
        animation: slideDown 0.6s ease-out;
    }
    
    @keyframes slideDown {
        from { opacity: 0; transform: translateY(-30px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .header-title {
        font-size: 2.5rem;
        font-weight: 700;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
    }
    
    .header-subtitle {
        font-size: 1.1rem;
        color: #666;
        font-weight: 400;
    }
    
    .empty-state {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        min-height: 350px;
        color: #999;
        animation: pulse 2s ease-in-out infinite;
    }
    
    @keyframes pulse {
        0%, 100% { opacity: 0.6; }
        50% { opacity: 1; }
    }
    
    .empty-state-icon {
        font-size: 4rem;
        margin-bottom: 1rem;
    }
    
    .empty-state-text {
        font-size: 1.2rem;
        font-weight: 500;
        margin-bottom: 0.5rem;
    }
    
    .empty-state-subtext {
        font-size: 0.95rem;
        color: #bbb;
    }
    
    .chat-message {
        padding: 1.2rem 1.5rem;
        border-radius: 15px;
        margin-bottom: 1rem;
        animation: messageSlideIn 0.4s ease-out;
        transition: all 0.3s ease;
    }
    
    @keyframes messageSlideIn {
        from { opacity: 0; transform: translateX(-20px); }
        to { opacity: 1; transform: translateX(0); }
    }
    
    .chat-message:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    }
    
    .user-message {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        margin-left: 15%;
        border-bottom-right-radius: 5px;
        animation: messageSlideInRight 0.4s ease-out;
    }
    
    @keyframes messageSlideInRight {
        from { opacity: 0; transform: translateX(20px); }
        to { opacity: 1; transform: translateX(0); }
    }
    
    .bot-message {
        background: #f8f9fa;
        color: #333;
        margin-right: 15%;
        border: 1px solid #e9ecef;
        border-bottom-left-radius: 5px;
    }
    
    .message-header {
        font-weight: 600;
        margin-bottom: 0.5rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    
    .message-content {
        line-height: 1.6;
        font-size: 0.95rem;
        white-space: pre-wrap;
        word-wrap: break-word;
    }
    
    .user-message .message-content {
        color: white;
    }
    
    .timestamp {
        font-size: 0.75rem;
        opacity: 0.7;
        margin-top: 0.5rem;
        text-align: right;
    }
    
    .confidence-badge {
        display: inline-block;
        padding: 0.3rem 0.8rem;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 600;
        margin-top: 0.5rem;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        animation: badgePulse 2s ease-in-out infinite;
    }
    
    @keyframes badgePulse {
        0%, 100% { transform: scale(1); }
        50% { transform: scale(1.05); }
    }
    
    .confidence-high {
        background: #10b981;
        color: white;
    }
    
    .confidence-medium {
        background: #f59e0b;
        color: white;
    }
    
    .confidence-low {
        background: #ef4444;
        color: white;
    }
    
    .service-card {
        background: white;
        border: 2px solid #e9ecef;
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    }
    
    .service-card:hover {
        box-shadow: 0 12px 24px rgba(102, 126, 234, 0.2);
        transform: translateY(-4px);
        border-color: #667eea;
    }
    
    .service-title {
        font-weight: 700;
        color: #667eea;
        font-size: 1.2rem;
        margin-bottom: 0.8rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
        transition: color 0.3s ease;
    }
    
    .service-card:hover .service-title {
        color: #764ba2;
    }
    
    .service-category {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 0.3rem 0.8rem;
        border-radius: 15px;
        font-size: 0.75rem;
        font-weight: 600;
        display: inline-block;
        margin-bottom: 0.8rem;
    }
    
    .service-detail {
        margin: 0.6rem 0;
        color: #555;
        display: flex;
        align-items: flex-start;
        gap: 0.5rem;
        transition: transform 0.2s ease;
    }
    
    .service-detail:hover {
        transform: translateX(5px);
    }
    
    .service-detail strong {
        color: #333;
        min-width: 100px;
    }
    
    .emergency-badge {
        background: #ef4444;
        color: white;
        padding: 0.3rem 0.8rem;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 700;
        display: inline-flex;
        align-items: center;
        gap: 0.3rem;
        animation: emergencyPulse 1.5s ease-in-out infinite;
    }
    
    @keyframes emergencyPulse {
        0%, 100% { opacity: 1; box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.7); }
        50% { opacity: 0.8; box-shadow: 0 0 0 10px rgba(239, 68, 68, 0); }
    }
    
    .stButton > button {
        width: 100%;
        border-radius: 25px;
        padding: 0.6rem 1.2rem;
        background: white;
        border: 2px solid #e9ecef;
        color: #333;
        font-weight: 500;
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        cursor: pointer;
    }
    
    .stButton > button:hover {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-color: transparent;
        transform: translateY(-3px);
        box-shadow: 0 8px 16px rgba(102, 126, 234, 0.4);
    }
    
    .stButton > button:active {
        transform: translateY(-1px);
    }
    
    .stTextInput > div > div > input {
        border-radius: 15px;
        border: 2px solid #e9ecef;
        padding: 0.8rem 1rem;
        font-size: 0.95rem;
        transition: all 0.3s ease;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #667eea;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        transform: scale(1.02);
    }
    
    .info-box {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 15px;
        margin: 1rem 0;
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
        animation: fadeIn 0.8s ease-in;
    }
    
    .info-box-title {
        font-weight: 700;
        font-size: 1.1rem;
        margin-bottom: 0.8rem;
    }
    
    .info-box-content {
        font-size: 0.9rem;
        line-height: 1.6;
    }
    
    .status-badge {
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-size: 0.9rem;
        font-weight: 600;
        margin: 0.5rem 0;
        animation: fadeIn 0.5s ease-in;
    }
    
    .status-healthy {
        background: #d1fae5;
        color: #065f46;
    }
    
    .status-error {
        background: #fee2e2;
        color: #991b1b;
    }
    
    .customer-care-box {
        background: #fef3c7;
        border-left: 4px solid #f59e0b;
        padding: 1.2rem;
        border-radius: 10px;
        margin: 1rem 0;
        transition: all 0.3s ease;
    }
    
    .customer-care-box:hover {
        transform: translateX(5px);
        box-shadow: 0 4px 12px rgba(245, 158, 11, 0.2);
    }
    
    .customer-care-title {
        font-weight: 700;
        color: #92400e;
        margin-bottom: 0.5rem;
    }
    
    .customer-care-detail {
        color: #78350f;
        font-size: 0.9rem;
        margin: 0.3rem 0;
    }
    
    .category-pill {
        display: inline-block;
        background: #f3f4f6;
        color: #374151;
        padding: 0.4rem 0.9rem;
        border-radius: 20px;
        font-size: 0.85rem;
        margin: 0.3rem;
        font-weight: 500;
        transition: all 0.3s ease;
        cursor: default;
    }
    
    .category-pill:hover {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        transform: scale(1.05);
    }
    
    ::-webkit-scrollbar {
        width: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: #f1f1f1;
        border-radius: 10px;
    }
    
    ::-webkit-scrollbar-thumb {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 10px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: #764ba2;
    }
    
    .stSpinner > div {
        border-color: #667eea !important;
        border-right-color: transparent !important;
    }
    
    .streamlit-expanderHeader {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 10px;
        padding: 0.8rem 1rem;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    .streamlit-expanderHeader:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
    }
    </style>
""", unsafe_allow_html=True)


def check_api_health() -> Dict:
    """Check if the API is healthy"""
    try:
        response = requests.get(f"{API_URL}/health", timeout=5)
        if response.status_code == 200:
            return response.json()
        return {"status": "unhealthy", "message": "API returned error status"}
    except requests.exceptions.RequestException as e:
        return {"status": "unavailable", "message": str(e)}


def send_message(question: str, location: Optional[str] = None) -> Dict:
    """Send message to chatbot API"""
    try:
        payload = {"question": question}
        if location and location.strip():
            payload["location"] = location.strip()
        
        response = requests.post(
            f"{API_URL}/chat",
            json=payload,
            timeout=60
        )
        if response.status_code == 200:
            return response.json()
        else:
            return {
                "answer": "Sorry, I encountered an error. Please try again.",
                "services": [],
                "confidence": "low",
                "service_count": 0
            }
    except requests.exceptions.Timeout:
        return {
            "answer": "Request timed out. Please try again.",
            "services": [],
            "confidence": "low",
            "service_count": 0
        }
    except requests.exceptions.RequestException as e:
        return {
            "answer": f"Connection error. Please ensure the backend is running.",
            "services": [],
            "confidence": "low",
            "service_count": 0
        }


def display_message(role: str, content: str, timestamp: str, confidence: Optional[str] = None, 
                   services: Optional[List] = None, service_count: int = 0):
    """Display a chat message with beautiful styling - FIXED to prevent HTML rendering"""
    import re
    message_class = "user-message" if role == "user" else "bot-message"
    role_emoji = "👤" if role == "user" else "🤖"
    role_name = "You" if role == "user" else "Assistant"
    
    # Remove HTML tags from content if present
    clean_content = re.sub(r'<[^>]+>', '', content)
    # Escape HTML in content to prevent rendering
    safe_content = html.escape(clean_content)
    
    message_html = f"""
    <div class="chat-message {message_class}">
        <div class="message-header">
            <span>{role_emoji}</span>
            <span>{role_name}</span>
        </div>
        <div class="message-content">{safe_content}</div>
        <div class="timestamp">{timestamp}</div>
    """
    
    message_html += "</div>"
    st.markdown(message_html, unsafe_allow_html=True)

def initialize_session_state():
    """Initialize session state variables"""
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    if 'api_status' not in st.session_state:
        st.session_state.api_status = None
    if 'user_location' not in st.session_state:
        st.session_state.user_location = ""


def main():
    """Main application function"""
    initialize_session_state()
    
    # Header
    st.markdown("""
        <div class="header-container">
            <div class="header-title">🏘️ Community Helpdesk</div>
            <div class="header-subtitle">Your AI Assistant for local services</div>
        </div>
    """, unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.markdown("### 📍 Your Location")
        location_input = st.text_input(
            "",
            value=st.session_state.user_location,
            placeholder="e.g., Adyar, T. Nagar, Velachery",
            help="Set your location for personalized results",
            label_visibility="collapsed"
        )
        st.session_state.user_location = location_input
        
        if location_input:
            st.markdown(f"""
                <div class="info-box">
                    <div class="info-box-title">📌 Current Location</div>
                    <div class="info-box-content">{html.escape(location_input)}</div>
                </div>
            """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # System Status
        st.markdown("### 🔍 System Status")
        if st.button("🔄 Check Status", use_container_width=True):
            with st.spinner("Checking..."):
                st.session_state.api_status = check_api_health()
        
        if st.session_state.api_status:
            status = st.session_state.api_status.get('status', 'unknown')
            if status == "healthy":
                total_services = st.session_state.api_status.get('total_services', 0)
                st.markdown(f"""
                    <div class="status-badge status-healthy">
                        ✅ All Systems Operational
                    </div>
                    <div style="margin-top: 1rem; font-size: 0.9rem; color: #666;">
                        📊 <strong>{total_services}</strong> services available<br>
                        🤖 Model: Llama 3.2 3B<br>
                        💾 Database: ChromaDB
                    </div>
                """, unsafe_allow_html=True)
            else:
                error_msg = html.escape(st.session_state.api_status.get('message', 'Unknown error'))
                st.markdown(f"""
                    <div class="status-badge status-error">
                        ❌ System Unavailable
                    </div>
                    <div style="margin-top: 1rem; font-size: 0.9rem; color: #ef4444;">
                        {error_msg}
                    </div>
                """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Service Categories
        st.markdown("### 📋 Available Services")
        categories = [
            ("🏥", "Healthcare"),
            ("🏛️", "Civic Services"),
            ("⚡", "Utilities"),
            ("🎓", "Education"),
            ("🚌", "Transport"),
            ("🛒", "Retail"),
            ("🔧", "Home Services"),
            ("💇", "Personal Care"),
            ("🏦", "Financial"),
            ("⚖️", "Legal"),
            ("🐾", "Pet Care"),
            ("📚", "Community")
        ]
        
        for icon, name in categories:
            st.markdown(f'<span class="category-pill">{icon} {name}</span>', unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Customer Care
        st.markdown("""
            <div class="customer-care-box">
                <div class="customer-care-title">📞 Need More Help?</div>
                <div class="customer-care-detail"><strong>Phone:</strong> 1913</div>
                <div class="customer-care-detail"><strong>Email:</strong> support@chennaicorporation.gov.in</div>
                <div class="customer-care-detail"><strong>Hours:</strong> 24/7</div>
            </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Clear Chat
        if st.button("🗑️ Clear Chat", use_container_width=True):
            st.session_state.messages = []
            st.rerun()
    
    # Main Chat Area
    st.markdown("### 💬 Ask About Services")
    
    # Quick Questions
    st.markdown("**Quick Questions:**")
    quick_questions = [
        "🏥 Nearest hospital",
        "🚨 Emergency services",
        "💊 24-hour pharmacy",
        "🏛️ Municipal office",
        "⚡ Electricity office",
        "🚌 Bus depot info"
    ]
    
    cols = st.columns(3)
    for i, question in enumerate(quick_questions):
        if cols[i % 3].button(question, key=f"quick_{i}"):
            timestamp = datetime.now().strftime("%I:%M %p")
            st.session_state.messages.append({
                "role": "user",
                "content": question,
                "timestamp": timestamp
            })
            
            with st.spinner("🔍 Searching..."):
                location_str = str(st.session_state.user_location) if st.session_state.user_location else None
                response = send_message(question, location_str)
            
            st.session_state.messages.append({
                "role": "assistant",
                "content": response['answer'],
                "timestamp": datetime.now().strftime("%I:%M %p"),
                "confidence": response.get('confidence', 'low'),
                "services": response.get('services', []),
                "service_count": response.get('service_count', 0)
            })
            st.rerun()
    
    st.markdown("---")
    
    # Chat Container
    st.markdown('<div class="chat-container">', unsafe_allow_html=True)
    
    if len(st.session_state.messages) == 0:
        st.markdown("""
            <div class="empty-state">
                <div class="empty-state-icon">💬</div>
                <div class="empty-state-text">Start a conversation</div>
            </div>
        """, unsafe_allow_html=True)
    else:
        for message in st.session_state.messages:
            display_message(
                role=message['role'],
                content=message['content'],
                timestamp=message['timestamp'],
                confidence=message.get('confidence'),
                services=message.get('services'),
                service_count=message.get('service_count', 0)
            )
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Chat Input
    user_input = st.chat_input("Ask about any service... (e.g., 'Where can I renew my gas cylinder?')")
    
    if user_input:
        timestamp = datetime.now().strftime("%I:%M %p")
        st.session_state.messages.append({
            "role": "user",
            "content": user_input,
            "timestamp": timestamp
        })
        
        with st.spinner("🔍 Searching services..."):
            location_str = str(st.session_state.user_location) if st.session_state.user_location else None
            response = send_message(user_input, location_str)
        
        st.session_state.messages.append({
            "role": "assistant",
            "content": response['answer'],
            "timestamp": datetime.now().strftime("%I:%M %p"),
            "confidence": response.get('confidence', 'low'),
            "services": response.get('services', []),
            "service_count": response.get('service_count', 0)
        })
        
        st.rerun()
    
    # Footer
    st.markdown("---")
    st.markdown("""
        <div style='text-align: center; color: white; padding: 1rem 0;'>
            <p style='margin: 0; font-size: 0.9rem;'>
                🏘️ <strong>Community Helpdesk</strong> • Built with Streamlit, FastAPI & Llama 3.2 3B
            </p>
            <p style='margin: 0.5rem 0 0 0; font-size: 0.85rem; opacity: 0.8;'>
                💡 Tip: Set your location in the sidebar for better results
            </p>
        </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()