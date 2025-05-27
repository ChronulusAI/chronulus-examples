# 'zapier' is imported by default. No need to import it
import os
import requests
import base64

from pydantic import BaseModel, Field
from typing import List
import time

from chronulus.session import Session
from chronulus.estimator import BinaryPredictor
from chronulus_core.types.attribute import Pdf

from db_tools import write_use_to_dynamodb, count_items_for_email

event = zapier.trigger_output

use_limit = 5
use_count = count_items_for_email(
    email=event.get("user_email"),
    table_name="screen-my-pitch-emails",
    region_name=os.environ["AWS_REGION"]
)


# define the data model for the Chronulus Agent
# alternatively, you could have extract more details from the email and fed these through to chronulus here.
# or even a fed through multiple PDFs if more than one was attached for the prospect startup.
class StartupContext(BaseModel):
    company_name: str = Field(description="Name of startup")
    pdf_attachment: Pdf = Field(description="Pitch Deck PDF")


# define the outputs we want to pass to the next Zapier step
class OutputData(BaseModel):
    status: str = Field(default='Failed')
    regret_passing_prob: str = Field(default='N/A')
    regret_passing_pct: str = Field(default='N/A')
    alpha: str = Field(default='N/A')
    beta: str = Field(default='N/A')
    alpha_approx: str = Field(default='N/A')
    beta_approx: str = Field(default='N/A')
    explanation: str = Field(default='N/A')
    use_count: int = Field(default=use_count)


if use_count <= use_limit:

    if not event.get("pdf_attachment"):
        # Use the below code to return data from your Function
        zapier.action.functions.return_function(
            params={
                "output_data": OutputData(status='TestRun').model_dump(),  # Output / Return Values
            },
            type_of="write",
        )

    # setup your Chronulus session
    chronulus_session = Session(
        name="VC Regret Minimization",

        situation="""
          I am a partner at a prestigious venture capital firm. A challenging aspect of my role day to day is 
          finding and evaluating investment opportunities. One way to think of this process is of minimizing my future
          regret of choosing not to invest in an investment opportunity. 
          """,

        task="""
          Please estimate the probability that the start-up described in the provided inputs will be so successful that
          I will come to regret turning down the opportunity to invest in it now.
          """,
    )

    agent = BinaryPredictor(
        session=chronulus_session,
        input_type=StartupContext,
    )

    pdf_url = event.get("pdf_attachment")
    response = requests.get(pdf_url, timeout=30)
    response.raise_for_status()
    pdf_base64 = base64.b64encode(response.content).decode('utf-8')

    context = StartupContext(
        company_name=event.get("company_name", 'No name given'),
        pdf_attachment=Pdf(data=pdf_base64)
    )

    try:
        req = agent.queue(context, num_experts=5)
        prediction_set = agent.get_request_predictions(req.request_id, try_every=5)

        write_use_to_dynamodb(
            email=event.get("user_email"),
            timestamp=int(time.time()),
            table_name="screen-my-pitch-emails",
            region_name=os.environ["AWS_REGION"]
        )

        output = OutputData(
            status="Complete",
            regret_passing_prob=str(prediction_set.prob_a),
            regret_passing_pct=f"{prediction_set.prob_a * 100: 2.2f}",
            alpha=str(prediction_set.beta_params.alpha),
            beta=str(prediction_set.beta_params.beta),
            alpha_approx=f"{prediction_set.beta_params.alpha: 3.3f}",
            beta_approx=f"{prediction_set.beta_params.beta: 3.3f}",
            explanation=prediction_set.text,
            use_count=use_count + 1
        )

        # Use the below code to return data from your Function
        zapier.action.functions.return_function(
            params={
                "output_data": output.model_dump(),  # Output / Return Values
            },
            type_of="write",
        )


    except:

        # Use the below code to return data from your Function
        zapier.action.functions.return_function(
            params={
                "output_data": OutputData().model_dump(),  # Output / Return Values
            },
            type_of="write",
        )

else:

    # Use the below code to return data from your Function
    zapier.action.functions.return_function(
        params={
            "output_data": OutputData(status="UseLimitReached").model_dump(),  # Output / Return Values
        },
        type_of="write",
    )
