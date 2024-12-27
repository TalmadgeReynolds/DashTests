import streamlit as st
import openai

# Configure the Streamlit page
st.set_page_config(page_title="Custom GPT Dashboard", layout="wide")

# Load OpenAI API key from Streamlit secrets
openai.api_key = st.secrets["openai"]["api_key"]

# Function to call OpenAI GPT API
def generate_gpt_response(prompt):
    try:
        response = openai.Completion.create(
            engine="text-davinci-003",  # Change to "gpt-3.5-turbo" if applicable
            prompt=prompt,
            max_tokens=150,
            temperature=0.7,
        )
        return response.choices[0].text.strip()
    except Exception as e:
        st.error(f"Error: {e}")
        return "An error occurred while processing your query."

# CSS for "glass pane" styling and UI
st.markdown(
    """
    <style>
        /* Blue Banner Styling */
        .blue-banner {
            background-color: #007BFF; /* Bootstrap primary blue */
            color: white;
            text-align: center;
            padding: 10px;
            font-size: 1.5rem;
            font-weight: bold;
            position: fixed;
            top: 0;
            width: 100%;
            z-index: 1000;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }

        /* Adjust Streamlit main content to avoid overlap with banner */
        .main-content {
            margin-top: 70px; /* Height of the banner + some spacing */
        }

        /* Glass Pane Styling */
        .pane {
            backdrop-filter: blur(10px);
            background-color: rgba(255, 255, 255, 0.8);
            border: 1px solid rgba(255, 255, 255, 0.4);
            border-radius: 12px;
            padding: 20px;
            margin: 10px 0;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            transition: transform 0.3s ease, opacity 0.3s ease;
        }
        .pane:hover {
            transform: scale(1.02);
            opacity: 0.95;
        }
        .query-pane {
            margin: auto;
            text-align: center;
            font-size: 1.2rem;
            padding: 30px;
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

# Blue Banner at the top
st.markdown("<div class='blue-banner'>Custom GPT Dashboard</div>", unsafe_allow_html=True)

# Start of the main content
st.markdown("<div class='main-content'>", unsafe_allow_html=True)

# App State to track dynamic panes
if "responses" not in st.session_state:
    st.session_state.responses = []  # Store response sections dynamically
if "zoomed_in_pane" not in st.session_state:
    st.session_state.zoomed_in_pane = None  # Track which pane is zoomed in

# Input Query Pane
if st.session_state.zoomed_in_pane is None:
    st.markdown("<div class='pane query-pane'>", unsafe_allow_html=True)
    prompt = st.text_area("Enter your GPT prompt here:", placeholder="Type something...", key="query_input")

    if st.button("Generate Response"):
        if not prompt.strip():
            st.warning("Please enter a valid prompt.")
        else:
            # Generate GPT response
            gpt_output = generate_gpt_response(prompt)

            # Simulate splitting response into sections
            response = {
                "Introduction": gpt_output[: len(gpt_output) // 3],
                "Analysis": gpt_output[len(gpt_output) // 3 : 2 * len(gpt_output) // 3],
                "Conclusion": gpt_output[2 * len(gpt_output) // 3 :],
            }
            st.session_state.responses.append(response)  # Append the GPT response
    st.markdown("</div>", unsafe_allow_html=True)

# Display Panes for Responses
for i, response in enumerate(st.session_state.responses):
    if st.session_state.zoomed_in_pane is None:  # Normal display
        for section, content in response.items():
            with st.container():
                st.markdown(f"<div class='pane'>", unsafe_allow_html=True)
                st.subheader(section)
                st.write(content)
                if st.button(f"Zoom into '{section}'", key=f"zoom_{i}_{section}"):
                    st.session_state.zoomed_in_pane = (i, section)  # Set zoom state
                st.markdown("</div>", unsafe_allow_html=True)

# Zoomed Pane Display
if st.session_state.zoomed_in_pane is not None:
    idx, zoomed_section = st.session_state.zoomed_in_pane
    zoomed_response = st.session_state.responses[idx]
    content = zoomed_response[zoomed_section]

    # Display the zoomed pane
    st.markdown("<div class='zoomed-pane'>", unsafe_allow_html=True)
    st.subheader(zoomed_section)
    st.write(content)

    # Follow-up question
    follow_up = st.text_input(f"Refine your query for '{zoomed_section}':")
    if st.button("Ask Follow-Up"):
        if follow_up.strip():
            st.write(f"Generating refined response for: '{follow_up}'...")
            # Append new content to responses
            refined_response = generate_gpt_response(follow_up)
            st.session_state.responses.append({
                "Follow-Up to " + zoomed_section: refined_response
            })
            st.session_state.zoomed_in_pane = None  # Exit zoom mode

    if st.button("Back"):
        st.session_state.zoomed_in_pane = None  # Exit zoom mode
    st.markdown("</div>", unsafe_allow_html=True)

# Close main content wrapper
st.markdown("</div>", unsafe_allow_html=True)
