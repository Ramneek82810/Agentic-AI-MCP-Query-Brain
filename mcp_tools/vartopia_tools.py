from sdk.tool import BaseTool
from fastapi import HTTPException
from api_client import client
import logging
import json

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
        # self.user_email = None
        # self.username=None
        # self.password=None

    async def login(self, username: str, password: str):
        if not username or not password:
            raise HTTPException(status_code=400, detail="username and password are required for login")
        
        logger.info(f"Attempting login with username={username} password={'*' * len(password)}")
        try:
            login_response = await client.login(username, password)
            
            
            if isinstance(login_response, str):
                try:
                    login_response = json.loads(login_response)
                except Exception as e:
                    logger.error("Failed to parse login response JSON")
                    raise HTTPException(status_code=500, detail=f"Invalid login response: {str(e)}")
                
            tokens = login_response.get("Tokens") or login_response.get("Data", {}).get("Tokens") or login_response.get("detail",{}).get("details",{}).get("Data",{}).get("Tokens")
            
            if not tokens or "AccessToken" not in tokens:
                raise HTTPException(
                    status_code=401,
                    detail=f"No AccessToken returned. Full login response: {login_response}"
                )

            self.access_token = tokens["AccessToken"]
            self.user_email = login_response.get("Email") or login_response.get("Data", {}).get("Email")

            self.username=username
            self.password=password
            
            logger.info(f"Login successful for {self.user_email}")
            
            return {
                "message": "Login successful",
                "access_token": self.access_token,
                "user_email": self.user_email,
            }

        except Exception as e:
            logger.exception("Vartopia login failed")
            raise HTTPException(status_code=500, detail=str(e))

    async def upsert_deal(self, deal_data: dict):
        if not self.access_token:
            raise HTTPException(status_code=401, detail="Not logged in. Call login first.")
        
        if not deal_data:
            raise HTTPException(status_code=400, detail="deal_data is required")
        
        logger.info(f"Submitting deal data:{json.dumps(deal_data)}")
        
        # payload={"deals":deal_data if isinstance(deal_data,list) else [deal_data]}
        # logger.info(f"Submitting deal data: {json.dumps(payload)}")
        
        required_keys=[
            "CommonFields", "CustomFields", "extensionAndRegUpdateDetails",
            "PrimarySalesRepDetails", "SubmitterDetails", "CustomerDetails",
            "ReviewerDetails", "flags"
        ] 
        for key in required_keys:
            if key not in deal_data:
                deal_data[key]={}
        
        payload = [deal_data] if isinstance(deal_data, dict) else deal_data
             
        try:
            return await client.submit_deal(
                access_token=self.access_token,
                user_email=self.user_email, 
                deal_data=payload
                )
            
        except Exception as e:
            logger.exception("upsert_deal failed")
            raise HTTPException(status_code=500, detail=str(e))

    async def get_registration_updates(self, unique_id="", varcrm_opportunity_id="", vartopia_transaction_id=""):
        if not self.access_token or not self.user_email:
            raise HTTPException(status_code=401, detail="Not logged in. Call login first.")
        try:
            return await client.get_registration_updates(
                access_token=self.access_token,
                user_email=self.user_email,
                unique_id=unique_id,
                varcrm_opportunity_id=varcrm_opportunity_id,
                vartopia_transaction_id=vartopia_transaction_id,
            )
        except Exception as e:
            logger.exception("get_registration_updates failed")
            raise HTTPException(status_code=500, detail=str(e))

    # async def list_vendors(self):
    #     if not self.access_token or not self.user_email or not self.username or not self.password:
    #         raise HTTPException(status_code=401, detail="Not logged in. Call login first.")
    #     try:
    #         return await client.get_vendors(
    #             access_token=self.access_token,
    #             user_email=self.user_email,
    #         )
    #     except Exception as e:
    #         logger.exception("list_vendors failed")
    #         raise HTTPException(status_code=500, detail=str(e))


    # async def list_programs(self, vendor_id: str):
    #     if not self.access_token or not self.user_email:
    #         raise HTTPException(status_code=401, detail="Not logged in. Call login first.")
    #     if not vendor_id:
    #         raise HTTPException(status_code=400, detail="vendor_id is required for list_programs")
    #     try:
    #         return await client.get_program(
    #                                         access_token=self.access_token,
    #                                         vendor_id=vendor_id,
    #                                         user_email=self.user_email
    #                                     )
    #     except Exception as e:
    #         logger.exception("list_programs failed")
    #         raise HTTPException(status_code=500, detail=str(e))



    # async def get_program_schema(self, program_id: str):
    #     if not self.access_token or not self.user_email:
    #         raise HTTPException(status_code=401, detail="Not logged in. Call login first.")
    #     if not program_id:
    #         raise HTTPException(status_code=400, detail="program_id is required for get_program_schema")
    #     try:
    #         return await client.get_program_schema(
    #                                                username=self.username,
    #                                                password=self.password,
    #                                                program_id=program_id,
    #                                                user_email=self.user_email
    #                                                )
    #     except Exception as e:
    #         logger.exception("get_program_schema failed")
    #         raise HTTPException(status_code=500, detail=str(e))

    async def run(self, input: dict):
        if not input or not isinstance(input, dict):
            raise HTTPException(status_code=400, detail="Input must be a dictionary")

        action = input.get("action")
        # user_id = input.get("user_id")
        params = input.get("params", {})

        if isinstance(params, str):
            try:
                params = json.loads(params)
            except Exception:
                raise HTTPException(status_code=400, detail="params must be a dictionary or valid JSON string")

        if not action:
            raise HTTPException(status_code=400, detail="No action provided for VartopiaTool")
        # if not user_id:
            # raise HTTPException(status_code=400, detail="user_id is required")

        logger.info(f"Running action '{action}' with params: {params}")

        if action == "login":
            return await self.login(params.get("username"),params.get("password"))

        elif action == "upsert_deal":
            return await self.upsert_deal(params)

        elif action in ["get_updates","get_registration_updates"]:
            return await self.get_registration_updates(
                unique_id=params.get("unique_id", ""),
                varcrm_opportunity_id=params.get("varcrm_opportunity_id", ""),
                vartopia_transaction_id=params.get("vartopia_transaction_id", ""),
            )

        # elif action == "list_vendors":
        #     return await self.list_vendors()

        # elif action == "list_programs":
        #     return await self.list_programs(params.get("vendor_id"))

        # elif action == "get_program_schema":
        #     return await self.get_program_schema(params.get("program_id"))

        else:
            raise HTTPException(status_code=400, detail=f"Unknown action: {action}")