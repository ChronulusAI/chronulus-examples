import sys
import io
import zipfile
import base64
import streamlit as st
from PIL import Image
from typing import Optional
import json


def encode_image(image):
    buffered = io.BytesIO()
    image.save(buffered, format="WebP", quality=75)
    return base64.b64encode(buffered.getvalue()).decode('utf-8')


def encode_pdf(pdf_file):
    """Convert a PDF file to a base64 encoded string."""
    return base64.b64encode(pdf_file.read()).decode('utf-8')


def process_uploaded_images(uploaded_files, related_to: Optional[str], display_label: str):
    images = []
    if uploaded_files:
        num_uploaded = len(uploaded_files)
        st.write(f"{display_label} Images ({num_uploaded}):")
        cols = st.columns(num_uploaded)  # Create columns for each image

        for i, file in enumerate(uploaded_files):
            with cols[i]:
                img = Image.open(file)
                st.image(img, caption=file.name, width=150)
                images.append({"data": encode_image(Image.open(file)), "type": "WEBP"})
    return images


def process_uploaded_pdfs(uploaded_files, related_to: Optional[str], display_label: str):
    if uploaded_files:
        num_uploaded = len(uploaded_files)
        st.write(f"{display_label} ({num_uploaded})")
        pdfs = [{"data": encode_pdf(file)} for file in uploaded_files]
        return pdfs
    return []


def update_request_list_store(cookie_controler, request_info: dict):
    request_list_str = cookie_controler.get('request_list')
    if request_list_str:
        request_list = json.loads(request_list_str) if type(request_list_str) is str else request_list_str
    else:
        request_list = []

    request_list = [request_info, *request_list]
    if sys.getsizeof(json.dumps(request_list)) > 4096:
        request_list = request_list[:-1]

    cookie_controler.set('request_list', json.dumps(request_list))


def cache_inputs_and_outputs_state(page: str, request_id: str, inputs: str, predictions: str, output_text: str):
    # Replace these with your actual file contents
    st.session_state[f"{page}_inputs"] = inputs
    st.session_state[f"{page}_predictions"] = predictions
    st.session_state[f"{page}_output_text"] = output_text
    st.session_state[f"{page}_request_id_prepared"] = request_id


def get_zip_file(page: str):
    zip_buffer = io.BytesIO()
    if f"{page}_request_id_prepared" in st.session_state.keys():
        request_id = st.session_state[f"{page}_request_id_prepared"]
        input_context = st.session_state[f"{page}_inputs"]
        output_data = st.session_state[f"{page}_predictions"]
        output_text = st.session_state[f"{page}_output_text"]

        with zipfile.ZipFile(zip_buffer, 'w') as zip_file:
            # Add JSON files to the ZIP
            zip_file.writestr(f'{request_id}-input_context.json', input_context)
            zip_file.writestr(f'{request_id}-output_data.json', output_data)
            # Add text file to the ZIP
            zip_file.writestr(f'{request_id}-output_text.txt', output_text)

        zip_buffer.seek(0)
        return zip_buffer.getvalue(), f'{request_id}-package.zip'
    else:
        zip_buffer.seek(0)
        return zip_buffer.getvalue(), None
