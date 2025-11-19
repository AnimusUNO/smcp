#!/usr/bin/env python3
"""
Aster API Client - Wrapper for Aster Finance API interactions

Handles authentication, request signing, and API communication.
"""

import hmac
import hashlib
import time
import logging
import requests
from typing import Dict, Any, Optional

logger = logging.getLogger("vibing.aster_client")


class AsterClient:
    """Wrapper for Aster API interactions"""
    
    def __init__(self, api_key: Optional[str] = None, api_secret: Optional[str] = None):
        self.base_url = "https://sapi.asterdex.com"
        self.api_key = api_key
        self.api_secret = api_secret
        
    def _get_signature(self, params: Dict[str, Any]) -> str:
        """Generate HMAC SHA256 signature for authenticated endpoints"""
        query_string = '&'.join([f"{k}={str(v)}" for k, v in sorted(params.items())])
        return hmac.new(
            self.api_secret.encode('utf-8'),
            query_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
    def _request(self, method: str, endpoint: str, params: Dict[str, Any] = None, signed: bool = False) -> Dict[str, Any]:
        """Make request to Aster API"""
        
        url = f"{self.base_url}{endpoint}"
        headers = {}
        
        if self.api_key:
            headers['X-MBX-APIKEY'] = self.api_key
            
        if signed:
            if not params:
                params = {}
            params['timestamp'] = int(time.time() * 1000)
            # Generate signature BEFORE adding it to params
            signature = self._get_signature(params)
            params['signature'] = signature
            
        try:
            if method == 'POST' and signed:
                # For POST requests with signatures, send data in request body as query string format
                # Set Content-Type header for form data
                headers['Content-Type'] = 'application/x-www-form-urlencoded'
                # Convert params dict to query string format for request body
                request_body = '&'.join([f"{k}={str(v)}" for k, v in sorted(params.items())])
                response = requests.post(url, headers=headers, data=request_body)
            elif method == 'GET' and signed:
                # For GET requests with signatures, manually construct query string to match signature exactly
                # Use the same format as signature generation: sorted params with string values
                query_string = '&'.join([f"{k}={str(v)}" for k, v in sorted(params.items())])
                full_url = f"{url}?{query_string}"
                response = requests.get(full_url, headers=headers)
            else:
                # For unsigned requests, send params in query string
                response = requests.request(method, url, headers=headers, params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"API request failed: {str(e)}")
            raise

    def get_symbol_filters(self, symbol: str) -> Dict[str, Any]:
        """Fetch exchange filters for a symbol (LOT_SIZE, MARKET_LOT_SIZE, MIN_NOTIONAL)."""
        try:
            info = self._request('GET', '/api/v1/exchangeInfo', {"symbol": symbol})
            # Some APIs return {symbols:[{symbol, filters:[...] }]} ; normalize
            symbols = info.get('symbols') if isinstance(info, dict) else None
            if isinstance(symbols, list):
                match = next((s for s in symbols if s.get('symbol') == symbol), None)
                if match:
                    filters = match.get('filters', [])
                else:
                    filters = []
            elif isinstance(info, list):
                match = next((s for s in info if s.get('symbol') == symbol), None)
                filters = match.get('filters', []) if match else []
            else:
                filters = info.get('filters', []) if isinstance(info, dict) else []

            result = {}
            for f in filters:
                ftype = f.get('filterType') or f.get('type')
                if ftype in ['LOT_SIZE', 'MARKET_LOT_SIZE', 'MIN_NOTIONAL']:
                    result[ftype] = f
            return result
        except Exception as e:
            logger.warning(f"Could not fetch exchange filters for {symbol}: {e}")
            return {}

