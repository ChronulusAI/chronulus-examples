import json
import os
from datetime import datetime
from typing import List

import streamlit as st
from chronulus import Session
from chronulus.estimator.binary_predictor import BinaryPredictor
from chronulus_core.types.attribute import Image as ImageType
from pydantic import BaseModel, Field
from streamlit_cookies_controller import CookieController

from lib.tools import get_zip_file, process_uploaded_images, update_request_list_store, cache_inputs_and_outputs_state
from local_types.request import SportsWinProb
from pages._menu import menu

st.set_page_config(
    page_title="Basketball Predictions | Chronulus",
    page_icon=":basketball:",
    layout="wide",
    initial_sidebar_state="auto"
)

menu()

@st.cache_resource
def get_session(session_id: str = None, env: dict = dict()):

    if not session_id:
        chronulus_session = Session(
            name="Basketball Game Win Prediction",
            situation="""
                I am a professional forecaster who places wagers on sporting events. I would like to improve my 
                chances of winning by getting independent insights and win probability estimates to use as signals for 
                the size of my wagers on basketball games.
                """,
            task="""
                Please predict the probability that the SUBJECT team will win the game against
                the OBJECT team given the information provided.
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


st.subheader("Basketball Predictions")
st.markdown("""
This demo estimates the win probabilities for a basketball game.

We assume the team listed first on the schedule is side 1 and the team listed second is side 2.

**Reverse Order of Sides**: When toggled on, this flips the order that the sides are input to the Chronulus Agent and
provides a prediction that mitigates the framing bias that is imposed by the original order as listed on the schedule.

The AI behind the Chronulus Agent was trained before Jan 1, 2025 and we have not given it internet search capabilities. So the agent is unaware of any outside win predictions or odds unless you provide them as inputs. 

As a best practice, providing your own inputs is the best way to ensure external opinion is not introduced to your predictions. For example, when taking a screen shot of a match-up, be sure to select only the areas with relevant information about the player or team. Many sites display odds near other useful player stats. Including these in the screenshot could lead to predictions that are swayed in the direction of the odds provided by the site.
""")


class GameContext(BaseModel):
    contest_name: str = Field(description="Name of the contest or tournament")
    location: str = Field(description="Location of tournament and contest")
    game_date: str = Field(description="Date of game")
    contest_details: str = Field(description="Additional details on the game or tournament, eg. previous history between the teams over the current season or playoff")
    side1: str = Field(description="The name of the SUBJECT team")
    side2: str = Field(description="The name of the OBJECT team")
    side1_details: str = Field(description="Additional context or details about the SUBJECT team")
    side2_details: str = Field(description="Additional context or details about the OBJECT team")
    contest_images: List[ImageType] = Field(description="Images providing data or context on the match-up, contest, or tournament broadly")
    side1_images: List[ImageType] = Field(description="Images providing data or context on the SUBJECT team")
    side2_images: List[ImageType] = Field(description="Images providing data or context on the OBJECT team")


controller = CookieController()

api_key = controller.get('CHRONULUS_API_KEY')
agent = None

if not api_key:
    st.subheader("API Key Not Found")
    st.write("Your Chronulus API could not be found.")

if api_key:
    active_env = dict(CHRONULUS_API_KEY=api_key)
    estimator_id = None
    session_id = controller.get('CHRONULUS_BASKETBALL_SESSION_ID')

    chronulus_session = get_session(session_id, env=active_env)
    controller.set("CHRONULUS_BASKETBALL_SESSION_ID", chronulus_session.session_id)

    agent = get_agent(chronulus_session, input_type=GameContext, estimator_id=estimator_id, env=active_env)
    controller.set("CHRONULUS_BASKETBALL_ESTIMATOR_ID", agent.estimator_id)

st.subheader("Contest Details")
st.markdown("Fill out the details below and then click 'Predict'.")

contest_name = st.text_input(label="Contest Name", placeholder="Name of the contest. E.g., 'NCAA 2025 - Final Four'")
location = st.text_input(label="Location", placeholder="Location of the game. E.g., Alamodome, San Antonio, TX")
game_date = st.date_input('Date of game', value=datetime.today().date())
contest_details = st.text_area(label="Contest Details", placeholder="Additional details on the game that affects both sides, eg. previous history between the teams")
side1 = st.text_input(label="Side 1", placeholder="Name(s) and rank(s) of Side 1")
side1_details = st.text_area(label="Side 1 Details", placeholder="Additional context or details about Side 1, eg. injury reports")
side2 = st.text_input(label="Side 2", placeholder="Name(s) and rank(s) of Side 2")
side2_details = st.text_area(label="Side 2 Details", placeholder="Additional context or details about Side 2, eg. injury reports")

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

    item = GameContext(
        contest_name=contest_name,
        location=location,
        game_date=str(game_date),
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

    cache_inputs_and_outputs_state('basketball', req.request_id, input_context_json_str, predictions_json_str, final_output)

    zip_data, zip_filename = get_zip_file(page="basketball")

    if zip_filename:
        st.download_button("Download Inputs & Outputs (.zip)",
                           data=zip_data,
                           file_name=zip_filename,
                           mime='application/zip',
                           disabled=zip_data is None,
                           key="download_current"
                           )

    st.markdown(final_output, unsafe_allow_html=True)

    # add request to list in cookies
    request_info = SportsWinProb(
        request_id=req.request_id,
        side1=side1,
        side2=side2,
        timestamp=datetime.now().timestamp(),
        reverse_order=reverse_order,
    )
    update_request_list_store(controller, request_info.model_dump())

    if 'IS_DEPLOYED' not in st.secrets.keys() or not st.secrets.get("IS_DEPLOYED"):
        os.makedirs("output", exist_ok=True)
        os.makedirs("inputs", exist_ok=True)

        with open(f"inputs/{req.request_id}.json", "w") as f:
            f.write(input_context_json_str)

        with open(f"output/{req.request_id}.txt", "w") as f:
            f.write(final_output)

        with open(f"output/{req.request_id}.json", "w") as f:
            f.write(predictions_json_str)


else:
    zip_data, zip_filename = get_zip_file(page="basketball")
    st.download_button("Download Inputs & Outputs (.zip)",
                       data=zip_data,
                       file_name=zip_filename,
                       mime='application/zip',
                       disabled=zip_filename is None,
                       key='download-previous'
                       )