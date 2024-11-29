def calculate_market_indicators(token_data, token_file):
    """
    Calculate various market indicators for risk assessment
    """
    try:
        # Price-based indicators
        close_prices = token_data['Close']
        current_price = close_prices.iloc[-1]
        price_change = calculate_price_change(token_data)
        volatility = close_prices.pct_change().std() * 100

        # Volume-based indicators
        volume = token_data['Volume']
        current_volume = volume.iloc[-1]
        avg_volume = volume.mean()
        volume_change = ((current_volume - volume.iloc[-2]) / volume.iloc[-2]) * 100

        # Market cap indicators
        market_cap = token_data['Market Cap']
        current_market_cap = market_cap.iloc[-1]
        market_cap_change = ((current_market_cap - market_cap.iloc[-2]) / market_cap.iloc[-2]) * 100

        # Calculate different risk combinations
        result1 = risk_client.call_rpc(
            "mul", 
            "Numbers",
            a=volatility,
            b=abs(price_change)
        )
        
        result2 = risk_client.call_rpc(
            "mul",
            "Numbers",
            a=volume_change,
            b=price_change
        )
        
        result3 = risk_client.call_rpc(
            "mul",
            "Numbers",
            a=market_cap_change,
            b=volatility
        )

        return {
            "token_name": os.path.splitext(token_file)[0],
            "assessment_date": datetime.now().isoformat(),
            "price_metrics": {
                "current_price": current_price,
                "price_change_24h": price_change,
                "volatility": volatility,
                "volatility_risk_score": result1
            },
            "volume_metrics": {
                "current_volume": current_volume,
                "average_volume": avg_volume,
                "volume_change_24h": volume_change,
                "volume_risk_score": result2
            },
            "market_cap_metrics": {
                "current_market_cap": current_market_cap,
                "market_cap_change_24h": market_cap_change,
                "market_cap_risk_score": result3
            },
            "combined_risk_scores": {
                "price_volume_risk": (result1 + result2) / 2,
                "price_market_cap_risk": (result1 + result3) / 2,
                "overall_risk_score": (result1 + result2 + result3) / 3
            }
        }
    except Exception as e:
        print(f"Error calculating market indicators: {str(e)}")
        raise

def get_risk_assessment(token_file):
    """
    Get risk assessment for a specific token
    """
    try:
        # Load token data
        token_data = load_token_data(token_file)
        
        # Calculate market indicators and risk scores
        assessment_result = calculate_market_indicators(token_data, token_file)
        
        print(f"\nRisk Assessment Results for {assessment_result['token_name']}:")
        print(f"Assessment Date: {assessment_result['assessment_date']}")
        
        print("\nPrice Metrics:")
        for key, value in assessment_result['price_metrics'].items():
            print(f"- {key}: {value:.2f}")
        
        print("\nVolume Metrics:")
        for key, value in assessment_result['volume_metrics'].items():
            print(f"- {key}: {value:.2f}")
        
        print("\nMarket Cap Metrics:")
        for key, value in assessment_result['market_cap_metrics'].items():
            print(f"- {key}: {value:.2f}")
        
        print("\nCombined Risk Scores:")
        for key, value in assessment_result['combined_risk_scores'].items():
            print(f"- {key}: {value:.2f}")
        
        return assessment_result
        
    except Exception as e:
        print(f"Error assessing risk for {token_file}: {str(e)}")
        raise