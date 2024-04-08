import logging
import streamlit as st


#from langchain.adapters import openai as lc_openai
from PIL import Image, ImageEnhance
import time
import json
import requests
import base64


from openai import OpenAI, OpenAIError

api_key = st.secrets["OPENAI_API_KEY"]
client = OpenAI(api_key=api_key)

assistant_id = "asst_gMCXcwX4afLZWEjKJ2dn7x2c"
if 'a' in st.query_params:
    assistant_id = st.query_params['a']

assistant_name = "MiaAI Education"
if 'n' in st.query_params:
    assistant_name = assistant_name + " - " + st.query_params['n']


logging.basicConfig(level=logging.INFO)

# Streamlit Page Configuration
st.set_page_config(
    page_title=assistant_name,
    page_icon="imgs/avatar_streamly.png",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "Get help": "https://github.com/AdieLaine/Streamly",
        "Report a bug": "https://github.com/AdieLaine/Streamly",
        "About": """
            ## Mia AI Education
            
            Created by Maria Sosai, Ioana Buduru si Raisa Cornea.
            
            Technovation Girls 2024
        """
    }
)

# Streamlit Updates and Expanders
st.title(assistant_name)


@st.cache_data(show_spinner=False)
def load_and_enhance_image(image_path, enhance=False):
    """
    Load and optionally enhance an image.

    Parameters:
    - image_path: str, path of the image
    - enhance: bool, whether to enhance the image or not

    Returns:
    - img: PIL.Image.Image, (enhanced) image
    """
    img = Image.open(image_path)
    if enhance:
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(1.8)
    return img

@st.cache_data(show_spinner=False)
def get_latest_update_from_json(keyword, latest_updates):
    """
    Fetch the latest Streamlit update based on a keyword.

    Parameters:
        keyword (str): The keyword to search for in the Streamlit updates.
        latest_updates (dict): The latest Streamlit updates data.

    Returns:
        str: The latest update related to the keyword, or a message if no update is found.
    """
    for section in ["Highlights", "Notable Changes", "Other Changes"]:
        for sub_key, sub_value in latest_updates.get(section, {}).items():
            for key, value in sub_value.items():
                if keyword.lower() in key.lower() or keyword.lower() in value.lower():
                    return f"Section: {section}\nSub-Category: {sub_key}\n{key}: {value}"

    return "No updates found for the specified keyword."

def img_to_base64(image_path):
    """Convert image to base64"""
    with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()

@st.cache_data(show_spinner=False)
def on_chat_submit(chat_input):
    
    user_input = chat_input.strip().lower()

    # Append user's query to conversation history
    st.session_state.conversation_history.append({"role": "user", "content": user_input})

    try:

        # Generate response
        assistant_message = generate_response(user_message=user_input)
        
        # Append assistant's reply to the conversation history
        st.session_state.conversation_history.append({"role": "assistant", "content": assistant_message})

        # Update the Streamlit chat history
        if "history" in st.session_state:
            st.session_state.history.append({"role": "user", "content": user_input})
            st.session_state.history.append({"role": "assistant", "content": assistant_message})

    except OpenAIError as e:
        logging.error(f"Error occurred: {e}")
        error_message = f"OpenAI Error: {str(e)}"
        st.error(error_message)
        #st.session_state.history.append({"role": "assistant", "content": error_message})
    
