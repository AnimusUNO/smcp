#!/usr/bin/env python3
"""
CoinMarketCap CLI Plugin

Provides cryptocurrency market data from CoinMarketCap API.

Environment:
  - CMC_API_KEY: Your CoinMarketCap API key (required)

Available endpoints:
  - Get latest price and market data for cryptocurrencies
  - Get global market metrics
  - Search for cryptocurrencies by name/symbol
"""

import argparse
import json
import os
import sys
from typing import Any, Dict, Optional

import requests


CMC_BASE_URL = "https://pro-api.coinmarketcap.com/v1"


def get_headers() -> Dict[str, str]:
    """Get API headers with authentication."""
    api_key = os.getenv("CMC_API_KEY")
    if not api_key:
        raise ValueError("CMC_API_KEY not set in environment")
    return {
        "X-CMC_PRO_API_KEY": api_key,
        "Accept": "application/json"
    }


def get_price(args: Dict[str, Any]) -> Dict[str, Any]:
    """Get latest price and market data for cryptocurrencies."""
    symbol = args.get("symbol")
    slug = args.get("slug")
    
    if not symbol and not slug:
        return {"error": "Provide either --symbol or --slug"}
    
    try:
        params = {}
        if symbol:
            params["symbol"] = symbol.upper()
        if slug:
            params["slug"] = slug.lower()
        
        # Add convert currency (default USD)
        params["convert"] = args.get("convert", "USD").upper()
        
        response = requests.get(
            f"{CMC_BASE_URL}/cryptocurrency/quotes/latest",
            headers=get_headers(),
            params=params,
            timeout=10
        )
        response.raise_for_status()
        
        data = response.json()
        
        if data.get("status", {}).get("error_code") != 0:
            return {"error": data.get("status", {}).get("error_message", "API error")}
        
        # Extract first cryptocurrency from response
        crypto_data = data.get("data", {})
        if symbol:
            crypto = crypto_data.get(symbol.upper())
        else:
            # For slug queries, get first result
            crypto = next(iter(crypto_data.values())) if crypto_data else None
        
        if not crypto:
            return {"error": "Cryptocurrency not found"}
        
        convert_currency = args.get("convert", "USD").upper()
        quote = crypto.get("quote", {}).get(convert_currency, {})
        
        # Return comprehensive market data with flattened key metrics
        result = {
            "id": crypto.get("id"),
            "name": crypto.get("name"),
            "symbol": crypto.get("symbol"),
            "slug": crypto.get("slug"),
            "cmc_rank": crypto.get("cmc_rank"),
            "num_market_pairs": crypto.get("num_market_pairs"),
            "date_added": crypto.get("date_added"),
            "max_supply": crypto.get("max_supply"),
            "circulating_supply": crypto.get("circulating_supply"),
            "total_supply": crypto.get("total_supply"),
            "is_active": crypto.get("is_active"),
            "platform": crypto.get("platform"),  # Token platform info (e.g., ERC-20)
            "tags": crypto.get("tags", []),
            # Flatten key quote metrics to top level for easy access
            "price": quote.get("price"),
            "market_cap": quote.get("market_cap"),
            "market_cap_dominance": quote.get("market_cap_dominance"),
            "fully_diluted_market_cap": quote.get("fully_diluted_market_cap"),
            "volume_24h": quote.get("volume_24h"),
            "volume_change_24h": quote.get("volume_change_24h"),
            "percent_change_1h": quote.get("percent_change_1h"),
            "percent_change_24h": quote.get("percent_change_24h"),
            "percent_change_7d": quote.get("percent_change_7d"),
            "percent_change_30d": quote.get("percent_change_30d"),
            "percent_change_60d": quote.get("percent_change_60d"),
            "percent_change_90d": quote.get("percent_change_90d"),
            "tvl": quote.get("tvl"),  # Total Value Locked (for DeFi tokens)
            # Keep full quote data for reference
            "quote": {
                "currency": convert_currency,
                "price": quote.get("price"),
                "volume_24h": quote.get("volume_24h"),
                "volume_change_24h": quote.get("volume_change_24h"),
                "percent_change_1h": quote.get("percent_change_1h"),
                "percent_change_24h": quote.get("percent_change_24h"),
                "percent_change_7d": quote.get("percent_change_7d"),
                "percent_change_30d": quote.get("percent_change_30d"),
                "percent_change_60d": quote.get("percent_change_60d"),
                "percent_change_90d": quote.get("percent_change_90d"),
                "market_cap": quote.get("market_cap"),
                "market_cap_dominance": quote.get("market_cap_dominance"),
                "fully_diluted_market_cap": quote.get("fully_diluted_market_cap"),
                "tvl": quote.get("tvl"),
                "last_updated": quote.get("last_updated")
            }
        }
        
        return result
    
    except requests.exceptions.RequestException as e:
        return {"error": f"API request failed: {str(e)}"}
    except Exception as e:
        return {"error": str(e)}


