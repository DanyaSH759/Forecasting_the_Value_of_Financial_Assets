from pydantic import BaseModel

class PredictRequest(BaseModel):
    schema: str
    asset_name: str