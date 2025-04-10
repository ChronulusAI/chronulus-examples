import os

from chronulus.estimator.binary_predictor import BinaryPredictor

import plotly.graph_objects as go
import plotly.express as px
import numpy as np
from scipy import stats
import json
from typing import TypeVar, Type


import streamlit as st
from streamlit_cookies_controller import CookieController

from local_types.request import VCRegret, RequestInfo
from pages._menu import menu


st.set_page_config(
    page_title="Visualize Prediction Sets | Chronulus",
    page_icon=":notebook_with_decorative_cover:",
    layout="wide",
    initial_sidebar_state="expanded"
)

menu()

st.subheader("Visualize Prediction Sets")
st.markdown("""
This demo provides tools for visualizing predictions sets from finance and markets demo

In the box below, select the prediction set from the use case you would like to explore.

""")


controller = CookieController()


def word_wrap(text, width=40):
    """
    Wraps plain text by replacing spaces with <br> tags to ensure text
    is wrapped at approximately the specified width.

    Args:
        text (str): The plain text to wrap
        width (int): The approximate maximum line length before wrapping

    Returns:
        str: Text with spaces replaced by <br> tags to create wrapping
    """
    if not text:
        return ""

    result = []
    current_line_length = 0
    words = text.split(' ')

    for word in words:
        # If adding this word would exceed the width
        if current_line_length + len(word) + 1 > width and current_line_length > 0:
            # Add a line break instead of a space
            result.append('<br>')
            current_line_length = 0
        elif current_line_length > 0:
            # Add a regular space
            result.append(' ')
            current_line_length += 1

        # Add the word
        result.append(word)
        current_line_length += len(word)

    return ''.join(result)


@st.cache_resource
def get_prediction_set(request_id: str = None, env: dict = dict()):
    return BinaryPredictor.get_request_predictions_static(request_id, env=env)


RequestInfoSubclass = TypeVar('RequestInfoSubclass', bound=RequestInfo)


def get_request_list_store(info_model: Type[RequestInfoSubclass]):
    request_list_str = controller.get('request_list')

    if request_list_str:
        request_list = json.loads(request_list_str) if type(request_list_str) is str else request_list_str
    else:
        request_list = []

    info_list = []

    for r in request_list:

        try:
            info_data = info_model(**r)
            info_list.append(info_data.model_dump())

        except:
            pass

    return info_list


def plot_beta(param_list, labels, notes):
    colors = px.colors.qualitative.Vivid
    # Generate x values for the distribution
    x = np.linspace(0, 1, 1000)
    fig = go.Figure()

    for i, (label, params, note) in enumerate(zip(labels, param_list, notes)):
        alpha, beta = params
        # Calculate PDF values
        pdf = stats.beta.pdf(x,  alpha, beta)
        text = word_wrap(note, 60).replace('\n','<br>')
        # Create custom hover template with the explanation
        hovertemplate = (
            f"<b>{label} - Beta({alpha:.2f}, {beta:.2f})</b><br><br>"
            f"{text}"
            "<extra></extra>"
        )

        # Create the plot using Plotly
        fig.add_trace(go.Scatter(
            x=x,
            y=pdf,
            mode='lines',
            name=f'{label}',
            line=dict(color=colors[i], width=2),
            hovertemplate=hovertemplate,
            hoverlabel=dict(
                bgcolor='white',
                font_size=11,
                font_family="Arial",
                align='left',
            )

        ))

    # Customize the layout
    fig.update_layout(
        xaxis_title="x",
        yaxis_title="Probability Density",
        height=400,
        margin=dict(l=40, r=40, t=60, b=40),
        legend=dict(yanchor="bottom", orientation="h", y=1.02, )
    )

    # Display the plot in Streamlit
    st.plotly_chart(fig, use_container_width=True)


def plot_prediction_set(prediction_set):
    col1, col2 = st.columns(2)

    with col1:
        # experts (+)
        param_list = []
        labels = []
        notes = []
        for i, pred in enumerate(prediction_set):
            item = pred.opinion_set.positive
            alpha, beta = item.beta_params.model_dump().values()
            param_list.append((alpha, beta))
            labels.append(f"Expert {i + 1} (+)")
            notes.append(item.text)

        plot_beta(param_list, labels=labels, notes=notes)

        # experts
        param_list = []
        labels = []
        notes = []
        for i, pred in enumerate(prediction_set):
            item = pred.opinion_set
            alpha, beta = item.beta_params.model_dump().values()
            param_list.append((alpha, beta))
            labels.append(f"Expert {i + 1}")
            note = f'Pred ({100 * item.prob[0]:.2f}%, {100 * item.prob[1]:.2f}%)'
            notes.append(note)

        plot_beta(param_list, labels=labels, notes=notes)

    with col2:

        # experts (-)
        param_list = []
        labels = []
        notes = []
        for i, pred in enumerate(prediction_set):
            item = pred.opinion_set.negative
            alpha, beta = item.beta_params.model_dump().values()
            param_list.append((alpha, beta))
            labels.append(f"Expert {i + 1} (-)")
            notes.append(item.text)

        plot_beta(param_list, labels=labels, notes=notes)

        alpha, beta = prediction_set.beta_params.model_dump().values()
        note = f'Pred ({100 * prediction_set.prob[0]:.2f}%, {100 * prediction_set.prob[1]:.2f}%)'
        plot_beta([(alpha, beta)], labels=["Consensus"], notes=[note])


api_key = controller.get('CHRONULUS_API_KEY')

if not api_key:
    st.subheader("API Key Not Found")
    st.write("Your Chronulus API could not be found.")

if api_key:
    active_env = dict(CHRONULUS_API_KEY=api_key)

    original_set = get_request_list_store(VCRegret)
    req_set1 = st.selectbox('Prediction Set', options=original_set, format_func=lambda x: f"{x.get('company_name')} - ({x.get('request_id')})")
    req1_id = req_set1.get('request_id') if isinstance(req_set1, dict) else None

    with st.expander("Distribution of Expert Opinions", expanded=True):

        if api_key and req1_id:
            pred_set1 = get_prediction_set(req1_id, env=active_env)
            plot_prediction_set(pred_set1)










