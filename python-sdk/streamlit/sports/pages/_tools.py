import sys
import io
import zipfile
import base64
import streamlit as st
from PIL import Image
import json

def encode_image(image):
    buffered = io.BytesIO()
    image.save(buffered, format="WebP", quality=75)
    return base64.b64encode(buffered.getvalue()).decode('utf-8')


def process_uploaded_images(uploaded_files, related_to: str, display_label: str):
    if uploaded_files:
        num_uploaded = len(uploaded_files)
        st.write(f"{display_label} Images ({num_uploaded}):")
        cols = st.columns(num_uploaded)  # Create columns for each image
        for i, file in enumerate(uploaded_files):
            with cols[i]:
                img = Image.open(file)
                st.image(img, caption=file.name, width=150)
        images = [{"data": encode_image(Image.open(file)), "type": "WEBP"} for file in uploaded_files]
        return images
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


def get_zip_file(request_id, input_context: str, output_data: str, output_text: str):
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w') as zip_file:
        # Add JSON files to the ZIP
        zip_file.writestr(f'{request_id}-input_context.json', input_context)
        zip_file.writestr(f'{request_id}-output_data.json', output_data)
        # Add text file to the ZIP
        zip_file.writestr(f'{request_id}-output_text.txt', output_text)

    zip_buffer.seek(0)
    return zip_buffer.getvalue()