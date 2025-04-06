import json
import os
from datetime import datetime

import streamlit as st
from streamlit_cookies_controller import CookieController

from pages._menu import menu
from pages._tools import get_zip_file, process_uploaded_images, update_request_list_store

st.set_page_config(
    page_title="Tennis Predictions | Chronulus",
    page_icon=":tennis:",
    layout="wide",
    initial_sidebar_state="auto"
)
menu()

from pydantic import BaseModel, Field
from chronulus import Session
from chronulus.estimator.binary_predictor import BinaryPredictor
from chronulus_core.types.attribute import Image as ImageType
from typing import List


@st.cache_resource
def get_session(session_id: str = None, env: dict = dict()):

    if not session_id:
        chronulus_session = Session(
            name="ATP/WTA Tennis Match Win Prediction",
            situation="""
                I am a professional forecaster who places wagers on sporting events. I would like to improve my 
                chances of winning by getting independent insights and win probability estimates to use as signals for 
                the size of my wagers on sports matches.
                """,
            task="""
                Please predict the probability that side1 (player or team if a doubles match) will win the match against
                side2 (player or team if a doubles match) given the information provided.
                """,
            env=env
        )
    else:
        chronulus_session = Session.load_from_saved_session(session_id, env=env)

    return chronulus_session


@st.cache_resource
def get_agent(_chronulus_session, input_type, estimator_id: str = None, env: dict = dict()):
    if not estimator_id:
        agent = BinaryPredictor(
            session=_chronulus_session,
            input_type=input_type
        )
    else:
        agent = BinaryPredictor.load_from_saved_estimator(estimator_id, env=env)
    return agent


class MatchContext(BaseModel):
    contest_name: str = Field(description="Name of the contest or tournament")
    location: str = Field(description="Location of tournament and contest")
    match_date: str = Field(description="Date of match")
    contest_details: str = Field(description="Additional details on the contest that affect both sides, eg. weather or previous history between the players")
    side1: str = Field(description="The name(s) of the player(s) on side1")
    side2: str = Field(description="The name(s) of the player(s) on side2")
    side1_details: str = Field(description="Additional context or details about side1")
    side2_details: str = Field(description="Additional context or details about side2")
    contest_images: List[ImageType] = Field(description="Images providing data or context on the match-up, contest, or tournament broadly")
    side1_images: List[ImageType] = Field(description="Images providing data or context on the side1")
    side2_images: List[ImageType] = Field(description="Images providing data or context on the side2")


controller = CookieController()

api_key = controller.get('CHRONULUS_API_KEY')

if not api_key:
    st.subheader("API Key Not Found")
    st.write("Your Chronulus API could not be found.")

if api_key:
    active_env = dict(CHRONULUS_API_KEY=api_key)
    estimator_id = None
    session_id = controller.get('CHRONULUS_SESSION_ID')

    chronulus_session = get_session(session_id, env=active_env)
    controller.set("CHRONULUS_SESSION_ID", chronulus_session.session_id)

    agent = get_agent(chronulus_session, input_type=MatchContext, estimator_id=estimator_id, env=active_env)
    controller.set("CHRONULUS_ESTIMATOR_ID", agent.estimator_id)

st.subheader("Contest Details")
st.markdown("Fill out the details below and then click 'Predict'.")

contest_name = st.text_input(label="Contest Name", placeholder="Name of the contest. E.g., 'ATP US Open - Round of 64'")
location = st.text_input(label="Location", placeholder="Location of match. E.g., Court 5, Miami, FL")
match_date = st.date_input('Date of match', value=datetime.today().date())
contest_details = st.text_area(label="Contest Details", placeholder="Additional details on the contest that affect both sides, eg. weather or previous history between the players")
side1 = st.text_input(label="Side 1", placeholder="Name(s) and rank(s) of Side 1")
side1_details = st.text_area(label="Side 1 Details")
side2 = st.text_input(label="Side 2", placeholder="Name(s) and rank(s) of Side 2")
side2_details = st.text_area(label="Side 2 Details")

uploaded_contest_files = st.file_uploader("Contest Images (optional)", accept_multiple_files=True, type=['png', 'jpg', 'jpeg', 'webp', 'gif', 'avif'])
uploaded_side1_files = st.file_uploader("Side 1 Images (optional)", accept_multiple_files=True, type=['png', 'jpg', 'jpeg', 'webp', 'gif', 'avif'])
uploaded_side2_files = st.file_uploader("Side 2 Images (optional)", accept_multiple_files=True, type=['png', 'jpg', 'jpeg', 'webp', 'gif', 'avif'])

contest_images = process_uploaded_images(uploaded_contest_files, related_to=contest_name, display_label='Contest')
side1_images = process_uploaded_images(uploaded_side1_files, related_to=side1, display_label='Side 1')
side2_images = process_uploaded_images(uploaded_side2_files, related_to=side2, display_label='Side 2')


num_experts = int(st.text_input(label="Number of Experts", value=5))

reverse_order = st.toggle("Reverse Order of Sides", value=False)

st.subheader("Predictions")

st.markdown("Fill out the details above and then click 'Predict'.")

if st.button("Predict", disabled=not (api_key or agent)) and side1 and side2:

    item = MatchContext(
        contest_name=contest_name,
        location=location,
        match_date=str(match_date),
        contest_details=contest_details,
        side1=side2 if reverse_order else side1,
        side2=side1 if reverse_order else side2,
        side1_details=side2_details if reverse_order else side1_details,
        side2_details=side1_details if reverse_order else side2_details,
        contest_images=[ImageType(**img) for img in contest_images],
        side1_images=[ImageType(**img) for img in (side2_images if reverse_order else side1_images)],
        side2_images=[ImageType(**img) for img in (side1_images if reverse_order else side2_images)],

    )

    req = agent.queue(item, num_experts=num_experts, note_length=(7, 10))
    prediction_set = agent.get_request_predictions(req.request_id, max_tries=30)

    output = prediction_set.text
    lines = [
        f"request_id: {req.request_id}",
        f"{prediction_set.prob} with Beta({prediction_set.beta_params.alpha}, {prediction_set.beta_params.beta})",
        output
    ]
    final_output = "\n\n".join(lines)


    predictions_json_str = json.dumps(prediction_set.to_dict(), indent=2)
    input_context = dict(
        session_id=chronulus_session.session_id,
        estimator_id=agent.estimator_id,
        item=item.model_dump(),
    )
    input_context_json_str = json.dumps(input_context, indent=2)

    st.download_button("Download Inputs & Outputs (.zip)",
                       data=get_zip_file(req.request_id, input_context_json_str, predictions_json_str, final_output),
                       file_name=f'{req.request_id}-package.zip',
                       mime='application/zip',
                       )

    st.markdown(final_output, unsafe_allow_html=True)

    # add request to list in cookies
    request_info = dict(
        request_id=req.request_id,
        side1=side1,
        side2=side2,
        timestamp=datetime.now().timestamp(),
        reverse_order=reverse_order,
    )
    update_request_list_store(controller, request_info)

    if 'IS_DEPLOYED' not in st.secrets.keys() or not st.secrets.get("IS_DEPLOYED"):

        os.makedirs("output", exist_ok=True)
        os.makedirs("inputs", exist_ok=True)

        with open(f"inputs/{req.request_id}.json", "w") as f:
            f.write(input_context_json_str)

        with open(f"output/{req.request_id}.txt", "w") as f:
            f.write(final_output)

        with open(f"output/{req.request_id}.json", "w") as f:
            f.write(predictions_json_str)
















