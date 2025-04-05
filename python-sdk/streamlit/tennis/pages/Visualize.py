import os

from chronulus.estimator.binary_predictor import BinaryPredictor

import plotly.graph_objects as go
import plotly.express as px
import numpy as np
from scipy import stats
import json

import streamlit as st
from streamlit_cookies_controller import CookieController
from pages._menu import menu

st.set_page_config(
    page_title="Chronulus | Tennis Prediction",
    page_icon=":tennis:",
    layout="wide",
    initial_sidebar_state="expanded"
)

menu()
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


def get_request_list_store():
    request_list_str = controller.get('request_list')

    if request_list_str:
        request_list = json.loads(request_list_str) if type(request_list_str) is str else request_list_str
    else:
        request_list = []

    original_orderings = [r for r in request_list if not r.get('reverse_order')]
    reverse_orderings = [r for r in request_list if r.get('reverse_order')]

    return original_orderings, reverse_orderings


if os.environ.get('CHRONULUS_API_KEY'):
    controller.set("CHRONULUS_API_KEY", os.environ.get('CHRONULUS_API_KEY'))

api_key_cookie = controller.get('CHRONULUS_API_KEY')

with st.expander("See your Chronulus API Key", expanded=api_key_cookie is None):
    api_key = st.text_input(
        label="Chronulus API Key",
        value=api_key_cookie if api_key_cookie else "",
        placeholder="Your Chronulus API Key"
    )

    agent = None
    if api_key:
        controller.set('CHRONULUS_API_KEY', api_key)

        active_env = dict(CHRONULUS_API_KEY=api_key)


def plot_beta(param_list, labels, notes):
    colors = px.colors.sequential.Plasma
    colors = px.colors.qualitative.Vivid
    # Generate x values for the distribution
    x = np.linspace(0, 1, 1000)
    fig = go.Figure()

    for i, (label, params, note) in enumerate(zip(labels, param_list, notes)):
        alpha, beta = params
        # Calculate PDF values
        pdf = stats.beta.pdf(x,  alpha, beta)
        text = word_wrap(note,60).replace('\n','<br>')
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
                font_size=10,
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

original, reverse = get_request_list_store()


if api_key:

    req_side1 = st.selectbox('Request Id (original order)', options=original, format_func=lambda x: f"{x.get('side1')} vs {x.get('side2')}")
    req1_id = req_side1.get('request_id')
    req_side2 = st.selectbox('Request Id (reverse order)', options=reverse, format_func=lambda x: f"{x.get('side1')} vs {x.get('side2')}")
    req2_id = req_side2.get('request_id')

    pred_set1 = get_prediction_set(req1_id, env=active_env)
    pred_set2 = get_prediction_set(req2_id, env=active_env)


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


with st.expander("Consensus Over Orderings", expanded=True):

    if api_key and req1_id and req2_id:
        param_list = []
        labels = []
        notes = []

        alpha1, beta1 = pred_set1.beta_params.model_dump().values()
        note = f'Pred ({100 * pred_set1.prob[0]:.2f}%, {100 * pred_set1.prob[1]:.2f}%)'
        param_list.append((alpha1, beta1))
        labels.append(f"Consensus (original)")
        notes.append(note)

        beta2, alpha2 = pred_set2.beta_params.model_dump().values()
        note = f'Pred ({100 * pred_set2.prob[1]:.2f}%, {100 * pred_set2.prob[0]:.2f}%)'
        param_list.append((alpha2, beta2))
        labels.append(f"Consensus (reverse)")
        notes.append(note)

        alpha3 = (alpha1 + alpha2) / 2
        beta3 = (beta1 + beta2) / 2
        prob_a = alpha3 / (alpha3+beta3)
        prob_b = beta3 / (alpha3+beta3)
        note = f'Pred ({100 * prob_a:.2f}%, {100 * prob_b:.2f}%)'
        param_list.append((alpha3, beta3))
        labels.append(f"Consensus (overall)")
        notes.append(note)

        plot_beta(param_list, labels=labels, notes=notes)



with st.expander("Original Ordering", expanded=True):
    if api_key and req1_id:
        plot_prediction_set(pred_set1)


with st.expander("Reverse Ordering", expanded=True):

    if api_key and req2_id:
        plot_prediction_set(pred_set2)










