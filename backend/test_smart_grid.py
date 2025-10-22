"""
Test Script for Smart Load Balancing & Forecasting
This script demonstrates the complete workflow
"""

import requests
import json
import pandas as pd
import time

API_URL = 'http://localhost:5000/api'
SESSION_ID = f'test_smart_grid_{int(time.time())}'


def print_section(title):
    """Print section header"""
    print('\n' + '='*60)
    print(f'  {title}')
    print('='*60 + '\n')


def test_generate_glm():
    """Test GLM file generation"""
    print_section('Test 1: Generate GridLAB-D GLM File')
    
    response = requests.post(
        f'{API_URL}/smart-grid/generate-glm',
        json={
            'session_id': SESSION_ID,
            'transformer_name': 'T1',
            'model_name': 'test_grid_model'
        }
    )
    
    result = response.json()
    print(f'Status: {response.status_code}')
    print(f'Response: {json.dumps(result, indent=2)}')
    
    return result.get('glm_file') if result.get('success') else None


def test_run_simulation(glm_file):
    """Test GridLAB-D simulation"""
    print_section('Test 2: Run GridLAB-D Simulation')
    
    if not glm_file:
        print('⚠️  Skipping: No GLM file available')
        return
    
    response = requests.post(
        f'{API_URL}/smart-grid/run-simulation',
        json={
            'glm_file': glm_file
        }
    )
    
    result = response.json()
    print(f'Status: {response.status_code}')
    
    if result.get('success'):
        print('✓ Simulation completed successfully')
        if result.get('results'):
            print(f'  - Transformer power data: {len(result["results"].get("transformer_power", [])) or "No"} records')
            print(f'  - Meter voltage data: {len(result["results"].get("meter_voltages", [])) or "No"} records')
    else:
        print(f'✗ Simulation failed: {result.get("error")}')
        if result.get('message'):
            print(f'  Info: {result.get("message")}')


def test_analyze_balance():
    """Test load balance analysis"""
    print_section('Test 3: Analyze Load Balance')
    
    response = requests.post(
        f'{API_URL}/smart-grid/analyze-balance',
        json={
            'session_id': SESSION_ID
        }
    )
    
    result = response.json()
    print(f'Status: {response.status_code}')
    
    if result.get('success'):
        analysis = result['analysis']
        stats = analysis.get('overall_stats', {})
        
        print('✓ Balance analysis completed')
        print(f'  - Total feeders: {stats.get("total_feeders", 0)}')
        print(f'  - Balanced feeders: {len(stats.get("balanced_feeders", []))}')
        print(f'  - Imbalanced feeders: {len(stats.get("imbalanced_feeders", []))}')
        
        # Show first feeder details
        feeder_analysis = analysis.get('feeder_analysis', {})
        if feeder_analysis:
            first_feeder = list(feeder_analysis.keys())[0]
            feeder_data = feeder_analysis[first_feeder]
            print(f'\n  Example: {first_feeder}')
            print(f'    - Imbalance: {feeder_data.get("imbalance_percentage", 0):.2f}%')
            print(f'    - Total load: {feeder_data.get("total_load_kw", 0):.2f} kW')
            print(f'    - Customers: {feeder_data.get("total_customers", 0)}')
    else:
        print(f'✗ Analysis failed: {result.get("error")}')


