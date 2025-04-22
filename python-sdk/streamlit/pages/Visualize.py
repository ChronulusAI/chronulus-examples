import os

from chronulus.estimator.binary_predictor import BinaryPredictor

import plotly.graph_objects as go
import plotly.express as px
import numpy as np
from scipy import stats
import json
from typing import TypeVar, Type, List


import streamlit as st
from streamlit_cookies_controller import CookieController

from local_types.request import RequestInfo, SportsWinProb
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
This demo provides tools for visualizing predictions sets from the sports prediction demos.

In the boxes below, select the prediction set from both an original and reserve ordering on the same match-up.

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

    info_list = get_request_list_store(SportsWinProb)

    original_sets = [info for info in info_list if not info.get('reverse_order')]
    reversed_sets = [info for info in info_list if info.get('reverse_order')]

    req_set1 = st.selectbox('Prediction Set 1 (Original)', options=original_sets, format_func=lambda x: f"{x.get('side1')} vs {x.get('side2')} - ({x.get('request_id')})")
    req_set2 = st.selectbox('Prediction Set 2 (Reversed)', options=reversed_sets, format_func=lambda x: f"{x.get('side1')} vs {x.get('side2')} - ({x.get('request_id')})")

    req1_id = req_set1.get('request_id') if isinstance(req_set1, dict) else None
    req2_id = req_set2.get('request_id') if isinstance(req_set2, dict) else None

    if req1_id and req2_id:
        pred_set1 = get_prediction_set(req1_id, env=active_env)
        pred_set2 = get_prediction_set(req2_id, env=active_env)

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
                prob_a = (alpha1 + alpha2) / (alpha1 + alpha2 + beta1 + beta2)
                prob_b = 1-prob_a
                note = f'Pred ({100 * prob_a:.2f}%, {100 * prob_b:.2f}%)'
                param_list.append((alpha3, beta3))
                labels.append(f"Consensus (overall)")
                notes.append(note)

                plot_beta(param_list, labels=labels, notes=notes)

    with st.expander("Original Ordering", expanded=True):

        if api_key and req1_id:
            pred_set1 = get_prediction_set(req1_id, env=active_env)
            plot_prediction_set(pred_set1)

    with st.expander("Reverse Ordering", expanded=True):

        if api_key and req2_id:
            pred_set2 = get_prediction_set(req2_id, env=active_env)
            plot_prediction_set(pred_set2)










