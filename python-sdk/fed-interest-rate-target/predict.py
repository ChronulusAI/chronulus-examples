import os
import json

from pydantic import BaseModel, Field
from typing import List


from chronulus.session import Session
from chronulus.estimator import BinaryPredictor
from chronulus_core.types.attribute import PdfFromFile, TextFromFile


from beta_plot import plot_prediction_set

chronulus_session = Session(
    name="Federal Reserve Interest Rate Target Prediction",

    situation="""When necessary, the Fed changes the stance of monetary policy 
    primarily by raising or lowering its target range for the federal funds rate, 
    an interest rate for overnight borrowing by banks.

    Lowering that target range represents an "easing" of monetary policy because it
    is accompanied by lower short-term interest rates in financial markets and a 
    loosening in broader financial conditions. This action may be needed if the 
    economy is sluggish or inflation is too low. Raising the target range represents
    a "tightening" of monetary policy, which raises interest rates and may be 
    necessary if the economy is overheating or inflation is too high.
    
    A change in the federal funds rate normally affects, and is accompanied by,
    changes in other interest rates and in financial conditions more broadly; those 
    changes will then affect the spending decisions of households and businesses and
    thus have implications for economic activity, employment, and inflation. 
    
    ----
    
    Our team is responsible for updating and logging interest rate movement signals. 
    """,

    task="""We would like to estimate the probability (as of today, March 30, 2025) that the Fed will change the 
    target fed funds range from its current one to the candidate range at the meeting date specified.
    """,
)


class MonetaryContext(BaseModel):
    fed_meeting_minutes: List[PdfFromFile] = Field(description="A collect of the most recent FOMC press releases.")
    fed_funds_history: TextFromFile = Field(description="TSV of fed funds rate target history")
    google_ai_overview: TextFromFile = Field(description="An overview of the current economic environment")
    perplexity_tariff_summary: TextFromFile = Field(description="A summary of new / upcoming US tariff policy")
    current_target_range: str = Field(description="The current fed funds target range")
    candidate_target_range: str = Field(description="The candidate fed funds target range")
    meeting_date: str = Field(description="The date of the FOMC meet at which the candidate target would be updated.")


agent = BinaryPredictor(
    session=chronulus_session,
    input_type=MonetaryContext,
)

# Fill in the metadata for the item or concept you want to predict
context = MonetaryContext(
    fed_meeting_minutes=[
        PdfFromFile(file_path="assets/monetary20250319a1.pdf"),
    ],
    fed_funds_history=TextFromFile(file_path="assets/fed-funds-history.txt"),
    google_ai_overview=TextFromFile(file_path="assets/google-ai-overview.txt"),
    perplexity_tariff_summary=TextFromFile(file_path="assets/perplexity-tariffs-overview.txt"),
    current_target_range="Low: 4.25% to High: 4.50%",
    candidate_target_range="Low: 4.00% to High: 4.25%",
    meeting_date="May 07, 2025"
)

req = agent.queue(context, num_experts=5)

prediction_set = agent.get_request_predictions(req.request_id, try_every=5)

os.makedirs("output", exist_ok=True)

plot_prediction_set(prediction_set, "output/prediction_set-betas.png", figsize=(8, 4))


with open("output/fed-funds-may2025.txt", "w") as f:
    f.write(prediction_set.text)


json_str = json.dumps(prediction_set.to_dict(), indent=2)
with open("output/fed-funds-may2025.json", "w") as f:
    f.write(json_str)