def test_suggest_balancing():
    """Test load balancing suggestions"""
    print_section('Test 4: Get Balancing Suggestions')
    
    response = requests.post(
        f'{API_URL}/smart-grid/suggest-balancing',
        json={
            'session_id': SESSION_ID
        }
    )
    
    result = response.json()
    print(f'Status: {response.status_code}')
    
    if result.get('success'):
        suggestions = result['suggestions']
        
        print('✓ Suggestions generated')
        print(f'  - Total suggestions: {suggestions.get("total_suggestions", 0)}')
        print(f'  - Estimated balanced feeders: {suggestions.get("estimated_balanced_feeders", 0)}')
        
        # Show first suggestion
        if suggestions.get('suggestions'):
            first = suggestions['suggestions'][0]
            print(f'\n  Example suggestion:')
            print(f'    - Customer: {first.get("customer_id")}')
            print(f'    - From: {first.get("from_phase")} → To: {first.get("to_phase")}')
            print(f'    - Load: {first.get("customer_load_kw", 0):.2f} kW')
            print(f'    - Expected improvement: {first.get("expected_improvement", {}).get("imbalance_reduction", 0):.4f}')
    else:
        print(f'✗ Suggestions failed: {result.get("error")}')


def test_simulate_balancing():
    """Test balancing simulation"""
    print_section('Test 5: Simulate Load Balancing')
    
    response = requests.post(
        f'{API_URL}/smart-grid/simulate-balancing',
        json={
            'session_id': SESSION_ID,
            'moves': []  # Use default suggestions
        }
    )
    
    result = response.json()
    print(f'Status: {response.status_code}')
    
    if result.get('success'):
        simulation = result['simulation']
        
        print('✓ Simulation completed')
        print(f'\n  Before balancing:')
        print(f'    - Avg imbalance: {simulation["before"]["avg_imbalance"]*100:.2f}%')
        print(f'    - Total load: {simulation["before"]["total_load_kw"]:.2f} kW')
        print(f'    - Avg voltage: {simulation["before"]["avg_voltage"]:.2f} V')
        
        print(f'\n  After balancing:')
        print(f'    - Avg imbalance: {simulation["after"]["avg_imbalance"]*100:.2f}%')
        print(f'    - Total load: {simulation["after"]["total_load_kw"]:.2f} kW')
        print(f'    - Avg voltage: {simulation["after"]["avg_voltage"]:.2f} V')
        
        print(f'\n  Improvements:')
        improvements = simulation['improvements']
        print(f'    - Imbalance reduction: {improvements["imbalance_reduction"]*100:.2f}%')
        print(f'    - Loss reduction: {improvements["loss_reduction_percentage"]:.2f}%')
        print(f'    - Voltage improvement: {improvements["voltage_improvement"]:.2f} V')
    else:
        print(f'✗ Simulation failed: {result.get("error")}')


def test_forecast(customer_id=None):
    """Test load forecasting"""
    print_section('Test 6: Load Forecasting')
    
    # Try with a customer from the session
    request_data = {
        'session_id': SESSION_ID,
        'model_type': 'prophet',
        'forecast_periods': 24  # 24 hours
    }
    
    if customer_id:
        request_data['customer_id'] = customer_id
    else:
        request_data['feeder_id'] = 'FEEDER_001'
    
    response = requests.post(
        f'{API_URL}/smart-grid/forecast',
        json=request_data
    )
    
    result = response.json()
    print(f'Status: {response.status_code}')
    
    if result.get('success'):
        print('✓ Forecast completed')
        print(f'  - Model: {result.get("model_type")}')
        
        metrics = result.get('metrics', {})
        print(f'  - MAE: {metrics.get("mae", 0):.2f}')
        print(f'  - RMSE: {metrics.get("rmse", 0):.2f}')
        print(f'  - MAPE: {metrics.get("mape", 0):.2f}%')
        
        forecast = result.get('forecast', {})
        if forecast.get('values'):
            print(f'  - Forecast points: {len(forecast["values"])}')
            print(f'  - First forecast value: {forecast["values"][0]:.2f}')
            print(f'  - Last forecast value: {forecast["values"][-1]:.2f}')
    else:
        print(f'✗ Forecast failed: {result.get("error")}')


