from sdk.tool import BaseTool
from fastapi import HTTPException
from api_client import client
import logging

logger = logging.getLogger(__name__)

class VartopiaTool(BaseTool):
    """
    MCP Tool to interact with Vartopia API.
    Supports: login, upsert deal, get deal updates, list vendors/programs, fetch program schema.
    """

    def __init__(self):
        super().__init__(
            name="VartopiaTool",
            description="Handles all Vartopia API actions: login, upsert_deal, get_updates, list_vendors, list_programs",
            run_func=self.run  
        )
        self.access_token = None
        self.user_email = None

    async def login(self, username:str, password:str):
        try:
            login_response=await client.login(username, password)
            self.access_token=(
                login_response.get("data",{})
                .get("Tokens",{})
                .get("AccessToken")
            )
            self.user_email=login_response.get("data",{}).get("Email")
            
            if not self.access_token:
                raise HTTPException(status_code=401, detail="Login failed: No access token returned.")
            
            return {
                "message":"Login successful",
                "access_token":self.access_token,
                "user_email":self.user_email,
            }
            
        except Exception as e:
            logger.exception("Vartopia login failed")
            raise HTTPException(status_code=500, detail=str(e))

    async def upsert_deal(self,deal_data:dict):
        if not self.access_token:
            raise HTTPException(status_code=401, detail="Not logged in. Call login first.")
        try:
            return await client.upsert_deal(self.access_token,deal_data)
        except Exception as e:
            logger.exception("upsert_deal failed")
            raise HTTPException(status_code=500, detail=str(e))

    async def get_registration_updates(self, unique_id="", varcrm_opportunity_id="", vartopia_transaction_id=""):
        if not self.access_token or not self.user_email:
            raise HTTPException(status_code=401, detail="Not logged in. Call login first.")
        try:
            return await client.get_registration_updates(
                self.user_email,
                unique_id=unique_id,
                varcrm_opportunity_id=varcrm_opportunity_id,
                vartopia_transaction_id=vartopia_transaction_id,
            )
        except Exception as e:
            logger.exception("get_registration_updates failed")
            raise HTTPException(status_code=500, detail=str(e))

    async def list_vendors(self):
        if not self.access_token or not self.user_email:
            raise HTTPException(status_code=401, detail="Not logged in. Call login first.")
        try:
            return await client.get_vendors(self.user_email)
        except Exception as e:
            logger.exception("list_vendors failed")
            raise HTTPException(status_code=500, detail=str(e))

    async def list_programs(self, vendor_id: str):
        if not self.access_token or not self.user_email:
            raise HTTPException(status_code=401, detail="Not logged in. Call login first.")
        if not vendor_id:
            raise HTTPException(status_code=400, detail="vendor_id is required for list_programs")
        try:
            return await client.get_program(vendor_id, self.user_email)
        except Exception as e:
            logger.exception("list_programs failed")
            raise HTTPException(status_code=500, detail=str(e))

    async def get_program_schema(self, program_id: str):
        if not self.access_token or not self.user_email:
            raise HTTPException(status_code=401, detail="Not logged in. Call login first.")
        if not program_id:
            raise HTTPException(status_code=400, detail="program_id is required for get_program_schema")
        try:
            return await client.get_program_schema(program_id, self.user_email)
        except Exception as e:
            logger.exception("get_program_schema failed")
            raise HTTPException(status_code=500, detail=str(e))

    async def run(self, input:dict):
        """
        Generic MCP run method.
        Accepts:
        - user_id / user_email (required for authentication)
        - action: login, upsert_deal, get_updates, list_vendors, list_programs
        - params (dict): optional dict of parameters for the action
        """
        if not input or not isinstance(input, dict):
            raise HTTPException(status_code=400, detail="payload must be a dictonary")
        
    
        action= input.get("action")
        user_id=input.get("user_id")
        params=input.get("params",{})
        
        if isinstance(params, str):
            import json
            try:
                params = json.loads(params)
            except Exception:
                raise HTTPException(status_code=400, detail="params must be a dictionary or valid JSON string")
        
        
        if not action:
            raise HTTPException(status_code=400, detail="No action provided for VartopiaTool")
        
        if not user_id:
            raise HTTPException(status_code=400,detail="user_id is required")
        
      
        if action != "login" and not user_id:
            raise HTTPException(status_code=400, detail="user_id is required")
                                
        logger.info(f"Running action '{action}' for user '{user_id}' with params:{params}")

        if action == "login":
            return await self.login(username=input.get("username", user_id),password=input.get("password"))
        elif action == "upsert_deal":
            return await self.upsert_deal(params)
        elif action == "get_updates":
            return await self.get_registration_updates(
                unique_id=params.get("unique_id", ""),
                varcrm_opportunity_id=params.get("varcrm_opportunity_id", ""),
                vartopia_transaction_id=params.get("vartopia_transaction_id", ""),
            )
        elif action == "list_vendors":
            return await self.list_vendors()
        elif action == "list_programs":
            return await self.list_programs(params.get("vendor_id"))
        elif action == "get_program_schema":
            return await self.get_program_schema(params.get("program_id"))
        else:
            raise HTTPException(status_code=400, detail=f"Unknown action: {action}")
