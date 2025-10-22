"""
Load Forecasting Module
Implements ARIMA, Prophet, and LSTM models for load prediction
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')


class LoadForecaster:
    """Handles load forecasting using multiple ML/AI models"""
    
    def __init__(self):
        self.models = {}
        self.forecasts = {}
    
    def _to_json_safe(self, obj):
        """Convert numpy/pandas types to JSON-serializable Python types"""
        if obj is None or isinstance(obj, (str, int, bool)):
            return obj
        elif isinstance(obj, float):
            # Handle NaN and Infinity
            if np.isnan(obj) or np.isinf(obj):
                return 0.0
            return obj
        elif isinstance(obj, (np.integer, np.floating)):
            val = obj.item()
            # Handle NaN and Infinity
            if isinstance(val, float) and (np.isnan(val) or np.isinf(val)):
                return 0.0
            return val
        elif isinstance(obj, np.bool_):
            return bool(obj)
        elif isinstance(obj, np.ndarray):
            # Handle NaN and Inf in arrays
            arr = obj.copy()
            if arr.dtype.kind == 'f':  # floating point
                arr = np.where(np.isnan(arr) | np.isinf(arr), 0.0, arr)
            return arr.tolist()
        elif isinstance(obj, pd.Timestamp):
            return obj.isoformat()
        elif isinstance(obj, dict):
            return {k: self._to_json_safe(v) for k, v in obj.items()}
        elif isinstance(obj, (list, tuple)):
            return [self._to_json_safe(item) for item in obj]
        else:
            return obj
    
    def forecast_with_arima(self, load_data: pd.DataFrame, 
                           forecast_periods: int = 168) -> Dict[str, Any]:
        """
        Forecast using ARIMA (AutoRegressive Integrated Moving Average)
        
        Args:
            load_data: DataFrame with 'datetime' and 'load_kw' columns
            forecast_periods: Number of periods to forecast (default: 168 = 1 week hourly)
            
        Returns:
            Dictionary with forecast results
        """
        try:
            from statsmodels.tsa.arima.model import ARIMA
            from statsmodels.tsa.stattools import adfuller
        except ImportError:
            return {
                'success': False,
                'error': 'statsmodels not installed. Install with: pip install statsmodels'
            }
        
        try:
            # Prepare data
            if 'datetime' not in load_data.columns:
                return {'success': False, 'error': 'datetime column required'}
            
            # Extract load column
            load_col = self._find_load_column(load_data)
            if not load_col:
                return {'success': False, 'error': 'No load column found'}
            
            # Ensure sorted by time
            df = load_data.sort_values('datetime').copy()
            df['load_kw'] = pd.to_numeric(df[load_col], errors='coerce')
            df = df.dropna(subset=['load_kw'])
            
            if len(df) < 50:
                return {'success': False, 'error': 'Insufficient data points (need at least 50)'}
            
            # Check stationarity
            adf_result = adfuller(df['load_kw'].values)
            is_stationary = adf_result[1] < 0.05
            
            # Auto-select ARIMA parameters (simplified)
            p, d, q = self._auto_select_arima_params(df['load_kw'], is_stationary)
            
            # Fit ARIMA model
            model = ARIMA(df['load_kw'].values, order=(p, d, q))
            fitted_model = model.fit()
            
            # Generate forecast
            forecast = fitted_model.forecast(steps=forecast_periods)
            
            # Calculate confidence intervals (95%)
            forecast_std = np.std(df['load_kw'])
            lower_bound = forecast - 1.96 * forecast_std
            upper_bound = forecast + 1.96 * forecast_std
            
            # Generate future timestamps
            last_time = df['datetime'].max()
            time_delta = self._estimate_time_delta(df)
            future_times = [last_time + (i + 1) * time_delta for i in range(forecast_periods)]
            
            # Calculate model performance metrics
            fitted_values = fitted_model.fittedvalues
            actual_values = df['load_kw'].values[-len(fitted_values):]
            
            mae = np.mean(np.abs(fitted_values - actual_values))
            rmse = np.sqrt(np.mean((fitted_values - actual_values) ** 2))
            
            # Calculate MAPE safely, avoiding division by zero
            non_zero_mask = actual_values != 0
            if np.sum(non_zero_mask) > 0:
                mape = np.mean(np.abs((actual_values[non_zero_mask] - fitted_values[non_zero_mask]) / actual_values[non_zero_mask])) * 100
            else:
                mape = 0.0
            
            result = {
                'success': True,
                'model_type': 'ARIMA',
                'model_params': {'p': p, 'd': d, 'q': q},
                'forecast': {
                    'timestamps': [str(t) for t in future_times],
                    'values': forecast.tolist(),
                    'lower_bound': lower_bound.tolist(),
                    'upper_bound': upper_bound.tolist()
                },
                'metrics': {
                    'mae': float(mae),
                    'rmse': float(rmse),
                    'mape': float(mape)
                },
                'historical': {
                    'timestamps': [str(t) for t in df['datetime'].tolist()],
                    'values': df['load_kw'].tolist(),
                    'fitted_values': fitted_values.tolist()
                }
            }
            
            return self._to_json_safe(result)
            
        except Exception as e:
            return {
                'success': False,
                'error': f'ARIMA forecasting failed: {str(e)}'
            }
    
    def forecast_with_prophet(self, load_data: pd.DataFrame,
                             forecast_periods: int = 168) -> Dict[str, Any]:
        """
        Forecast using Facebook Prophet
        
        Args:
            load_data: DataFrame with 'datetime' and load column
            forecast_periods: Number of periods to forecast
            
        Returns:
            Dictionary with forecast results
        """
        try:
            from prophet import Prophet
        except ImportError:
            return {
                'success': False,
                'error': 'Prophet not installed. Install with: pip install prophet'
            }
        
        try:
            # Prepare data
            load_col = self._find_load_column(load_data)
            if not load_col:
                return {'success': False, 'error': 'No load column found'}
            
            df = load_data.sort_values('datetime').copy()
            
            # Prophet requires 'ds' and 'y' columns
            prophet_df = pd.DataFrame({
                'ds': pd.to_datetime(df['datetime']),
                'y': pd.to_numeric(df[load_col], errors='coerce')
            })
            prophet_df = prophet_df.dropna()
            
            if len(prophet_df) < 50:
                return {'success': False, 'error': 'Insufficient data points'}
            
            # Initialize and fit Prophet model
            model = Prophet(
                daily_seasonality=True,
                weekly_seasonality=True,
                yearly_seasonality=False,  # Usually not enough data
                changepoint_prior_scale=0.05
            )
            
            model.fit(prophet_df)
            
            # Create future dataframe
            time_delta = self._estimate_time_delta(df)
            future = model.make_future_dataframe(
                periods=forecast_periods,
                freq=self._timedelta_to_freq(time_delta)
            )
            
            # Generate forecast
            forecast = model.predict(future)
            
            # Extract forecast data
            forecast_data = forecast[forecast['ds'] > prophet_df['ds'].max()]
            
            # Calculate metrics on training data
            train_pred = forecast[forecast['ds'].isin(prophet_df['ds'])]
            actual = prophet_df['y'].values
            predicted = train_pred['yhat'].values[:len(actual)]
            
            mae = np.mean(np.abs(actual - predicted))
            rmse = np.sqrt(np.mean((actual - predicted) ** 2))
            
            # Calculate MAPE safely, avoiding division by zero
            non_zero_mask = actual != 0
            if np.sum(non_zero_mask) > 0:
                mape = np.mean(np.abs((actual[non_zero_mask] - predicted[non_zero_mask]) / actual[non_zero_mask])) * 100
            else:
                mape = 0.0
            
            result = {
                'success': True,
                'model_type': 'Prophet',
                'forecast': {
                    'timestamps': [str(t) for t in forecast_data['ds'].tolist()],
                    'values': forecast_data['yhat'].tolist(),
                    'lower_bound': forecast_data['yhat_lower'].tolist(),
                    'upper_bound': forecast_data['yhat_upper'].tolist()
                },
                'metrics': {
                    'mae': float(mae),
                    'rmse': float(rmse),
                    'mape': float(mape)
                },
                'historical': {
                    'timestamps': [str(t) for t in prophet_df['ds'].tolist()],
                    'values': prophet_df['y'].tolist(),
                    'fitted_values': predicted.tolist()
                },
                'components': {
                    'trend': forecast_data['trend'].tolist(),
                    'weekly': forecast_data.get('weekly', [0] * len(forecast_data)).tolist() if 'weekly' in forecast_data.columns else None,
                    'daily': forecast_data.get('daily', [0] * len(forecast_data)).tolist() if 'daily' in forecast_data.columns else None
                }
            }
            
            return self._to_json_safe(result)
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Prophet forecasting failed: {str(e)}'
            }
    
    def forecast_with_lstm(self, load_data: pd.DataFrame,
                          forecast_periods: int = 168,
                          lookback_periods: int = 24) -> Dict[str, Any]:
        """
        Forecast using LSTM (Long Short-Term Memory) neural network
        
        Args:
            load_data: DataFrame with 'datetime' and load column
            forecast_periods: Number of periods to forecast
            lookback_periods: Number of historical periods to use for prediction
            
        Returns:
            Dictionary with forecast results
        """
        try:
            import tensorflow as tf
            from tensorflow import keras
            from sklearn.preprocessing import MinMaxScaler
        except ImportError:
            return {
                'success': False,
                'error': 'TensorFlow not installed. Install with: pip install tensorflow scikit-learn'
            }
        
        try:
            # Prepare data
            load_col = self._find_load_column(load_data)
            if not load_col:
                return {'success': False, 'error': 'No load column found'}
            
            df = load_data.sort_values('datetime').copy()
            df['load_kw'] = pd.to_numeric(df[load_col], errors='coerce')
            df = df.dropna(subset=['load_kw'])
            
            if len(df) < lookback_periods * 3:
                return {'success': False, 'error': f'Insufficient data points (need at least {lookback_periods * 3})'}
            
            # Scale data
            scaler = MinMaxScaler(feature_range=(0, 1))
            scaled_data = scaler.fit_transform(df['load_kw'].values.reshape(-1, 1))
            
            # Prepare sequences
            X, y = self._create_sequences(scaled_data, lookback_periods)
            
            # Split into train/test
            train_size = int(len(X) * 0.8)
            X_train, X_test = X[:train_size], X[train_size:]
            y_train, y_test = y[:train_size], y[train_size:]
            
            # Build LSTM model
            model = keras.Sequential([
                keras.layers.LSTM(50, return_sequences=True, input_shape=(lookback_periods, 1)),
                keras.layers.Dropout(0.2),
                keras.layers.LSTM(50, return_sequences=False),
                keras.layers.Dropout(0.2),
                keras.layers.Dense(25),
                keras.layers.Dense(1)
            ])
            
            model.compile(optimizer='adam', loss='mean_squared_error')
            
            # Train model (with reduced epochs for speed)
            history = model.fit(
                X_train, y_train,
                batch_size=32,
                epochs=20,
                validation_data=(X_test, y_test),
                verbose=0
            )
            
            # Generate forecast
            last_sequence = scaled_data[-lookback_periods:]
            forecast_values = []
            
            current_sequence = last_sequence.copy()
            for _ in range(forecast_periods):
                # Predict next value
                next_pred = model.predict(current_sequence.reshape(1, lookback_periods, 1), verbose=0)
                forecast_values.append(next_pred[0, 0])
                
                # Update sequence
                current_sequence = np.append(current_sequence[1:], next_pred)
            
            # Inverse transform predictions
            forecast_values = scaler.inverse_transform(np.array(forecast_values).reshape(-1, 1)).flatten()
            
            # Calculate confidence intervals (using training error)
            test_pred = model.predict(X_test, verbose=0)
            test_error_std = np.std(scaler.inverse_transform(y_test) - scaler.inverse_transform(test_pred))
            
            lower_bound = forecast_values - 1.96 * test_error_std
            upper_bound = forecast_values + 1.96 * test_error_std
            
            # Generate future timestamps
            last_time = df['datetime'].max()
            time_delta = self._estimate_time_delta(df)
            future_times = [last_time + (i + 1) * time_delta for i in range(forecast_periods)]
            
            # Calculate metrics
            train_pred = model.predict(X_train, verbose=0)
            train_actual = scaler.inverse_transform(y_train)
            train_pred_inv = scaler.inverse_transform(train_pred)
            
            mae = np.mean(np.abs(train_actual - train_pred_inv))
            rmse = np.sqrt(np.mean((train_actual - train_pred_inv) ** 2))
            
            # Calculate MAPE safely, avoiding division by zero
            non_zero_mask = train_actual.flatten() != 0
            if np.sum(non_zero_mask) > 0:
                mape = np.mean(np.abs((train_actual.flatten()[non_zero_mask] - train_pred_inv.flatten()[non_zero_mask]) / train_actual.flatten()[non_zero_mask])) * 100
            else:
                mape = 0.0
            
            result = {
                'success': True,
                'model_type': 'LSTM',
                'model_params': {
                    'lookback_periods': lookback_periods,
                    'epochs': 20,
                    'layers': 2
                },
                'forecast': {
                    'timestamps': [str(t) for t in future_times],
                    'values': forecast_values.tolist(),
                    'lower_bound': lower_bound.tolist(),
                    'upper_bound': upper_bound.tolist()
                },
                'metrics': {
                    'mae': float(mae),
                    'rmse': float(rmse),
                    'mape': float(mape),
                    'final_loss': float(history.history['loss'][-1])
                },
                'historical': {
                    'timestamps': [str(t) for t in df['datetime'].tolist()],
                    'values': df['load_kw'].tolist()
                }
            }
            
            return self._to_json_safe(result)
            
        except Exception as e:
            return {
                'success': False,
                'error': f'LSTM forecasting failed: {str(e)}'
            }
    
    def forecast_aggregate_load(self, customer_data: Dict[str, pd.DataFrame],
                               feeder_id: str,
                               model_type: str = 'prophet',
                               forecast_periods: int = 168) -> Dict[str, Any]:
        """
        Forecast aggregate load for all customers on a feeder
        
        Args:
            customer_data: Dictionary of customer DataFrames
            feeder_id: Feeder to forecast
            model_type: 'arima', 'prophet', or 'lstm'
            forecast_periods: Number of periods to forecast
            
        Returns:
            Aggregate forecast results
        """
        try:
            # Aggregate all customer loads
            aggregated_data = self._aggregate_customer_loads(customer_data)
            
            if aggregated_data is None or len(aggregated_data) == 0:
                return {
                    'success': False,
                    'error': 'No valid load data to aggregate'
                }
            
            # Apply selected forecasting model
            if model_type.lower() == 'arima':
                result = self.forecast_with_arima(aggregated_data, forecast_periods)
            elif model_type.lower() == 'prophet':
                result = self.forecast_with_prophet(aggregated_data, forecast_periods)
            elif model_type.lower() == 'lstm':
                result = self.forecast_with_lstm(aggregated_data, forecast_periods)
            else:
                return {
                    'success': False,
                    'error': f'Unknown model type: {model_type}'
                }
            
            if result['success']:
                result['feeder_id'] = feeder_id
                result['total_customers'] = len(customer_data)
            
            return result
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Aggregate forecasting failed: {str(e)}'
            }
    
    def forecast_transformer_load(self, transformer_data: pd.DataFrame,
                                  model_type: str = 'prophet',
                                  forecast_periods: int = 168) -> Dict[str, Any]:
        """
        Forecast transformer load using historical transformer data
        
        Args:
            transformer_data: DataFrame containing transformer load data
            model_type: 'arima', 'prophet', or 'lstm'
            forecast_periods: Number of periods to forecast
            
        Returns:
            Transformer forecast results
        """
        try:
            # Prepare transformer data for forecasting
            prepared_data = self._prepare_transformer_data_for_forecast(transformer_data)
            
            if prepared_data is None or len(prepared_data) == 0:
                return {
                    'success': False,
                    'error': 'No valid transformer load data to forecast'
                }
            
            # Apply selected forecasting model
            if model_type.lower() == 'arima':
                result = self.forecast_with_arima(prepared_data, forecast_periods)
            elif model_type.lower() == 'prophet':
                result = self.forecast_with_prophet(prepared_data, forecast_periods)
            elif model_type.lower() == 'lstm':
                result = self.forecast_with_lstm(prepared_data, forecast_periods)
            else:
                return {
                    'success': False,
                    'error': f'Unknown model type: {model_type}'
                }
            
            if result['success']:
                result['source'] = 'transformer'
                result['data_type'] = 'transformer_load'
            
            return result
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Transformer forecasting failed: {str(e)}'
            }
    
    def compare_models(self, load_data: pd.DataFrame,
                      forecast_periods: int = 168) -> Dict[str, Any]:
        """
        Compare all three forecasting models
        
        Args:
            load_data: Historical load data
            forecast_periods: Number of periods to forecast
            
        Returns:
            Comparison of all models
        """
        results = {
            'arima': self.forecast_with_arima(load_data, forecast_periods),
            'prophet': self.forecast_with_prophet(load_data, forecast_periods),
            'lstm': self.forecast_with_lstm(load_data, forecast_periods)
        }
        
        # Determine best model based on MAPE
        best_model = None
        best_mape = float('inf')
        
        for model_name, result in results.items():
            if result['success']:
                mape = result.get('metrics', {}).get('mape', float('inf'))
                if mape < best_mape:
                    best_mape = mape
                    best_model = model_name
        
        result = {
            'models': results,
            'best_model': best_model,
            'best_mape': best_mape
        }
        
        return self._to_json_safe(result)
    
    # Helper methods
    
    def _find_load_column(self, df: pd.DataFrame) -> Optional[str]:
        """Find the load/power column in DataFrame"""
        # Priority order
        patterns = ['KW', 'POWER', 'LOAD', 'DEMAND', 'KVA']
        
        for pattern in patterns:
            matching_cols = [col for col in df.columns if pattern in col.upper()]
            if matching_cols:
                return matching_cols[0]
        
        return None
    
    def _estimate_time_delta(self, df: pd.DataFrame) -> timedelta:
        """Estimate time interval between readings"""
        if len(df) < 2:
            return timedelta(hours=1)
        
        time_diffs = df['datetime'].diff().dropna()
        median_diff = time_diffs.median()
        
        return median_diff
    
    def _timedelta_to_freq(self, td: timedelta) -> str:
        """Convert timedelta to pandas frequency string"""
        total_seconds = td.total_seconds()
        
        if total_seconds < 60:
            return f'{int(total_seconds)}S'
        elif total_seconds < 3600:
            return f'{int(total_seconds / 60)}T'
        elif total_seconds < 86400:
            return f'{int(total_seconds / 3600)}H'
        else:
            return f'{int(total_seconds / 86400)}D'
    
    def _auto_select_arima_params(self, series: pd.Series, 
                                  is_stationary: bool) -> Tuple[int, int, int]:
        """Auto-select ARIMA parameters (simplified)"""
        # Simplified parameter selection
        # In production, use auto_arima or grid search
        
        d = 0 if is_stationary else 1
        p = 2  # AR order
        q = 2  # MA order
        
        return p, d, q
    
    def _create_sequences(self, data: np.ndarray, 
                         lookback: int) -> Tuple[np.ndarray, np.ndarray]:
        """Create sequences for LSTM training"""
        X, y = [], []
        
        for i in range(lookback, len(data)):
            X.append(data[i-lookback:i, 0])
            y.append(data[i, 0])
        
        return np.array(X), np.array(y)
    
    def _aggregate_customer_loads(self, customer_data: Dict[str, pd.DataFrame]) -> Optional[pd.DataFrame]:
        """Aggregate loads from multiple customers"""
        all_data = []
        
        for customer_id, df in customer_data.items():
            if df is None or len(df) == 0:
                continue
            
            # Find load column
            load_col = self._find_load_column(df)
            if not load_col:
                continue
            
            # Ensure datetime column
            if 'datetime' not in df.columns:
                continue
            
            temp_df = df[['datetime', load_col]].copy()
            temp_df['datetime'] = pd.to_datetime(temp_df['datetime'])
            temp_df['load_kw'] = pd.to_numeric(temp_df[load_col], errors='coerce')
            temp_df = temp_df.dropna()
            
            all_data.append(temp_df[['datetime', 'load_kw']])
        
        if not all_data:
            return None
        
        # Merge and aggregate by timestamp
        combined = pd.concat(all_data)
        aggregated = combined.groupby('datetime').agg({'load_kw': 'sum'}).reset_index()
        
        return aggregated
    
    def _prepare_transformer_data_for_forecast(self, transformer_data: pd.DataFrame) -> Optional[pd.DataFrame]:
        """Prepare transformer data for forecasting"""
        try:
            # Create datetime column from DATE and TIME if not already present
            if 'datetime' not in transformer_data.columns:
                if 'DATE' in transformer_data.columns and 'TIME' in transformer_data.columns:
                    transformer_data['datetime'] = pd.to_datetime(
                        transformer_data['DATE'].astype(str) + ' ' + transformer_data['TIME'].astype(str),
                        errors='coerce'
                    )
                elif 'TIMESTAMP' in transformer_data.columns:
                    transformer_data['datetime'] = pd.to_datetime(transformer_data['TIMESTAMP'], errors='coerce')
                else:
                    return None
            
            # Find load column (prefer kW, then kVA)
            load_col = self._find_load_column(transformer_data)
            if not load_col:
                return None
            
            # Prepare data
            prepared_df = transformer_data[['datetime', load_col]].copy()
            prepared_df['datetime'] = pd.to_datetime(prepared_df['datetime'])
            prepared_df['load_kw'] = pd.to_numeric(prepared_df[load_col], errors='coerce')
            prepared_df = prepared_df.dropna()
            prepared_df = prepared_df.sort_values('datetime')
            
            # Remove duplicates
            prepared_df = prepared_df.drop_duplicates(subset=['datetime'], keep='first')
            
            return prepared_df[['datetime', 'load_kw']]
            
        except Exception as e:
            print(f"Error preparing transformer data: {str(e)}")
            return None