def test_compare_models(customer_id=None):
    """Test model comparison"""
    print_section('Test 7: Compare Forecast Models')
    
    if not customer_id:
        print('⚠️  Skipping: Need valid customer ID')
        return
    
    response = requests.post(
        f'{API_URL}/smart-grid/compare-forecast-models',
        json={
            'session_id': SESSION_ID,
            'customer_id': customer_id,
            'forecast_periods': 24
        }
    )
    
    result = response.json()
    print(f'Status: {response.status_code}')
    
    if result.get('success'):
        comparison = result['comparison']
        
        print('✓ Model comparison completed')
        print(f'  - Best model: {comparison.get("best_model", "N/A")}')
        print(f'  - Best MAPE: {comparison.get("best_mape", 0):.2f}%')
        
        print('\n  Model Results:')
        for model_name, model_result in comparison.get('models', {}).items():
            if model_result.get('success'):
                metrics = model_result.get('metrics', {})
                print(f'    - {model_name.upper()}: MAE={metrics.get("mae", 0):.2f}, '
                      f'RMSE={metrics.get("rmse", 0):.2f}, '
                      f'MAPE={metrics.get("mape", 0):.2f}%')
            else:
                print(f'    - {model_name.upper()}: Failed')
    else:
        print(f'✗ Comparison failed: {result.get("error")}')


def test_dashboard():
    """Test dashboard data"""
    print_section('Test 8: Get Dashboard Data')
    
    response = requests.get(
        f'{API_URL}/smart-grid/dashboard-data',
        params={'session_id': SESSION_ID}
    )
    
    result = response.json()
    print(f'Status: {response.status_code}')
    
    if result.get('success'):
        dashboard = result['dashboard']
        
        print('✓ Dashboard data retrieved')
        print(f'  - Has analysis: {dashboard.get("has_analysis")}')
        print(f'  - Has balance analysis: {dashboard.get("has_balance_analysis")}')
        print(f'  - Has forecasts: {dashboard.get("has_forecasts")}')
        print(f'  - Total customers: {dashboard.get("total_customers")}')
        print(f'  - Total feeders: {dashboard.get("total_feeders")}')
    else:
        print(f'✗ Dashboard retrieval failed: {result.get("error")}')


def main():
    """Run all tests"""
    print('\n' + '🔋'*30)
    print('  Smart Load Balancing & Forecasting - Test Suite')
    print('🔋'*30)
    
    print(f'\nSession ID: {SESSION_ID}')
    print(f'API URL: {API_URL}')
    
    # Note: These tests assume you have already:
    # 1. Uploaded feeder NMD data
    # 2. Uploaded customer data
    # 3. Run NMD correlation analysis
    
    print('\n⚠️  Prerequisites:')
    print('  1. Backend server must be running (python backend/app.py)')
    print('  2. NMD analysis must be completed first')
    print('  3. Customer and feeder data must be uploaded')
    
    input('\nPress Enter to continue with tests...')
    
    # Run tests
    try:
        # Test 1: Generate GLM
        glm_file = test_generate_glm()
        
        # Test 2: Run simulation (optional, requires GridLAB-D)
        test_run_simulation(glm_file)
        
        # Test 3: Analyze balance
        test_analyze_balance()
        
        # Test 4: Get suggestions
        test_suggest_balancing()
        
        # Test 5: Simulate balancing
        test_simulate_balancing()
        
        # Test 6: Forecast
        test_forecast()
        
        # Test 7: Compare models (needs customer ID)
        # test_compare_models('CUSTOMER_12345')
        
        # Test 8: Dashboard
        test_dashboard()
        
        print_section('Test Summary')
        print('✓ All tests completed!')
        print('\nNote: Some tests may fail if prerequisites are not met.')
        print('Please ensure you have run NMD analysis with valid data first.')
        
    except requests.exceptions.ConnectionError:
        print('\n❌ Error: Could not connect to API server')
        print('Please ensure the backend server is running:')
        print('  cd backend')
        print('  python app.py')
    
    except Exception as e:
        print(f'\n❌ Unexpected error: {str(e)}')
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()

