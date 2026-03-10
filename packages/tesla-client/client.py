"""
Tesla Fleet API Client

Main client for interacting with Tesla Fleet API.
"""

import os
import asyncio
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import httpx
from urllib.parse import urlencode

from .models import VehicleData, TokenResponse
from .vehicle import Vehicle
from .exceptions import (
    TeslaAPIError,
    AuthenticationError,
    VehicleUnavailableError,
    RateLimitError,
    CommandFailedError,
    ServerError,
)


class TeslaFleetClient:
    """
    Tesla Fleet API Client
    
    Usage:
        client = TeslaFleetClient(
            client_id="your_client_id",
            client_secret="your_client_secret",
            region="cn"
        )
        
        # Authenticate
        auth_url = client.get_authorization_url()
        # ... redirect user to auth_url ...
        token = await client.exchange_code(code)
        
        # Get vehicles
        vehicles = await client.get_vehicles()
        
        # Get vehicle data
        vehicle = vehicles[0]
        data = await vehicle.get_vehicle_data()
    """
    
    # API Endpoints by region
    BASE_URLS = {
        "na": "https://fleet-api.prd.na.vn.cloud.tesla.com",
        "eu": "https://fleet-api.prd.eu.vn.cloud.tesla.com",
        "cn": "https://fleet-api.prd.cn.vn.cloud.tesla.cn",
    }
    
    AUTH_URLS = {
        "na": "https://auth.tesla.com/oauth2/v3/authorize",
        "eu": "https://auth.tesla.com/oauth2/v3/authorize",
        "cn": "https://auth.tesla.cn/oauth2/v3/authorize",
    }
    
    TOKEN_URLS = {
        "na": "https://auth.tesla.com/oauth2/v3/token",
        "eu": "https://auth.tesla.com/oauth2/v3/token",
        "cn": "https://auth.tesla.cn/oauth2/v3/token",
    }
    
    SCOPES = [
        "openid",
        "offline_access",
        "user_data",
        "vehicle_device_data",
        "vehicle_cmds",
        "vehicle_charging_cmds",
        "energy_device_data",
        "energy_cmds",
    ]
    
    def __init__(
        self,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        redirect_uri: Optional[str] = None,
        region: str = "cn",
        access_token: Optional[str] = None,
        refresh_token: Optional[str] = None,
        token_expires_at: Optional[datetime] = None,
    ):
        """
        Initialize Tesla Fleet API client.
        
        Args:
            client_id: OAuth client ID
            client_secret: OAuth client secret
            redirect_uri: OAuth redirect URI
            region: API region (na, eu, cn)
            access_token: Existing access token
            refresh_token: Existing refresh token
            token_expires_at: Token expiration time
        """
        self.client_id = client_id or os.getenv("TESLA_CLIENT_ID")
        self.client_secret = client_secret or os.getenv("TESLA_CLIENT_SECRET")
        self.redirect_uri = redirect_uri or os.getenv("TESLA_REDIRECT_URI")
        self.region = region.lower()
        
        if self.region not in self.BASE_URLS:
            raise ValueError(f"Invalid region: {region}. Must be one of: {list(self.BASE_URLS.keys())}")
        
        self.base_url = self.BASE_URLS[self.region]
        self.auth_url = self.AUTH_URLS[self.region]
        self.token_url = self.TOKEN_URLS[self.region]
        
        self._access_token = access_token
        self._refresh_token = refresh_token
        self._token_expires_at = token_expires_at
        
        self._client: Optional[httpx.AsyncClient] = None
    
    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None or self._client.is_closed:
            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json",
            }
            if self._access_token:
                headers["Authorization"] = f"Bearer {self._access_token}"
            
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                headers=headers,
                timeout=30.0,
            )
        return self._client
    
    async def _request(
        self,
        method: str,
        endpoint: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Make API request with error handling."""
        client = await self._get_client()
        
        # Check token expiration
        if self._token_expires_at and datetime.utcnow() >= self._token_expires_at:
            await self._refresh_access_token()
        
        try:
            response = await client.request(method, endpoint, **kwargs)
            
            if response.status_code == 429:
                raise RateLimitError("API rate limit exceeded. Please try again later.", 429)
            elif response.status_code == 401:
                raise AuthenticationError("Authentication failed. Please check your credentials.", 401)
            elif response.status_code == 408:
                raise VehicleUnavailableError("Vehicle is offline or unavailable.", 408)
            elif response.status_code >= 500:
                raise ServerError(f"Tesla server error: {response.status_code}", response.status_code)
            elif response.status_code >= 400:
                raise TeslaAPIError(
                    f"API error: {response.status_code}",
                    response.status_code,
                    response.json() if response.text else None
                )
            
            response.raise_for_status()
            return response.json() if response.text else {}
            
        except httpx.HTTPStatusError as e:
            raise TeslaAPIError(f"HTTP error: {e.response.status_code}", e.response.status_code)
        except httpx.RequestError as e:
            raise TeslaAPIError(f"Request failed: {str(e)}")
    
    async def _refresh_access_token(self) -> None:
        """Refresh access token using refresh token."""
        if not self._refresh_token:
            raise AuthenticationError("No refresh token available")
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.token_url,
                json={
                    "grant_type": "refresh_token",
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "refresh_token": self._refresh_token,
                },
            )
            
            if response.status_code != 200:
                raise AuthenticationError(f"Failed to refresh token: {response.text}")
            
            data = response.json()
            self._access_token = data["access_token"]
            self._refresh_token = data.get("refresh_token", self._refresh_token)
            expires_in = data.get("expires_in", 3600)
            self._token_expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
            
            # Update client headers
            if self._client:
                self._client.headers["Authorization"] = f"Bearer {self._access_token}"
    
    def get_authorization_url(self, state: Optional[str] = None) -> str:
        """
        Generate OAuth authorization URL.
        
        Args:
            state: Optional state parameter for security
            
        Returns:
            Authorization URL to redirect user to
        """
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "response_type": "code",
            "scope": " ".join(self.SCOPES),
            "prompt": "login",
        }
        if state:
            params["state"] = state
        
        return f"{self.auth_url}?{urlencode(params)}"
    
    async def exchange_code(self, code: str) -> TokenResponse:
        """
        Exchange authorization code for access token.
        
        Args:
            code: Authorization code from callback
            
        Returns:
            TokenResponse with access_token and refresh_token
        """
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.token_url,
                json={
                    "grant_type": "authorization_code",
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "code": code,
                    "redirect_uri": self.redirect_uri,
                },
            )
            
            if response.status_code != 200:
                raise AuthenticationError(f"Failed to exchange code: {response.text}")
            
            data = response.json()
            self._access_token = data["access_token"]
            self._refresh_token = data["refresh_token"]
            expires_in = data.get("expires_in", 3600)
            self._token_expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
            
            return TokenResponse(
                access_token=self._access_token,
                refresh_token=self._refresh_token,
                expires_in=expires_in,
            )
    
    async def get_vehicles(self) -> List[Vehicle]:
        """
        Get list of vehicles associated with account.
        
        Returns:
            List of Vehicle objects
        """
        data = await self._request("GET", "/api/1/vehicles")
        vehicles = []
        for v in data.get("response", []):
            vehicle = Vehicle(self, v)
            vehicles.append(vehicle)
        return vehicles
    
    async def get_vehicle(self, vin: str) -> Optional[Vehicle]:
        """
        Get specific vehicle by VIN.
        
        Args:
            vin: Vehicle VIN
            
        Returns:
            Vehicle object or None if not found
        """
        vehicles = await self.get_vehicles()
        for v in vehicles:
            if v.vin == vin:
                return v
        return None
    
    async def get_user(self) -> Dict[str, Any]:
        """
        Get user information.
        
        Returns:
            User data dictionary
        """
        return await self._request("GET", "/api/1/users/me")
    
    async def close(self) -> None:
        """Close HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
