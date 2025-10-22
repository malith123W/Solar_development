"""
Load Balancing Module
Handles phase balancing analysis and optimization
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
import json


@dataclass
class PhaseLoad:
    """Represents load on a single phase"""
    phase_name: str
    total_load_kw: float
    total_reactive_kvar: float
    customer_count: int
    customers: List[str]
    avg_voltage: float
    min_voltage: float
    max_voltage: float


class LoadBalancer:
    """Analyzes and optimizes load distribution across phases"""
    
    def __init__(self, max_imbalance_threshold: float = 0.15):
        """
        Initialize load balancer
        
        Args:
            max_imbalance_threshold: Maximum allowable imbalance (0.15 = 15%)
        """
        self.max_imbalance_threshold = max_imbalance_threshold
        self.nominal_voltage = 230  # V
    
    def _to_json_safe(self, obj):
        """Convert numpy/pandas types to JSON-serializable Python types"""
        if obj is None or isinstance(obj, (str, int, float, bool)):
            return obj
        elif isinstance(obj, (np.integer, np.floating)):
            return obj.item()
        elif isinstance(obj, np.bool_):
            return bool(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, dict):
            return {k: self._to_json_safe(v) for k, v in obj.items()}
        elif isinstance(obj, (list, tuple)):
            return [self._to_json_safe(item) for item in obj]
        else:
            return obj
    
    def analyze_current_balance(self, feeder_data: pd.DataFrame, 
                                customer_data: Dict[str, pd.DataFrame],
                                assignments: List[Dict],
                                transformer_data: Optional[pd.DataFrame] = None) -> Dict[str, Any]:
        """
        Analyze current load balance across feeders and phases
        
        Args:
            feeder_data: DataFrame containing feeder NMD data
            customer_data: Dictionary of customer DataFrames
            assignments: List of customer-feeder-phase assignments
            transformer_data: Optional DataFrame containing transformer load data
            
        Returns:
            Dictionary containing balance analysis results
        """
        # Organize data by feeder and phase
        feeder_structure = self._organize_by_feeder_and_phase(assignments, customer_data)
        
        # Analyze each feeder
        feeder_analysis = {}
        overall_stats = {
            'total_feeders': len(feeder_structure),
            'total_customers': len(assignments),
            'imbalanced_feeders': [],
            'balanced_feeders': []
        }
        
        # Analyze transformer load if available
        transformer_analysis = None
        if transformer_data is not None and len(transformer_data) > 0:
            transformer_analysis = self._analyze_transformer_load(transformer_data)
            overall_stats['transformer_analysis'] = transformer_analysis
        
        for feeder_id, phases in feeder_structure.items():
            phase_loads = self._calculate_phase_loads(phases, customer_data)
            imbalance = self._calculate_imbalance(phase_loads)
            
            feeder_analysis[feeder_id] = {
                'phase_loads': [
                    {
                        'phase': pl.phase_name,
                        'total_kw': pl.total_load_kw,
                        'total_kvar': pl.total_reactive_kvar,
                        'customer_count': pl.customer_count,
                        'customers': pl.customers,
                        'avg_voltage': pl.avg_voltage
                    }
                    for pl in phase_loads
                ],
                'imbalance_percentage': imbalance * 100,
                'is_balanced': imbalance <= self.max_imbalance_threshold,
                'total_load_kw': sum(pl.total_load_kw for pl in phase_loads),
                'total_customers': sum(pl.customer_count for pl in phase_loads)
            }
            
            if imbalance > self.max_imbalance_threshold:
                overall_stats['imbalanced_feeders'].append(feeder_id)
            else:
                overall_stats['balanced_feeders'].append(feeder_id)
        
        result = {
            'feeder_analysis': feeder_analysis,
            'overall_stats': overall_stats,
            'max_imbalance_threshold': self.max_imbalance_threshold * 100
        }
        
        # Convert all numpy types to JSON-serializable Python types
        return self._to_json_safe(result)
    
    def suggest_balancing_moves(self, feeder_data: pd.DataFrame,
                               customer_data: Dict[str, pd.DataFrame],
                               assignments: List[Dict]) -> Dict[str, Any]:
        """
        Suggest customer reassignments to balance loads
        
        Args:
            feeder_data: DataFrame containing feeder NMD data
            customer_data: Dictionary of customer DataFrames
            assignments: List of customer-feeder-phase assignments
            
        Returns:
            Dictionary containing suggested moves
        """
        # Organize data
        feeder_structure = self._organize_by_feeder_and_phase(assignments, customer_data)
        
        suggestions = []
        
        for feeder_id, phases in feeder_structure.items():
            phase_loads = self._calculate_phase_loads(phases, customer_data)
            imbalance = self._calculate_imbalance(phase_loads)
            
            if imbalance > self.max_imbalance_threshold:
                # Find best moves to balance this feeder
                moves = self._find_optimal_moves(feeder_id, phase_loads, customer_data)
                suggestions.extend(moves)
        
        # Calculate expected improvements
        for suggestion in suggestions:
            improvement = self._calculate_improvement(
                suggestion,
                feeder_structure,
                customer_data
            )
            suggestion['expected_improvement'] = improvement
        
        # Sort by expected improvement
        suggestions.sort(key=lambda x: x['expected_improvement']['imbalance_reduction'], 
                        reverse=True)
        
        result = {
            'suggestions': suggestions,
            'total_suggestions': len(suggestions),
            'estimated_balanced_feeders': self._estimate_balanced_feeders(
                suggestions, feeder_structure, customer_data
            )
        }
        
        # Convert all numpy types to JSON-serializable Python types
        return self._to_json_safe(result)
    
    def simulate_balancing(self, original_assignments: List[Dict],
                          balancing_moves: List[Dict],
                          customer_data: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        """
        Simulate the effect of applying balancing moves
        
        Args:
            original_assignments: Original customer assignments
            balancing_moves: Proposed balancing moves
            customer_data: Dictionary of customer DataFrames
            
        Returns:
            Comparison of before and after balance
        """
        # Create new assignments with moves applied
        new_assignments = original_assignments.copy()
        
        for move in balancing_moves:
            customer_id = move['customer_id']
            new_phase = move['to_phase']
            
            # Find and update assignment
            for i, assignment in enumerate(new_assignments):
                if assignment['customer_id'] == customer_id:
                    # Update phase assignment
                    if 'phase_assignments' in assignment:
                        for pa in assignment['phase_assignments']:
                            pa['assigned_feeder_phase'] = new_phase
                    new_assignments[i] = assignment
                    break
        
        # Calculate before and after stats
        before_structure = self._organize_by_feeder_and_phase(original_assignments, customer_data)
        after_structure = self._organize_by_feeder_and_phase(new_assignments, customer_data)
        
        before_stats = self._calculate_overall_stats(before_structure, customer_data)
        after_stats = self._calculate_overall_stats(after_structure, customer_data)
        
        result = {
            'before': before_stats,
            'after': after_stats,
            'improvements': {
                'imbalance_reduction': before_stats['avg_imbalance'] - after_stats['avg_imbalance'],
                'loss_reduction_percentage': self._estimate_loss_reduction(
                    before_stats, after_stats
                ),
                'voltage_improvement': after_stats['avg_voltage'] - before_stats['avg_voltage']
            },
            'moves_applied': len(balancing_moves)
        }
        
        # Convert all numpy types to JSON-serializable Python types
        return self._to_json_safe(result)
    
    def calculate_losses(self, phase_loads: List[PhaseLoad], 
                        feeder_resistance: float = 0.5) -> Dict[str, float]:
        """
        Calculate power losses for given phase loads
        
        Args:
            phase_loads: List of PhaseLoad objects
            feeder_resistance: Feeder resistance in ohms (per phase)
            
        Returns:
            Dictionary with loss calculations
        """
        total_losses = 0
        phase_losses = {}
        
        for phase_load in phase_loads:
            # Calculate current: I = P / V (simplified, single-phase)
            if phase_load.avg_voltage > 0:
                current = (phase_load.total_load_kw * 1000) / phase_load.avg_voltage
                # Loss = I^2 * R
                loss = (current ** 2) * feeder_resistance / 1000  # kW
                phase_losses[phase_load.phase_name] = loss
                total_losses += loss
        
        return {
            'total_losses_kw': total_losses,
            'phase_losses': phase_losses,
            'loss_percentage': (total_losses / sum(pl.total_load_kw for pl in phase_loads) * 100)
                              if sum(pl.total_load_kw for pl in phase_loads) > 0 else 0
        }
    
    def _organize_by_feeder_and_phase(self, assignments: List[Dict],
                                     customer_data: Dict[str, pd.DataFrame]) -> Dict:
        """Organize customers by feeder and phase"""
        feeder_structure = {}
        
        for assignment in assignments:
            customer_id = assignment['customer_id']
            feeder_id = assignment['assigned_feeder']
            phase_assignments = assignment.get('phase_assignments', [])
            
            if feeder_id not in feeder_structure:
                feeder_structure[feeder_id] = {
                    'Phase A': [],
                    'Phase B': [],
                    'Phase C': []
                }
            
            if phase_assignments:
                for phase_assignment in phase_assignments:
                    assigned_phase = phase_assignment['assigned_feeder_phase']
                    feeder_structure[feeder_id][assigned_phase].append({
                        'customer_id': customer_id,
                        'data': customer_data.get(customer_id)
                    })
            else:
                feeder_structure[feeder_id]['Phase A'].append({
                    'customer_id': customer_id,
                    'data': customer_data.get(customer_id)
                })
        
        return feeder_structure
    
    def _calculate_phase_loads(self, phases: Dict[str, List], 
                               customer_data: Dict[str, pd.DataFrame]) -> List[PhaseLoad]:
        """Calculate loads for each phase"""
        phase_loads = []
        
        for phase_name, customers in phases.items():
            total_kw = 0
            total_kvar = 0
            voltages = []
            customer_ids = []
            
            for customer_info in customers:
                customer_id = customer_info['customer_id']
                customer_ids.append(customer_id)
                
                df = customer_data.get(customer_id)
                if df is not None and len(df) > 0:
                    # Extract power if available
                    power_cols = [col for col in df.columns if 'KW' in col.upper()]
                    if power_cols:
                        avg_kw = pd.to_numeric(df[power_cols[0]], errors='coerce').mean()
                        if not pd.isna(avg_kw):
                            total_kw += avg_kw
                    else:
                        total_kw += 5.0  # Default load
                    
                    # Extract reactive power if available
                    reactive_cols = [col for col in df.columns if 'KVAR' in col.upper()]
                    if reactive_cols:
                        avg_kvar = pd.to_numeric(df[reactive_cols[0]], errors='coerce').mean()
                        if not pd.isna(avg_kvar):
                            total_kvar += avg_kvar
                    else:
                        total_kvar += 1.0  # Default reactive power
                    
                    # Extract voltage if available
                    voltage_cols = [col for col in df.columns if 'VOLTAGE' in col.upper()]
                    if voltage_cols:
                        avg_voltage = pd.to_numeric(df[voltage_cols[0]], errors='coerce').mean()
                        if not pd.isna(avg_voltage):
                            voltages.append(avg_voltage)
                else:
                    total_kw += 5.0
                    total_kvar += 1.0
            
            avg_voltage = np.mean(voltages) if voltages else self.nominal_voltage
            min_voltage = np.min(voltages) if voltages else self.nominal_voltage
            max_voltage = np.max(voltages) if voltages else self.nominal_voltage
            
            phase_loads.append(PhaseLoad(
                phase_name=phase_name,
                total_load_kw=total_kw,
                total_reactive_kvar=total_kvar,
                customer_count=len(customers),
                customers=customer_ids,
                avg_voltage=avg_voltage,
                min_voltage=min_voltage,
                max_voltage=max_voltage
            ))
        
        return phase_loads
    
    def _calculate_imbalance(self, phase_loads: List[PhaseLoad]) -> float:
        """
        Calculate load imbalance across phases
        
        Returns:
            Imbalance as a decimal (0.0 to 1.0)
        """
        if not phase_loads:
            return 0.0
        
        loads = [pl.total_load_kw for pl in phase_loads]
        avg_load = np.mean(loads)
        
        if avg_load == 0:
            return 0.0
        
        max_deviation = max(abs(load - avg_load) for load in loads)
        imbalance = max_deviation / avg_load
        
        return imbalance
    
    def _find_optimal_moves(self, feeder_id: str, phase_loads: List[PhaseLoad],
                           customer_data: Dict[str, pd.DataFrame]) -> List[Dict]:
        """Find optimal customer moves to balance phases"""
        moves = []
        
        # Find most loaded and least loaded phases
        sorted_phases = sorted(phase_loads, key=lambda x: x.total_load_kw, reverse=True)
        
        if len(sorted_phases) < 2:
            return moves
        
        most_loaded = sorted_phases[0]
        least_loaded = sorted_phases[-1]
        
        # Don't suggest moves if already balanced
        if most_loaded.total_load_kw - least_loaded.total_load_kw < most_loaded.total_load_kw * 0.1:
            return moves
        
        # Find customers in most loaded phase
        for customer_id in most_loaded.customers:
            df = customer_data.get(customer_id)
            customer_load = 5.0  # Default
            
            if df is not None and len(df) > 0:
                power_cols = [col for col in df.columns if 'KW' in col.upper()]
                if power_cols:
                    avg_kw = pd.to_numeric(df[power_cols[0]], errors='coerce').mean()
                    if not pd.isna(avg_kw):
                        customer_load = avg_kw
            
            # Suggest move if it would improve balance
            new_most_loaded = most_loaded.total_load_kw - customer_load
            new_least_loaded = least_loaded.total_load_kw + customer_load
            
            if abs(new_most_loaded - new_least_loaded) < abs(most_loaded.total_load_kw - least_loaded.total_load_kw):
                moves.append({
                    'customer_id': customer_id,
                    'feeder_id': feeder_id,
                    'from_phase': most_loaded.phase_name,
                    'to_phase': least_loaded.phase_name,
                    'customer_load_kw': customer_load,
                    'reason': 'Balance load distribution'
                })
                
                # Limit number of suggestions per feeder
                if len(moves) >= 5:
                    break
        
        return moves
    
    def _calculate_improvement(self, move: Dict, feeder_structure: Dict,
                              customer_data: Dict[str, pd.DataFrame]) -> Dict[str, float]:
        """Calculate expected improvement from a move"""
        feeder_id = move['feeder_id']
        phases = feeder_structure.get(feeder_id, {})
        
        # Calculate current imbalance
        phase_loads_before = self._calculate_phase_loads(phases, customer_data)
        imbalance_before = self._calculate_imbalance(phase_loads_before)
        
        # Simulate move
        # (Simplified - in production, create a deep copy and apply move)
        customer_load = move['customer_load_kw']
        
        # Estimate new imbalance
        from_phase_load = next((pl.total_load_kw for pl in phase_loads_before 
                               if pl.phase_name == move['from_phase']), 0)
        to_phase_load = next((pl.total_load_kw for pl in phase_loads_before 
                             if pl.phase_name == move['to_phase']), 0)
        
        new_from = from_phase_load - customer_load
        new_to = to_phase_load + customer_load
        
        avg_load = np.mean([pl.total_load_kw for pl in phase_loads_before])
        if avg_load > 0:
            max_deviation_after = max(abs(new_from - avg_load), abs(new_to - avg_load))
            imbalance_after = max_deviation_after / avg_load
        else:
            imbalance_after = imbalance_before
        
        return {
            'imbalance_before': imbalance_before,
            'imbalance_after': imbalance_after,
            'imbalance_reduction': imbalance_before - imbalance_after
        }
    
    def _calculate_overall_stats(self, feeder_structure: Dict,
                                customer_data: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        """Calculate overall statistics for all feeders"""
        total_imbalance = 0
        total_feeders = len(feeder_structure)
        total_load = 0
        voltages = []
        
        for feeder_id, phases in feeder_structure.items():
            phase_loads = self._calculate_phase_loads(phases, customer_data)
            imbalance = self._calculate_imbalance(phase_loads)
            total_imbalance += imbalance
            total_load += sum(pl.total_load_kw for pl in phase_loads)
            
            for pl in phase_loads:
                voltages.append(pl.avg_voltage)
        
        return {
            'avg_imbalance': total_imbalance / total_feeders if total_feeders > 0 else 0,
            'total_load_kw': total_load,
            'avg_voltage': np.mean(voltages) if voltages else self.nominal_voltage
        }
    
    def _estimate_loss_reduction(self, before_stats: Dict, after_stats: Dict) -> float:
        """Estimate percentage loss reduction from balancing"""
        # Losses are proportional to imbalance squared (simplified)
        before_loss_factor = (1 + before_stats['avg_imbalance']) ** 2
        after_loss_factor = (1 + after_stats['avg_imbalance']) ** 2
        
        if before_loss_factor > 0:
            reduction = ((before_loss_factor - after_loss_factor) / before_loss_factor) * 100
            return max(0, reduction)
        
        return 0
    
    def _estimate_balanced_feeders(self, suggestions: List[Dict],
                                  feeder_structure: Dict,
                                  customer_data: Dict[str, pd.DataFrame]) -> int:
        """Estimate how many feeders would be balanced after applying suggestions"""
        # Simplified estimation
        feeders_to_improve = set(s['feeder_id'] for s in suggestions)
        
        balanced_count = 0
        for feeder_id, phases in feeder_structure.items():
            phase_loads = self._calculate_phase_loads(phases, customer_data)
            imbalance = self._calculate_imbalance(phase_loads)
            
            if imbalance <= self.max_imbalance_threshold:
                balanced_count += 1
            elif feeder_id in feeders_to_improve:
                # Assume improvement if suggestions exist
                balanced_count += 0.7  # 70% chance of improvement
        
        return int(balanced_count)
    
    def _analyze_transformer_load(self, transformer_data: pd.DataFrame) -> Dict[str, Any]:
        """
        Analyze transformer load data
        
        Args:
            transformer_data: DataFrame containing transformer load data
            
        Returns:
            Dictionary with transformer analysis results
        """
        analysis = {
            'total_records': len(transformer_data),
            'phase_analysis': {},
            'load_statistics': {},
            'voltage_statistics': {},
            'power_factor_analysis': {},
            'utilization': {}
        }
        
        try:
            # Extract phase currents
            phase_a_col = [col for col in transformer_data.columns if 'PHASE_A' in col.upper() and 'CURRENT' in col.upper()]
            phase_b_col = [col for col in transformer_data.columns if 'PHASE_B' in col.upper() and 'CURRENT' in col.upper()]
            phase_c_col = [col for col in transformer_data.columns if 'PHASE_C' in col.upper() and 'CURRENT' in col.upper()]
            
            # Extract voltages
            voltage_a_col = [col for col in transformer_data.columns if 'PHASE_A' in col.upper() and 'VOLTAGE' in col.upper()]
            voltage_b_col = [col for col in transformer_data.columns if 'PHASE_B' in col.upper() and 'VOLTAGE' in col.upper()]
            voltage_c_col = [col for col in transformer_data.columns if 'PHASE_C' in col.upper() and 'VOLTAGE' in col.upper()]
            
            # Analyze phase currents
            if phase_a_col and phase_b_col and phase_c_col:
                phase_a_current = pd.to_numeric(transformer_data[phase_a_col[0]], errors='coerce')
                phase_b_current = pd.to_numeric(transformer_data[phase_b_col[0]], errors='coerce')
                phase_c_current = pd.to_numeric(transformer_data[phase_c_col[0]], errors='coerce')
                
                analysis['phase_analysis'] = {
                    'Phase A': {
                        'avg_current': float(phase_a_current.mean()),
                        'max_current': float(phase_a_current.max()),
                        'min_current': float(phase_a_current.min()),
                        'std_current': float(phase_a_current.std())
                    },
                    'Phase B': {
                        'avg_current': float(phase_b_current.mean()),
                        'max_current': float(phase_b_current.max()),
                        'min_current': float(phase_b_current.min()),
                        'std_current': float(phase_b_current.std())
                    },
                    'Phase C': {
                        'avg_current': float(phase_c_current.mean()),
                        'max_current': float(phase_c_current.max()),
                        'min_current': float(phase_c_current.min()),
                        'std_current': float(phase_c_current.std())
                    }
                }
                
                # Calculate current imbalance
                avg_currents = [phase_a_current.mean(), phase_b_current.mean(), phase_c_current.mean()]
                avg_current = np.mean(avg_currents)
                if avg_current > 0:
                    max_deviation = max(abs(i - avg_current) for i in avg_currents)
                    current_imbalance = (max_deviation / avg_current) * 100
                    analysis['phase_analysis']['current_imbalance_percentage'] = float(current_imbalance)
            
            # Analyze voltages
            if voltage_a_col and voltage_b_col and voltage_c_col:
                voltage_a = pd.to_numeric(transformer_data[voltage_a_col[0]], errors='coerce')
                voltage_b = pd.to_numeric(transformer_data[voltage_b_col[0]], errors='coerce')
                voltage_c = pd.to_numeric(transformer_data[voltage_c_col[0]], errors='coerce')
                
                analysis['voltage_statistics'] = {
                    'Phase A': {
                        'avg_voltage': float(voltage_a.mean()),
                        'max_voltage': float(voltage_a.max()),
                        'min_voltage': float(voltage_a.min()),
                        'std_voltage': float(voltage_a.std())
                    },
                    'Phase B': {
                        'avg_voltage': float(voltage_b.mean()),
                        'max_voltage': float(voltage_b.max()),
                        'min_voltage': float(voltage_b.min()),
                        'std_voltage': float(voltage_b.std())
                    },
                    'Phase C': {
                        'avg_voltage': float(voltage_c.mean()),
                        'max_voltage': float(voltage_c.max()),
                        'min_voltage': float(voltage_c.min()),
                        'std_voltage': float(voltage_c.std())
                    }
                }
                
                # Calculate voltage imbalance
                avg_voltages = [voltage_a.mean(), voltage_b.mean(), voltage_c.mean()]
                avg_voltage = np.mean(avg_voltages)
                if avg_voltage > 0:
                    max_deviation = max(abs(v - avg_voltage) for v in avg_voltages)
                    voltage_imbalance = (max_deviation / avg_voltage) * 100
                    analysis['voltage_statistics']['voltage_imbalance_percentage'] = float(voltage_imbalance)
            
            # Analyze load (kW and kVA)
            load_kw_col = [col for col in transformer_data.columns if 'IMPORT_KW' in col.upper() and 'AVG' in col.upper()]
            load_kva_col = [col for col in transformer_data.columns if 'IMPORT_KVA' in col.upper() and 'AVG' in col.upper()]
            
            if load_kw_col:
                load_kw = pd.to_numeric(transformer_data[load_kw_col[0]], errors='coerce')
                analysis['load_statistics']['kw'] = {
                    'avg_load_kw': float(load_kw.mean()),
                    'max_load_kw': float(load_kw.max()),
                    'min_load_kw': float(load_kw.min()),
                    'std_load_kw': float(load_kw.std())
                }
            
            if load_kva_col:
                load_kva = pd.to_numeric(transformer_data[load_kva_col[0]], errors='coerce')
                analysis['load_statistics']['kva'] = {
                    'avg_load_kva': float(load_kva.mean()),
                    'max_load_kva': float(load_kva.max()),
                    'min_load_kva': float(load_kva.min()),
                    'std_load_kva': float(load_kva.std())
                }
            
            # Analyze power factor
            pf_col = [col for col in transformer_data.columns if 'POWER_FACTOR' in col.upper()]
            if pf_col:
                power_factor = pd.to_numeric(transformer_data[pf_col[0]], errors='coerce')
                analysis['power_factor_analysis'] = {
                    'avg_power_factor': float(power_factor.mean()),
                    'max_power_factor': float(power_factor.max()),
                    'min_power_factor': float(power_factor.min()),
                    'std_power_factor': float(power_factor.std())
                }
            
            # Calculate transformer utilization (assuming 100 kVA transformer as default)
            transformer_capacity_kva = 100.0
            if load_kva_col:
                utilization_percentage = (load_kva.max() / transformer_capacity_kva) * 100
                analysis['utilization'] = {
                    'transformer_capacity_kva': transformer_capacity_kva,
                    'peak_load_kva': float(load_kva.max()),
                    'utilization_percentage': float(utilization_percentage),
                    'available_capacity_kva': float(transformer_capacity_kva - load_kva.max())
                }
            
        except Exception as e:
            analysis['error'] = f'Error analyzing transformer data: {str(e)}'
        
        return analysis

