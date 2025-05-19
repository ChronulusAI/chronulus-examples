import os

import streamlit as st
from streamlit_cookies_controller import CookieController

from pages._menu import menu

st.set_page_config(
    page_title="FAQs | Chronulus",
    page_icon=":bulb:",
    layout="centered",
    initial_sidebar_state="auto"
)

menu()
controller = CookieController()

st.subheader("FAQs")
st.markdown("""

#### Image Upload Error

You may receive the following error when uploading an image or file:

```bash
AxiosError: Request failed with status code 400
```

This is a [known issue with Streamlit](https://github.com/streamlit/streamlit/issues/11396) and is to due the file name of the uploaded file containing a unicode characters.

##### It usually happens for a couple reasons:

1. When the file name contains non-english characters like cyrillic or kanji.
    - In this case, simply rename the file to contain only english characters.
2. When uploading Screenshot images from newer version of MacOS (Sonoma and later)
    - In this case, Mac inserts a special space character between the time and AM/PM suffix
    - You can either rename the file to get rid of this character, or...
    - Go to your Mac `Settings -> Date & Time` and then toggle on '24-hour time'. This changes the default time format on your Mac to a 24-hour clock and removes the character by default for your screenshots filenames.
    



""")