def search(args: Dict[str, Any]) -> Dict[str, Any]:
    """Search for cryptocurrencies by name or symbol."""
    query = args.get("query")
    
    if not query:
        return {"error": "Missing required argument: query"}
    
    try:
        # Use the map endpoint to search
        response = requests.get(
            f"{CMC_BASE_URL}/cryptocurrency/map",
            headers=get_headers(),
            params={"symbol": query.upper()},
            timeout=10
        )
        
        # If symbol search fails, try listing and filter
        if response.status_code != 200:
            return {"error": f"Search failed: {response.status_code}"}
        
        data = response.json()
        
        if data.get("status", {}).get("error_code") != 0:
            return {"error": data.get("status", {}).get("error_message", "API error")}
        
        results = data.get("data", [])
        
        # Limit results
        limit = int(args.get("limit", 10))
        results = results[:limit]
        
        return {
            "results": [
                {
                    "id": crypto.get("id"),
                    "name": crypto.get("name"),
                    "symbol": crypto.get("symbol"),
                    "slug": crypto.get("slug"),
                    "rank": crypto.get("rank"),
                    "is_active": crypto.get("is_active", 1)
                }
                for crypto in results
            ]
        }
    
    except Exception as e:
        return {"error": str(e)}


def get_info(args: Dict[str, Any]) -> Dict[str, Any]:
    """Get comprehensive information about a cryptocurrency including metadata."""
    symbol = args.get("symbol")
    slug = args.get("slug")
    
    if not symbol and not slug:
        return {"error": "Provide either --symbol or --slug"}
    
    try:
        # Get metadata
        params = {}
        if symbol:
            params["symbol"] = symbol.upper()
        if slug:
            params["slug"] = slug.lower()
        
        response = requests.get(
            f"{CMC_BASE_URL}/cryptocurrency/info",
            headers=get_headers(),
            params=params,
            timeout=10
        )
        response.raise_for_status()
        
        info_data = response.json()
        
        if info_data.get("status", {}).get("error_code") != 0:
            return {"error": info_data.get("status", {}).get("error_message", "API error")}
        
        # Get price data
        price_data = get_price(args)
        
        # Extract cryptocurrency info
        crypto_info = info_data.get("data", {})
        if symbol:
            info = crypto_info.get(symbol.upper())
        else:
            info = next(iter(crypto_info.values())) if crypto_info else None
        
        if not info:
            return {"error": "Cryptocurrency not found"}
        
        # Extract key market metrics from price_data for easy access
        quote_data = {}
        if price_data and "error" not in price_data and "quote" in price_data:
            quote_data = price_data.get("quote", {})
        
        # Combine metadata and price data with flattened key metrics
        return {
            "basic_info": {
                "id": info.get("id"),
                "name": info.get("name"),
                "symbol": info.get("symbol"),
                "slug": info.get("slug"),
                "category": info.get("category"),
                "description": info.get("description"),
                "logo": info.get("logo"),
                "tags": info.get("tags", []),
                "platform": info.get("platform"),  # Token contract info
                "date_added": info.get("date_added"),
                "date_launched": info.get("date_launched")
            },
            # Flatten key market metrics for easy access
            "price": quote_data.get("price"),
            "market_cap": quote_data.get("market_cap"),
            "market_cap_rank": price_data.get("cmc_rank") if price_data and "error" not in price_data else None,
            "volume_24h": quote_data.get("volume_24h"),
            "percent_change_24h": quote_data.get("percent_change_24h"),
            "percent_change_7d": quote_data.get("percent_change_7d"),
            "circulating_supply": price_data.get("circulating_supply") if price_data and "error" not in price_data else None,
            "total_supply": price_data.get("total_supply") if price_data and "error" not in price_data else None,
            "max_supply": price_data.get("max_supply") if price_data and "error" not in price_data else None,
            "urls": {
                "website": info.get("urls", {}).get("website", []),
                "explorer": info.get("urls", {}).get("explorer", []),
                "source_code": info.get("urls", {}).get("source_code", []),
                "message_board": info.get("urls", {}).get("message_board", []),
                "chat": info.get("urls", {}).get("chat", []),
                "announcement": info.get("urls", {}).get("announcement", []),
                "reddit": info.get("urls", {}).get("reddit", []),
                "twitter": info.get("urls", {}).get("twitter", [])
            },
            "contract_address": info.get("contract_address", []),
            "full_market_data": price_data if "error" not in price_data else None
        }
    
    except Exception as e:
        return {"error": str(e)}


