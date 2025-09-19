import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import logging

from mcp_tools.vartopia_tools import VartopiaTool

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Vartopia API Layer", version="1.0.0")
vartopia_tool = VartopiaTool()

class VendorRequest(BaseModel):
    user_email: str

class ProgramRequest(BaseModel):
    vendor_id: str
    user_email: str

class ProgramSchemaRequest(BaseModel):
    program_id: str
    user_email: str

class SubmitDealRequest(BaseModel):
    program_id: str
    user_email: str
    form_data: dict

@app.post("/vendors")
async def vendors(req: VendorRequest):
    try:
        return await vartopia_tool.run(action="list_vendors", user_email=req.user_email)
    except Exception as e:
        logger.exception("Error fetching vendors")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/programs")
async def programs(req: ProgramRequest):
    try:
        return await vartopia_tool.run(
            action="list_programs",
            vendor_id=req.vendor_id,
            user_email=req.user_email
        )
    except Exception as e:
        logger.exception("Error fetching programs")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/program-schema")
async def program_schema(req: ProgramSchemaRequest):
    try:
        return await vartopia_tool.run(
            action="get_program_schema",
            program_id=req.program_id,
            user_email=req.user_email
        )
    except Exception as e:
        logger.exception("Error fetching program schema")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/submit-deal")
async def submit_deal_endpoint(req: SubmitDealRequest):
    try:
        return await vartopia_tool.run(
            action="submit_deal",
            program_id=req.program_id,
            user_email=req.user_email,
            form_data=req.form_data
        )
    except Exception as e:
        logger.exception("Error submitting deal")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run("main1:app", host="0.0.0.0", port=9000, reload=True)
