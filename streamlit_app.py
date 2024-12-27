import openai
import streamlit as st

# Load OpenAI API key from Streamlit secrets
openai.api_key = st.secrets["openai"]["api_key"]

# Configure Streamlit page
st.set_page_config(page_title="Dynamic Pane ChatGPT Dashboard", layout="wide")

# CSS for styling panes and layout
st.markdown(
    """
    <style>
        .pane {
            backdrop-filter: blur(10px);
            background-color: rgba(255, 255, 255, 0.8);
            border: 1px solid rgba(255, 255, 255, 0.4);
            border-radius: 12px;
            padding: 20px;
            margin: 10px 10px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            transition: transform 0.3s ease, opacity 0.3s ease;
        }
        .pane:hover {
            transform: scale(1.02);
            opacity: 0.95;
        }
        .query-pane {
            display: flex;
            flex-direction: column;
            align-items: center;
            margin-top: 50px;
            margin-bottom: 30px;
        }
        .response-pane {
            margin: 10px 0;
        }
        .zoomed-pane {
            padding: 40px;
            border: 2px solid rgba(0, 0, 0, 0.2);
            margin: 20px auto;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# Initialize session state to track panes and zoom state
if "responses" not in st.session_state:
    st.session_state.responses = []  # List of response panes
if "zoomed_pane" not in st.session_state:
    st.session_state.zoomed_pane = None  # Zoomed pane state

# Function to query OpenAI GPT
def query_gpt(prompt, conversation=None):
    try:
        # Prepare the conversation messages
        messages = [{"role": "system", "content": "You are a helpful assistant."}]
        if conversation:
            messages.extend(conversation)
        messages.append({"role": "user", "content": prompt})
        
        # Use the updated ChatCompletion.create method
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",  # Replace with "gpt-4" if needed
            messages=messages,
            temperature=0.7,
        )
        # Extract the assistant's reply
        return response["choices"][0]["message"]["content"]
    except Exception as e:
        return f"Error: {e}"

# Central Query Pane
if st.session_state.zoomed_pane is None:
    st.markdown("<div class='query-pane'>", unsafe_allow_html=True)
    st.title("ChatGPT Dashboard")
    prompt = st.text_area("Enter your GPT prompt:", placeholder="Type something...")
    
    if st.button("Submit"):
        if not prompt.strip():
            st.warning("Please enter a valid prompt.")
        else:
            # Query GPT and store the response
            with st.spinner("Generating response..."):
                response_content = query_gpt(prompt)
                st.session_state.responses.append({
                    "prompt": prompt,
                    "response": response_content
                })
    st.markdown("</div>", unsafe_allow_html=True)

# Display Response Panes
for i, response_data in enumerate(st.session_state.responses):
    if st.session_state.zoomed_pane is None:  # Show all panes
        st.markdown("<div class='pane response-pane'>", unsafe_allow_html=True)
        st.subheader(f"Response {i + 1}")
        st.write(response_data["response"][:300] + "...")  # Show a snippet
        if st.button(f"Zoom into Response {i + 1}", key=f"zoom_{i}"):
            st.session_state.zoomed_pane = i
        st.markdown("</div>", unsafe_allow_html=True)

# Zoomed Pane Display
if st.session_state.zoomed_pane is not None:
    index = st.session_state.zoomed_pane
    zoomed_response = st.session_state.responses[index]

    st.markdown("<div class='zoomed-pane'>", unsafe_allow_html=True)
    st.subheader("Zoomed View")
    st.write(zoomed_response["response"])

    # Refinement area
    follow_up = st.text_area("Ask a follow-up question:", placeholder="Refine your query here...")
    if st.button("Refine Response"):
        if not follow_up.strip():
            st.warning("Please enter a valid follow-up question.")
        else:
            with st.spinner("Generating refined response..."):
                new_response = query_gpt(follow_up, conversation=[
                    {"role": "user", "content": zoomed_response["prompt"]},
                    {"role": "assistant", "content": zoomed_response["response"]},
                ])
                st.session_state.responses.append({
                    "prompt": follow_up,
                    "response": new_response
                })
            st.session_state.zoomed_pane = None  # Exit zoom mode

    if st.button("Back"):
        st.session_state.zoomed_pane = None  # Exit zoom mode
    st.markdown("</div>", unsafe_allow_html=True)

