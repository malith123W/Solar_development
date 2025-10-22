#!/usr/bin/env python3
"""
Test script for NMD Analysis feature
Run this to verify the installation and basic functionality
"""

import sys
import os

def test_imports():
    """Test if all required modules can be imported"""
    print("Testing imports...")
    
    try:
        import pandas as pd
        print("✓ pandas imported successfully")
    except ImportError as e:
        print(f"✗ pandas import failed: {e}")
        return False
    
    try:
        import numpy as np
        print("✓ numpy imported successfully")
    except ImportError as e:
        print(f"✗ numpy import failed: {e}")
        return False
    
    try:
        from scipy.stats import pearsonr
        print("✓ scipy imported successfully")
    except ImportError as e:
        print(f"✗ scipy import failed: {e}")
        return False
    
    try:
        from sklearn.metrics import mean_squared_error
        print("✓ scikit-learn imported successfully")
    except ImportError as e:
        print(f"✗ scikit-learn import failed: {e}")
        return False
    
    try:
        from flask import Flask
        print("✓ Flask imported successfully")
    except ImportError as e:
        print(f"✗ Flask import failed: {e}")
        return False
    
    return True

def test_nmd_analysis_module():
    """Test if the NMD analysis module can be imported"""
    print("\nTesting NMD analysis module...")
    
    try:
        from nmd_analysis import NMDAnalysisProcessor
        print("✓ NMDAnalysisProcessor imported successfully")
        
        # Test instantiation
        processor = NMDAnalysisProcessor()
        print("✓ NMDAnalysisProcessor instantiated successfully")
        
        return True
    except ImportError as e:
        print(f"✗ NMD analysis module import failed: {e}")
        return False
    except Exception as e:
        print(f"✗ NMD analysis module test failed: {e}")
        return False

def test_app_integration():
    """Test if the app can be imported with the new module"""
    print("\nTesting app integration...")
    
    try:
        # Add current directory to path
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        
        from app import app
        print("✓ Flask app imported successfully")
        
        # Test if the new routes are registered
        routes = [rule.rule for rule in app.url_map.iter_rules()]
        nmd_routes = [route for route in routes if 'nmd_analysis' in route]
        
        if nmd_routes:
            print(f"✓ NMD analysis routes found: {nmd_routes}")
        else:
            print("✗ No NMD analysis routes found")
            return False
        
        return True
    except ImportError as e:
        print(f"✗ App import failed: {e}")
        return False
    except Exception as e:
        print(f"✗ App integration test failed: {e}")
        return False

def create_sample_data():
    """Create sample CSV files for testing"""
    print("\nCreating sample data files...")
    
    import pandas as pd
    import numpy as np
    from datetime import datetime, timedelta
    
    # Create sample feeder data
    start_time = datetime(2025, 1, 1, 0, 0, 0)
    times = [start_time + timedelta(minutes=i*15) for i in range(96)]  # 24 hours, 15-min intervals
    
    feeder_data = {
        'DATE': [t.strftime('%d/%m/%Y') for t in times],
        'TIME': [t.strftime('%H:%M:%S') for t in times],
        'PHASE_A': 230 + np.random.normal(0, 5, len(times)),
        'PHASE_B': 230 + np.random.normal(0, 5, len(times)),
        'PHASE_C': 230 + np.random.normal(0, 5, len(times))
    }
    
    feeder_df = pd.DataFrame(feeder_data)
    feeder_df.to_csv('sample_feeder.csv', index=False)
    print("✓ Sample feeder data created: sample_feeder.csv")
    
    # Create sample customer data
    for i in range(3):
        customer_times = [start_time + timedelta(minutes=j*15 + np.random.randint(-5, 5)) for j in range(96)]
        customer_data = {
            'DATE': [t.strftime('%d/%m/%Y') for t in customer_times],
            'TIME': [t.strftime('%H:%M:%S') for t in customer_times],
            'PHASE_A': 230 + np.random.normal(0, 8, len(customer_times)),
            'PHASE_B': 230 + np.random.normal(0, 8, len(customer_times)),
            'PHASE_C': 230 + np.random.normal(0, 8, len(customer_times))
        }
        
        customer_df = pd.DataFrame(customer_data)
        customer_df.to_csv(f'sample_customer_{i+1}.csv', index=False)
        print(f"✓ Sample customer data created: sample_customer_{i+1}.csv")
    
    return True

def main():
    """Run all tests"""
    print("NMD Analysis Feature Test Suite")
    print("=" * 40)
    
    all_tests_passed = True
    
    # Test imports
    if not test_imports():
        all_tests_passed = False
    
    # Test NMD analysis module
    if not test_nmd_analysis_module():
        all_tests_passed = False
    
    # Test app integration
    if not test_app_integration():
        all_tests_passed = False
    
    # Create sample data
    if not create_sample_data():
        all_tests_passed = False
    
    print("\n" + "=" * 40)
    if all_tests_passed:
        print("✓ All tests passed! NMD Analysis feature is ready to use.")
        print("\nTo test the feature:")
        print("1. Run: python app.py")
        print("2. Go to: http://localhost:5000/nmd_analysis")
        print("3. Upload the sample CSV files created in this directory")
    else:
        print("✗ Some tests failed. Please check the errors above.")
        print("\nTo install missing dependencies:")
        print("pip install -r requirements.txt")
    
    return all_tests_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