def main():
    """
    Display Streamlit updates and handle the chat interface.
    """
    # Initialize session state variables for chat history and conversation history
    if 'history' not in st.session_state:
        st.session_state.history = []
    if 'conversation_history' not in st.session_state:
        st.session_state.conversation_history = []
    if 'thread_id' not in st.session_state:
        st.session_state.thread_id = None
    
    # Inject custom CSS for glowing border effect
    st.markdown(
        """
        <style>
        .cover-glow {
            width: 100%;
            height: auto;
            padding: 3px;
            box-shadow: 
                0 0 5px #330000,
                0 0 10px #660000,
                0 0 15px #990000,
                0 0 20px #CC0000,
                0 0 25px #FF0000,
                0 0 30px #FF3333,
                0 0 35px #FF6666;
            position: relative;
            z-index: -1;
            border-radius: 30px;  /* Rounded corners */
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # Function to convert image to base64
    def img_to_base64(image_path):
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()

    # Load and display sidebar image with glowing effect
    img_path = "imgs/sidebar_streamly_avatar.png"
    img_base64 = img_to_base64(img_path)
    st.sidebar.markdown(
        f'<img src="data:image/png;base64,{img_base64}" class="cover-glow">',
        unsafe_allow_html=True,
    )
    st.sidebar.markdown("---")
    
    # Sidebar for Mode Selection
    mode = st.sidebar.radio("Select Mode:", options=["Latest Updates", "Chat with Streamly"], index=1)
    use_langchain = st.sidebar.checkbox("Use LangChain OpenAI Adapter 🦜️🔗 ", value=False)
    st.sidebar.markdown("---")
    # Toggle checkbox in the sidebar for basic interactions
    show_basic_info = st.sidebar.toggle("Show Basic Interactions", value=True)

    # Display the st.info box if the checkbox is checked
    if show_basic_info:
        st.sidebar.markdown("""
        ### Basic Interactions
        - **Ask About Streamlit**: Type your questions about Streamlit's latest updates, features, or issues.
        - **Search for Code**: Use keywords like 'code example', 'syntax', or 'how-to' to get relevant code snippets.
        - **Navigate Updates**: Switch to 'Updates' mode to browse the latest Streamlit updates in detail.
        """)

    # Add another toggle checkbox in the sidebar for advanced interactions
    show_advanced_info = st.sidebar.toggle("Show Advanced Interactions", value=False)

    # Display the st.info box if the checkbox is checked
    if show_advanced_info:
        st.sidebar.markdown("""
        ### Advanced Interactions
        - **Generate an App**: Use keywords like **generate app**, **create app** to get a basic Streamlit app code.
        - **Code Explanation**: Ask for **code explanation**, **walk me through the code** to understand the underlying logic of Streamlit code snippets.
        - **Project Analysis**: Use **analyze my project**, **technical feedback** to get insights and recommendations on your current Streamlit project.
        - **Debug Assistance**: Use **debug this**, **fix this error** to get help with troubleshooting issues in your Streamlit app.
        """)

    st.sidebar.markdown("---")
    # Load image and convert to base64
    img_path = "imgs/stsidebarimg.png"  # Replace with the actual image path
    img_base64 = img_to_base64(img_path)



    # Display image with custom CSS class for glowing effect
    st.sidebar.markdown(
        f'<img src="data:image/png;base64,{img_base64}" class="cover-glow">',
        unsafe_allow_html=True,
    )
    
    # Handle Chat and Update Modes
    chat_input = st.chat_input("Sunt aici sa te ajut:")
    if chat_input:
        on_chat_submit(chat_input)

    # Display chat history with custom avatars
    for message in st.session_state.history[-20:]:
        role = message["role"]
        
        # Set avatar based on role
        if role == "assistant":
            avatar_image = "imgs/avatar_streamly.png"
        elif role == "user":
            avatar_image = "imgs/stuser.png"
        else:
            avatar_image = None  # Default
        
        with st.chat_message(role, avatar=avatar_image):
            st.write(message["content"])

    


        
def generate_response(user_message):

    # If a thread doesn't exist, create one and store it
    if st.session_state.thread_id is None:
        thread = client.beta.threads.create()
        st.session_state.thread_id = thread.id

    # Add message to thread
    message = client.beta.threads.messages.create(
        thread_id=st.session_state.thread_id,
        role="user",
        content=user_message,
    )

    # Retrieve the Assistant
    assistant = client.beta.assistants.retrieve(assistant_id)

    # Run the assistant
    run = client.beta.threads.runs.create(
        thread_id=st.session_state.thread_id,
        assistant_id=assistant.id,
    )

    # Wait for completion
    # https://platform.openai.com/docs/assistants/how-it-works/runs-and-run-steps#:~:text=under%20failed_at.-,Polling%20for%20updates,-In%20order%20to
    while run.status in ['queued', 'in_progress']:
        # wait for 0.5 seconds
        time.sleep(0.5)
        run = client.beta.threads.runs.retrieve(thread_id=st.session_state.thread_id, run_id=run.id)

    # Retrieve the Messages
    messages = client.beta.threads.messages.list(thread_id=st.session_state.thread_id)
    assistant_message = messages.data[0].content[0].text.value
    logging.info(f"Generated message: {assistant_message}")
    
    return assistant_message
        
    

if __name__ == "__main__":
    main()