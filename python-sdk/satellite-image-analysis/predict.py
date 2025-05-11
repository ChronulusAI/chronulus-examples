from pydantic import BaseModel, Field

from chronulus.session import Session
from chronulus.estimator import BinaryPredictor
from chronulus_core.types.attribute import ImageFromFile

from beta_plot import save_predictions


chronulus_session = Session(
    name="Satellite Image Analysis",

    situation="""
    I am US DoD analyst focused on surveillance in the Ukraine / Russia theater.
    We believe Russia may be deploying decoy surface to air systems and are trying to identify them
    from satellite imagery.
    """,

    task="""Given the context provided, predict the probability that the systems indicated in the analysis image are all
    real, active versions of the QUERY system(s) and not decoys or decorative (non-functional).
    """,
)


class AnalysisContext(BaseModel):
    query_system: str = Field(description="The name of the QUERY system")
    analysis_image: ImageFromFile = Field(description="The image to be analyzed")


agent = BinaryPredictor(
    session=chronulus_session,
    input_type=AnalysisContext,
)


# Fill in the metadata for the item or concept you want to predict
context1 = AnalysisContext(
    query_system="S-300 or S-400 air defense system",
    analysis_image=ImageFromFile(file_path="assets/sat1.jpeg")
)

req1 = agent.queue(context1, num_experts=5)
prediction_set1 = agent.get_request_predictions(req1.request_id, try_every=5)

save_predictions(prediction_set1, output_path="output-1")


# Fill in the metadata for the item or concept you want to predict
context2 = AnalysisContext(
    query_system="S-300 or S-400 air defense system",
    analysis_image=ImageFromFile(file_path="assets/sat2.jpeg")
)

req2 = agent.queue(context2, num_experts=5)
prediction_set2 = agent.get_request_predictions(req2.request_id, try_every=5)

save_predictions(prediction_set2, output_path="output-2")




