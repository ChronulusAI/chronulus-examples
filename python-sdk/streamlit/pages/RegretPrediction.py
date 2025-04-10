import json
import os
from datetime import datetime
from typing import List

import streamlit as st
from chronulus import Session
from chronulus.estimator.binary_predictor import BinaryPredictor
from chronulus_core.types.attribute import Pdf
from pydantic import BaseModel, Field
from streamlit_cookies_controller import CookieController

from lib.tools import get_zip_file, update_request_list_store, cache_inputs_and_outputs_state, \
    process_uploaded_pdfs
from pages._menu import menu
from local_types.request import VCRegret

st.set_page_config(
    page_title="Missed Opportunity Prediction | Chronulus",
    page_icon=":money_with_wings:",
    layout="wide",
    initial_sidebar_state="auto"
)
menu()


@st.cache_resource
def get_session(session_id: str = None, env: dict = dict()):

    if not session_id:
        chronulus_session = Session(
            name="VC Regret Minimization",
            situation="""
                I am a partner at a prestigious venture capital firm. A challenging aspect of my role day to day is 
                finding and evaluating investment opportunities. One way to think of this process is one of minimizing the
                regret of passing on an investment opportunity. Estimating the regret of passing on an opportunity
                allows me to score each opportunity and only investing in those where I would have the highest 
                probability of regret.
                """,
            task="""
                Please estimate the probability that we will regret passing on the opportunity to lead or join the round
                of the startup described by the provided inputs. 
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


st.header("Missed Opportunity Regret Prediction")
st.markdown("""
This demo is estimates the probability of regretting a missed investment opportunity.
""")


class StartupContext(BaseModel):
    name: str = Field(description="Name of startup")
    elevator_pitch: str = Field(description="Elevator pitch")
    team: str = Field(description="Team background and expertise")
    market_opportunity: str = Field(description="Market Opportunity")
    traction_metrics: str = Field(description="Traction metrics")
    unit_economics: str = Field(description="Unit economics")
    competition: str = Field(description="Competitive landscape")
    gtm: str = Field(description="Go-to-market strategy")
    capital_efficiency: str = Field(description="Capital efficiency")
    use_of_funds: str = Field(description="Use of funds")
    exit_opportunities: str = Field(description="Exit opportunities")
    projections: str = Field(description="Financial projections")
    additional_pdfs: List[Pdf] = Field(description="Additional / Supporting PDFs")


controller = CookieController()

api_key = controller.get('CHRONULUS_API_KEY')
agent = None

if not api_key:
    st.subheader("API Key Not Found")
    st.write("Your Chronulus API could not be found.")

if api_key:
    active_env = dict(CHRONULUS_API_KEY=api_key)
    estimator_id = None
    session_id = controller.get('CHRONULUS_VC_SESSION_ID')

    chronulus_session = get_session(session_id, env=active_env)
    controller.set("CHRONULUS_VC_SESSION_ID", chronulus_session.session_id)

    agent = get_agent(chronulus_session, input_type=StartupContext, estimator_id=estimator_id, env=active_env)
    controller.set("CHRONULUS_VC_ESTIMATOR_ID", agent.estimator_id)

st.subheader("Opportunity Details")
st.markdown("Fill out the details below and then click 'Predict'.")

company_name = st.text_input(label="Startup Name (required)", placeholder="Name of the company")
elevator_pitch = st.text_area(label="Elevator Pitch", placeholder="60 second elevator pitch")
team = st.text_area(label="Team background and expertise", placeholder="Relevant domain expertise, prior startup experience, and complementary skill sets")
market_opp = st.text_area(label='Market Opportunity', placeholder="Definition of the total addressable market (TAM), serviceable addressable market (SAM), and serviceable obtainable market (SOM)")
traction_metrics = st.text_area(label="Traction Metrics", placeholder="Monthly recurring revenue (MRR), annual recurring revenue (ARR), user growth rate, customer acquisition cost (CAC), lifetime value (LTV), and retention rates.")
unit_economics = st.text_area(label="Unit economics", placeholder="Gross margins, contribution margins per customer, and path to profitability.")
competition = st.text_area(label="Competitive landscape", placeholder="The unique value proposition compared to competitors and barriers to entry.")
gtm = st.text_area(label="Go-to-market strategy", placeholder="The plan to acquire and scale customers efficiently.")
cap_efficiency = st.text_area(label="Capital efficiency:", placeholder="Use of previous funding and burn rate")
use_of_funds = st.text_area(label="Use of funds", placeholder="Clear plan for how the new capital will be deployed to achieve specific milestones.")
exit_opportunities = st.text_area(label="Exit Opportunities", placeholder="Potential acquirers and comparable exits in the industry.")
projections = st.text_area(label="Financial Projections", placeholder="3-5 year forecasts with reasonable assumptions.")

uploaded_pdfs = st.file_uploader(
    "Additional Materials as PDFs (optional)",
    accept_multiple_files=True,
    type=['pdf'],
)

additional_pdfs = process_uploaded_pdfs(uploaded_pdfs, related_to=None, display_label='Additional Materials as PDFs ')

num_experts = int(st.text_input(label="Number of Experts", value=5))


st.subheader("Predictions")

st.markdown("Fill out the details above and then click 'Predict'.")


if st.button("Predict", disabled=not (api_key or agent)) and company_name:

    item = StartupContext(
        name=company_name,
        elevator_pitch=elevator_pitch,
        team=team,
        market_opportunity=market_opp,
        traction_metrics=traction_metrics,
        unit_economics=unit_economics,
        competition=competition,
        gtm=gtm,
        capital_efficiency=cap_efficiency,
        use_of_funds=use_of_funds,
        exit_opportunities=exit_opportunities,
        projections=projections,
        additional_pdfs=[Pdf(**pdf) for pdf in additional_pdfs],
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

    cache_inputs_and_outputs_state('tennis', req.request_id, input_context_json_str, predictions_json_str, final_output)

    zip_data, zip_filename = get_zip_file(page="tennis")

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
    request_info = VCRegret(
        request_id=req.request_id,
        timestamp=datetime.now().timestamp(),
        company_name=company_name,
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
    zip_data, zip_filename = get_zip_file(page="tennis")
    st.download_button("Download Inputs & Outputs (.zip)",
                       data=zip_data,
                       file_name=zip_filename,
                       mime='application/zip',
                       disabled=zip_filename is None,
                       key='download-previous'
                       )














