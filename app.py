import requests
import pandas as pd
import time
import re
import validators

import streamlit as st
from st_keyup import st_keyup
from streamlit_option_menu import option_menu


# --- CLASS METHODS ---
# Retrieve mock user list and cache the response
@st.cache_data(show_spinner=True)
def get_mock_user_list():
    response = requests.get("https://jsonplaceholder.typicode.com/users")
    df_users = pd.DataFrame(response.json())
    time.sleep(1.5) # display spinner
    return df_users

# Clear the textboxes in the new user form
#   (Streamlit forms can only clear fields upon submission, which is not desirable
#   when validating user input since the fields should remain populated when invalid input is detected)
def clear_form():
    st.session_state["name"] = ""
    st.session_state["email"] = ""


# --- WEB PAGE CONFIGURATION ---
page_title = "User Directory"
st.set_page_config(page_title=page_title, page_icon=":bust_in_silhouette:", layout="centered")  # set_page_config() must be first command in Streamlit app
                                                                                                # Emoji icons: https://www.webfx.com/tools/emoji-cheat-sheet/
st.markdown("<h1 style='text-align: center'>"+page_title+"</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center'>This page presents a mock list of users from the <a href=\"https://jsonplaceholder.typicode.com/users\">{JSON} Placeholder</a> website.</p>", unsafe_allow_html=True)


# --- CLASS VARIABLES ---
# Columns to display in user directory table 
col_name = 'name'
col_email = 'email'
display_cols = {col_name: "The user's birth name", 
                col_email: "The user's e-mail address"}

# Initialise user directory dataframe
#   Streamlit operates by running the script from top to bottom after every interaction.
#   It is thus necessary to persist the user directory dataframe using session state (clears upon refresh)
if 'df_user_directory' not in st.session_state:
    st.session_state['df_user_directory'] = get_mock_user_list()


# --- NAVIGATION MENU ---
tab_1 = "View directory"
tab_2 = "Add new user"
selected = option_menu(
    menu_title=None,
    options=[tab_1, tab_2],
    icons=["people", "person-add"],  # bootstrap icons: https://icons.getbootstrap.com/
    default_index=0,
    orientation="horizontal",
)


# --- NAVIGATION TAB SELECTION ---
# NAV TAB: View directory
if selected == tab_1:
    # Reset local dataframe (df_filtered)
    df_filtered = st.session_state['df_user_directory'].copy()
    
    # Page introduction
    with st.container():
        col1, col2 = st.columns([2, 1])  # column layout (spacing)
        col1.subheader("List of existing users")
        col1.markdown(
        """
        All users are presented in the table below.\n
        - **To search for a user**: enter the text to search in the _Perform a search_ cascading window.
        - **To add a new user**: input their details by visiting the _Add new user_ tab from the navigation menu.
        """
        )
        col2.info(f"Number of users: {len(st.session_state['df_user_directory'])}", icon="🗓")
        
    # Perform a search
    #   Filters dataframe and displays the result
    with st.expander("Perform a search"):
        col1, col2 = st.columns([4, 1])  # column layout (spacing)
        
        with col1:
            search_term = st_keyup("Search term", debounce=200, key="0")
        search_columns = st.multiselect("Columns to search",
                                        list(display_cols.keys()),
                                        default=[col_name, col_email],
                                        max_selections=None,
                                        placeholder="Choose which columns to filter.")
        
        # Initialise a boolean mask with False values across all rows in dataframe  
        #   False: the row should not be displayed
        #   True: the row should be displayed
        mask = pd.Series([False] * len(df_filtered), index=df_filtered.index)

        # Apply a regex-based filter for each cell/value in the dataframe
        #   If any value (for the specified columns) in a row agrees with the search criteria, the row is marked as True (for display)
        for col in search_columns:
            mask |= df_filtered[col].astype(str).str.contains(re.escape(search_term), case=False)

        # Apply the final filter to the dataFrame
        df_filtered = df_filtered[mask]
        
        with col2:
            st.markdown("#")  # intentional white space (heading 1 size)
            st.markdown("_Matches:_" + " **" + str(len(df_filtered.index)) + "**")
    
    # Display filtered dataframe
    st.dataframe(df_filtered, hide_index=True, column_order=(col_name, col_email), height=500)


# NAV TAB: Add new user
if selected == tab_2:
    # Input form
    with st.form(key='new_user', clear_on_submit=False):
            
        # Form introduction
        with st.container():                
            st.subheader("Add a new user")
            st.write("Complete the following fields and click submit")
            
        # Input fields
        with st.container():    
            col1, col2 = st.columns([1, 1])
            input_name = col1.text_input(label='Name and surname', key='name')
            input_email = col2.text_input(label='E-mail address', key='email')
        
        # Form buttons
        with st.container():    
            col1, col2 = st.columns([.2, 1])
                
            submit_button = col1.form_submit_button(label='Submit')
            clear = col2.form_submit_button(label="Clear", on_click=clear_form)

        # Submit button
        # Validate the user input and add new user to dataframe
        if submit_button:
            valid_input = True # boolean flag if all inoput is valid
                            
            # Validation: name
            # Test if input contains at least two words with at least one space
            if not re.search(r"^[^ ]+ [^ ]+", input_name):
                st.warning("Enter your name and surname separated by a space.")
                valid_input = False
                
            # Validation: email
            # Validation relies on built-in Python module
            if not validators.email(input_email):
                st.warning("Enter a valid e-mail address.")
                valid_input = False

            # Only add new user to dataframe if all input fields are valid 
            if valid_input:
                try:
                    new_user = {'name':input_name, 'email':input_email}
                    st.session_state['df_user_directory'].loc[len(st.session_state['df_user_directory'])] = new_user
                    
                    st.success("New user added", icon="✔")
                    # clear_form()  # cannot clear form: command raises error
                except ValueError:
                    st.error("Failed to add new user", icon="✖")
                    