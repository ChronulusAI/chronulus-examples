import os
import json

from pydantic import BaseModel, Field
from typing import List
from datetime import datetime
import matplotlib.pyplot as plt

from chronulus.session import Session
from chronulus.estimator import NormalizedForecaster
from chronulus_core.types.attribute import ImageFromFile, ImageFromUrl

chronulus_session = Session(
    name="NYC Interborough Express Feasibility Study",

   situation="""The Interborough Express (IBX) is a transformative rapid transit 
    project that will connect currently underserved areas of Brooklyn and Queens. 
    It will substantially cut down on travel times between the two boroughs, 
    reduce congestion, and expand economic opportunities for the people who live 
    and work in the surrounding neighborhoods. 

    The project would be built along the existing, LIRR-owned Bay Ridge Branch 
    and CSX-owned Fremont Secondary, a 14-mile freight line that extends from Bay 
    Ridge, Brooklyn, to Jackson Heights, Queens. It would create a new transit
    option for close to 900,000 residents of the neighborhoods along the route, 
    along with 260,000 people who work in Brooklyn and Queens. It would connect 
    with up to 17 different subway lines, as well as Long Island Rail Road, with 
    end-to-end travel times anticipated at less than 40 minutes. Daily weekday 
    ridership is estimated at 115,000. 

    Using the existing rail infrastructure means the Interborough Express could 
    be built more quickly and efficiently. It would also preserve the Bay Ridge
    Branch’s use as a freight line, providing an opportunity to connect to the 
    Port Authority’s Cross-Harbor Freight Project. 

    After extensive planning, analysis, and public engagement, Light Rail was 
    chosen because it will provide the best service for riders at the best value. 
    It also announced a preliminary list of stations and advanced other important 
    planning and engineering analysis of the project. The formal environmental 
    review process is anticipated to begin soon.

    Project benefits
    - A direct public transit option between Brooklyn and Queens
    - Connections with up to 17 subway lines and Long Island Rail Road
    - A faster commute — end-to-end rides are expected to take 40 minutes
    - A new transit option in underserved locations where more than a third of 
    residents are below the federal poverty line    
    """,

    task="""As part of the planning processing for IBX, we would like to forecast
     the seasonal foot traffic through a few candidate rail stations with 
     connections to subway lines. In each example, forecast the foot traffic 
     (number of passengers using the connection) from the source line to 
     destination line at the candidate location. Assume the connection and IBX 
     have already been open and in use for several months.
    """,
)


class IBXConnectionPoint(BaseModel):
    candidate_location: str = Field(description="The name of the candidate location for the IBX connection.")
    source_line: str = Field(description="The name of the source line for the foot traffic.")
    destination_line: str = Field(description="The name of the destination line for the foot traffic.")
    project_images: List[ImageFromFile] = Field(default=[], description="A list of images that provide context for the IBX project.")
    events_schedule: str = Field(description="A schedule of major events in 2025")

nf_agent = NormalizedForecaster(
    session=chronulus_session,
    input_type=IBXConnectionPoint,
)


# Fill in the metadata for the item or concept you want to predict
connection_point = IBXConnectionPoint(
    candidate_location="74 St - Broadway, with connections to the 7, E, F, M, and R lines",
    source_line="IBX",
    destination_line="F line",
    project_images=[
        ImageFromFile(file_path="images/ibx-map.png"),
        ImageFromFile(file_path="images/ibx-concept.png"),
    ],
    events_schedule="""
        - US Open: Mon, Aug 25, 2025 – Sun, Sep 7, 2025
    """
)


# daily forecast
forecast_start_date = datetime(2025, 8, 1)
req = nf_agent.queue(connection_point, start_dt=forecast_start_date, days=60, note_length=(7, 10))
predictions = nf_agent.get_predictions(req.request_id)

os.makedirs("output",exist_ok=True)

fig, ax = plt.subplots(1,1,figsize=(12,4))
predictions[0].to_pandas().plot(ax=ax)
plt.savefig("output/ibx-daily.png")

predictions[0].to_pandas().to_csv("output/ibx-hourly.csv")

with open("output/ibx-daily-rows.json", "w") as f:
    json_str = json.dumps(predictions[0].to_json(orient="rows"), indent=4)
    f.write(json_str)

with open("output/ibx-daily-columns.json", "w") as f:
    json_str = json.dumps(predictions[0].to_json(orient="columns"), indent=4)
    f.write(json_str)

with open("output/ibx-daily.txt", "w") as f:
    f.write(predictions[0].text)


# hourly forecast
forecast_start_date = datetime(2025, 9, 4)
req = nf_agent.queue(connection_point, start_dt=forecast_start_date, hours=5*24, note_length=(7, 10))
predictions = nf_agent.get_predictions(req.request_id)


fig, ax = plt.subplots(1,1,figsize=(12,4))
predictions[0].to_pandas().plot(ax=ax)
plt.savefig("output/ibx-hourly.png")

predictions[0].to_pandas().to_csv("output/ibx-hourly.csv")

with open("output/ibx-hourly-rows.json", "w") as f:
    json_str = json.dumps(predictions[0].to_json(orient="rows"), indent=4)
    f.write(json_str)

with open("output/ibx-hourly-columns.json", "w") as f:
    json_str = json.dumps(predictions[0].to_json(orient="columns"), indent=4)
    f.write(json_str)

with open("output/ibx-hourly.txt", "w") as f:
    f.write(predictions[0].text)

with open("output/ibx-hourly.txt", "w") as f:
    f.write(predictions[0].text)