def global_metrics(args: Dict[str, Any]) -> Dict[str, Any]:
    """Get global cryptocurrency market metrics."""
    try:
        convert = args.get("convert", "USD").upper()
        
        response = requests.get(
            f"{CMC_BASE_URL}/global-metrics/quotes/latest",
            headers=get_headers(),
            params={"convert": convert},
            timeout=10
        )
        response.raise_for_status()
        
        data = response.json()
        
        if data.get("status", {}).get("error_code") != 0:
            return {"error": data.get("status", {}).get("error_message", "API error")}
        
        metrics = data.get("data", {})
        quote = metrics.get("quote", {}).get(convert, {})
        
        return {
            "active_cryptocurrencies": metrics.get("active_cryptocurrencies"),
            "active_exchanges": metrics.get("active_exchanges"),
            "active_market_pairs": metrics.get("active_market_pairs"),
            "total_market_cap": quote.get("total_market_cap"),
            "total_volume_24h": quote.get("total_volume_24h"),
            "btc_dominance": metrics.get("btc_dominance"),
            "eth_dominance": metrics.get("eth_dominance"),
            "last_updated": quote.get("last_updated")
        }
    
    except Exception as e:
        return {"error": str(e)}


def main():
    parser = argparse.ArgumentParser(
        description="CoinMarketCap API tools",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Available commands:
  get-price         Get latest price and market data for a cryptocurrency
  get-info          Get comprehensive information including metadata, description, links, and contract addresses
  search            Search for cryptocurrencies by name or symbol
  global-metrics    Get global cryptocurrency market metrics

Examples:
  python cli.py get-price --symbol BTC
  python cli.py get-info --symbol ETH --convert USD
  python cli.py get-info --slug wrapped-bitcoin
  python cli.py search --query ethereum
  python cli.py global-metrics --convert USD
        """
    )

    sub = parser.add_subparsers(dest="command", help="Available commands")

    # get-price
    p_price = sub.add_parser("get-price", help="Get price and market data")
    p_price.add_argument("--symbol", help="Cryptocurrency symbol (e.g., BTC, ETH)")
    p_price.add_argument("--slug", help="Cryptocurrency slug (e.g., bitcoin, ethereum)")
    p_price.add_argument("--convert", default="USD", help="Convert to currency (default: USD)")

    # get-info
    p_info = sub.add_parser("get-info", help="Get comprehensive cryptocurrency information")
    p_info.add_argument("--symbol", help="Cryptocurrency symbol (e.g., BTC, ETH)")
    p_info.add_argument("--slug", help="Cryptocurrency slug (e.g., bitcoin, ethereum)")
    p_info.add_argument("--convert", default="USD", help="Convert to currency (default: USD)")

    # search
    p_search = sub.add_parser("search", help="Search for cryptocurrencies")
    p_search.add_argument("--query", required=True, help="Search query (name or symbol)")
    p_search.add_argument("--limit", default="10", help="Max results (default: 10)")

    # global-metrics
    p_global = sub.add_parser("global-metrics", help="Get global market metrics")
    p_global.add_argument("--convert", default="USD", help="Convert to currency (default: USD)")

    args_ns = parser.parse_args()

    if not getattr(args_ns, "command", None):
        parser.print_help()
        sys.exit(1)

    args = vars(args_ns)
    try:
        if args_ns.command == "get-price":
            out = get_price(args)
        elif args_ns.command == "get-info":
            out = get_info(args)
        elif args_ns.command == "search":
            out = search(args)
        elif args_ns.command == "global-metrics":
            out = global_metrics(args)
        else:
            out = {"error": f"Unknown command: {args_ns.command}"}
        print(json.dumps(out))
        sys.exit(0 if "error" not in out else 1)
    except Exception as e:
        print(json.dumps({"error": str(e)}))
        sys.exit(1)


if __name__ == "__main__":
    main()

