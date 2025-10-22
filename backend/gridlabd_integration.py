"""
GridLAB-D Integration Module
Handles .glm file generation and GridLAB-D simulation integration
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
import os
import subprocess
import json
import tempfile
import shutil
import atexit
from datetime import datetime, timedelta


class GridLABDIntegration:
    """Handles GridLAB-D model generation and simulation"""
    
    def __init__(self, output_dir='gridlabd_models', use_temp_files=True):
        self.output_dir = output_dir
        self.use_temp_files = use_temp_files
        self.temp_dir = None
        self.temp_files = []  # Track temporary files for cleanup
        
        if use_temp_files:
            # Create temporary directory for this instance
            self.temp_dir = tempfile.mkdtemp(prefix='gridlabd_')
            # Register cleanup function to run on exit
            atexit.register(self.cleanup_temp_files)
        else:
            os.makedirs(output_dir, exist_ok=True)
            
        self.nominal_voltage = 230  # V (phase voltage)
        self.line_voltage = 400  # V (line-to-line voltage)
        self.frequency = 50  # Hz
    
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
        elif isinstance(obj, pd.Timestamp):
            return obj.isoformat()
        elif isinstance(obj, dict):
            return {k: self._to_json_safe(v) for k, v in obj.items()}
        elif isinstance(obj, (list, tuple)):
            return [self._to_json_safe(item) for item in obj]
        else:
            return obj
    
    def generate_glm_from_data(self, feeder_data: pd.DataFrame, customer_data: Dict[str, pd.DataFrame],
                               assignments: List[Dict], transformer_name: str = 'T1',
                               model_name: str = 'grid_model', transformer_capacity_kva: float = 5000,
                               primary_voltage: float = 11000, secondary_voltage: float = 400,
                               transformer_data: Optional[pd.DataFrame] = None) -> str:
        """
        Generate a GridLAB-D .glm file from NMD and customer data
        
        Args:
            feeder_data: DataFrame containing feeder NMD data
            customer_data: Dictionary of customer DataFrames {customer_id: df}
            assignments: List of customer-feeder assignments from NMD analysis
            transformer_name: Name of the main transformer
            model_name: Name for the output model
            transformer_capacity_kva: Transformer capacity in kVA
            primary_voltage: Primary voltage in V
            secondary_voltage: Secondary voltage in V
            transformer_data: Optional DataFrame containing transformer load data
            
        Returns:
            Path to generated .glm file
        """
        glm_content = []
        
        # Header and global settings
        glm_content.append(self._generate_header())
        
        # Clock settings
        glm_content.append(self._generate_clock())
        
        # Module configuration
        glm_content.append(self._generate_modules())
        
        # Network objects
        # 1. Main transformer (substation) - use transformer data if available
        if transformer_data is not None and len(transformer_data) > 0:
            # Extract actual transformer capacity from data if available
            actual_capacity = self._extract_transformer_capacity(transformer_data, transformer_capacity_kva)
            glm_content.append(self._generate_transformer(transformer_name, actual_capacity, primary_voltage, secondary_voltage))
        else:
            glm_content.append(self._generate_transformer(transformer_name, transformer_capacity_kva, primary_voltage, secondary_voltage))
        
        # 2. Group customers by feeder and phase
        feeder_structure = self._organize_by_feeder_and_phase(assignments, customer_data)
        
        # 3. Generate feeders, poles, and customer connections
        for feeder_id, phases in feeder_structure.items():
            # Create feeder node
            glm_content.append(self._generate_feeder_node(feeder_id, transformer_name))
            
            # Create underground/overhead lines from transformer to feeder
            glm_content.append(self._generate_transmission_line(
                f"{transformer_name}_to_{feeder_id}",
                transformer_name,
                feeder_id,
                length=500  # meters
            ))
            
            # For each phase in the feeder
            for phase_name, customers in phases.items():
                if not customers:
                    continue
                
                phase_letter = phase_name.split()[-1]  # A, B, or C
                
                # Create phase node
                phase_node_id = f"{feeder_id}_{phase_letter}"
                glm_content.append(self._generate_phase_node(phase_node_id, feeder_id, phase_letter))
                
                # Create line from feeder to phase node
                glm_content.append(self._generate_distribution_line(
                    f"{feeder_id}_to_{phase_node_id}",
                    feeder_id,
                    phase_node_id,
                    phase_letter,
                    length=200  # meters
                ))
                
                # Create poles and customer connections
                for i, customer_info in enumerate(customers):
                    customer_id = customer_info['customer_id']
                    
                    # Create pole for this customer
                    pole_id = f"pole_{customer_id}"
                    glm_content.append(self._generate_pole(pole_id, phase_node_id, phase_letter))
                    
                    # Create service line from pole to customer
                    glm_content.append(self._generate_service_line(
                        f"service_{customer_id}",
                        pole_id,
                        f"meter_{customer_id}",
                        phase_letter,
                        length=30  # meters
                    ))
                    
                    # Create meter and load
                    avg_load = self._calculate_average_load(customer_data.get(customer_id))
                    glm_content.append(self._generate_meter_and_load(
                        customer_id,
                        f"meter_{customer_id}",
                        phase_letter,
                        avg_load
                    ))
        
        # Recorders for monitoring
        glm_content.append(self._generate_recorders(transformer_name))
        
        # Combine all parts
        glm_file_content = '\n\n'.join(glm_content)
        
        # Write to file (temporary or permanent based on configuration)
        if self.use_temp_files and self.temp_dir:
            glm_filepath = os.path.join(self.temp_dir, f"{model_name}.glm")
        else:
            glm_filepath = os.path.join(self.output_dir, f"{model_name}.glm")
            
        with open(glm_filepath, 'w') as f:
            f.write(glm_file_content)
        
        # Track temporary file for cleanup
        if self.use_temp_files:
            self.temp_files.append(glm_filepath)
        
        return glm_filepath
    
    def _generate_header(self) -> str:
        """Generate GLM file header with metadata"""
        return f"""// GridLAB-D Model
// Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
// Purpose: Smart Load Balancing and Forecasting Analysis
"""
    
    def _generate_clock(self) -> str:
        """Generate clock configuration"""
        start_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        end_time = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S')
        
        return f"""clock {{
    timezone UTC0;
    starttime '{start_time}';
    stoptime '{end_time}';
}}"""
    
    def _generate_modules(self) -> str:
        """Generate required GridLAB-D modules"""
        return """module powerflow {
    solver_method NR;
    NR_iteration_limit 50;
};

module tape;

module residential {
    implicit_enduses NONE;
};"""
    
    def _generate_transformer(self, name: str, capacity_kva: float = 5000, 
                             primary_voltage: float = 11000, secondary_voltage: float = 400) -> str:
        """Generate main transformer (substation)"""
        # Calculate phase voltages
        primary_phase_voltage = primary_voltage / np.sqrt(3)
        secondary_phase_voltage = secondary_voltage / np.sqrt(3)
        
        # Calculate complex voltages for balanced 3-phase system
        primary_va = primary_phase_voltage + 0j
        primary_vb = -primary_phase_voltage/2 - primary_phase_voltage*np.sqrt(3)/2*1j
        primary_vc = -primary_phase_voltage/2 + primary_phase_voltage*np.sqrt(3)/2*1j
        
        secondary_va = secondary_phase_voltage + 0j
        secondary_vb = -secondary_phase_voltage/2 - secondary_phase_voltage*np.sqrt(3)/2*1j
        secondary_vc = -secondary_phase_voltage/2 + secondary_phase_voltage*np.sqrt(3)/2*1j
        
        return f"""object transformer_configuration {{
    name transformer_config_{name};
    connect_type WYE_WYE;
    install_type PADMOUNT;
    power_rating {capacity_kva};  // kVA
    primary_voltage {primary_voltage};  // V
    secondary_voltage {secondary_voltage};  // V
    resistance 0.01;
    reactance 0.06;
}};

object transformer {{
    name {name};
    phases ABCN;
    from source_node;
    to {name}_secondary;
    configuration transformer_config_{name};
}};

object node {{
    name source_node;
    phases ABCN;
    bustype SWING;
    voltage_A {primary_va.real:.2f}+{primary_va.imag:.2f}j;  // {primary_voltage}V / sqrt(3)
    voltage_B {primary_vb.real:.2f}{primary_vb.imag:+.2f}j;
    voltage_C {primary_vc.real:.2f}{primary_vc.imag:+.2f}j;
    nominal_voltage {primary_phase_voltage:.2f};
}};

object node {{
    name {name}_secondary;
    phases ABCN;
    voltage_A {secondary_va.real:.2f}+{secondary_va.imag:.2f}j;  // {secondary_voltage}V / sqrt(3)
    voltage_B {secondary_vb.real:.2f}{secondary_vb.imag:+.2f}j;
    voltage_C {secondary_vc.real:.2f}{secondary_vc.imag:+.2f}j;
    nominal_voltage {secondary_phase_voltage:.2f};
}};"""
    
    def _generate_feeder_node(self, feeder_id: str, transformer_name: str) -> str:
        """Generate feeder node"""
        return f"""object node {{
    name {feeder_id};
    phases ABCN;
    voltage_A 230.94+0j;
    voltage_B -115.47-200j;
    voltage_C -115.47+200j;
    nominal_voltage 230.94;
}};"""
    
    def _generate_transmission_line(self, line_name: str, from_node: str, 
                                   to_node: str, length: float) -> str:
        """Generate transmission line from transformer to feeder"""
        return f"""object line_configuration {{
    name line_config_{line_name};
    conductor_A overhead_line_conductor;
    conductor_B overhead_line_conductor;
    conductor_C overhead_line_conductor;
    conductor_N overhead_line_conductor;
    spacing line_spacing_500;
}};

object line_spacing {{
    name line_spacing_500;
    distance_AB 1.0 m;
    distance_BC 1.0 m;
    distance_AC 2.0 m;
    distance_AN 1.5 m;
    distance_BN 1.5 m;
    distance_CN 1.5 m;
}};

object overhead_line_conductor {{
    name overhead_line_conductor;
    geometric_mean_radius 0.00446 m;
    resistance 0.592 Ohm/km;
}};

object overhead_line {{
    name {line_name};
    phases ABCN;
    from {from_node}_secondary;
    to {to_node};
    length {length} m;
    configuration line_config_{line_name};
}};"""
    
    def _generate_phase_node(self, node_id: str, parent_feeder: str, phase: str) -> str:
        """Generate phase-specific node"""
        phase_voltages = {
            'A': '230.94+0j',
            'B': '-115.47-200j',
            'C': '-115.47+200j'
        }
        
        return f"""object node {{
    name {node_id};
    phases {phase}N;
    voltage_{phase} {phase_voltages[phase]};
    nominal_voltage 230.94;
}};"""
    
    def _generate_distribution_line(self, line_name: str, from_node: str, 
                                   to_node: str, phase: str, length: float) -> str:
        """Generate distribution line for specific phase"""
        return f"""object underground_line_conductor {{
    name ugc_{phase}_{line_name};
    outer_diameter 0.025 m;
    conductor_gmr 0.00446 m;
    conductor_diameter 0.015 m;
    conductor_resistance 0.769 Ohm/km;
    neutral_gmr 0.00446 m;
    neutral_resistance 0.769 Ohm/km;
    neutral_diameter 0.015 m;
    neutral_strands 13;
}};

object line_spacing {{
    name spacing_{line_name};
    distance_{phase}N 0.5 m;
}};

object line_configuration {{
    name config_{line_name};
    conductor_{phase} ugc_{phase}_{line_name};
    conductor_N ugc_{phase}_{line_name};
    spacing spacing_{line_name};
}};

object underground_line {{
    name {line_name};
    phases {phase}N;
    from {from_node};
    to {to_node};
    length {length} m;
    configuration config_{line_name};
}};"""
    
    def _generate_pole(self, pole_id: str, phase_node: str, phase: str) -> str:
        """Generate pole (connection point)"""
        phase_voltages = {
            'A': '230.94+0j',
            'B': '-115.47-200j',
            'C': '-115.47+200j'
        }
        
        return f"""object node {{
    name {pole_id};
    parent {phase_node};
    phases {phase}N;
    voltage_{phase} {phase_voltages[phase]};
    nominal_voltage 230.94;
}};"""
    
    def _generate_service_line(self, line_name: str, from_pole: str, 
                               to_meter: str, phase: str, length: float) -> str:
        """Generate service line from pole to customer meter"""
        return f"""object triplex_line_conductor {{
    name tlc_{line_name};
    resistance 0.97 Ohm/km;
    geometric_mean_radius 0.01111 m;
}};

object triplex_line_configuration {{
    name tlc_config_{line_name};
    conductor_1 tlc_{line_name};
    conductor_2 tlc_{line_name};
    conductor_N tlc_{line_name};
    insulation_thickness 0.08 in;
    diameter 0.368 in;
}};

object triplex_line {{
    name {line_name};
    phases {phase}S;
    from {from_pole};
    to {to_meter};
    length {length} m;
    configuration tlc_config_{line_name};
}};"""
    
    def _generate_meter_and_load(self, customer_id: str, meter_id: str, 
                                phase: str, avg_load: Dict[str, float]) -> str:
        """Generate meter and load for a customer"""
        real_power = avg_load.get('real_power_kw', 5.0)
        reactive_power = avg_load.get('reactive_power_kvar', 1.0)
        
        return f"""object triplex_meter {{
    name {meter_id};
    phases {phase}S;
    nominal_voltage 230.0;
}};

object triplex_load {{
    name load_{customer_id};
    parent {meter_id};
    phases {phase}S;
    constant_power_{phase} {real_power*1000}+{reactive_power*1000}j;  // W
    nominal_voltage 230.0;
}};"""
    
    def _generate_recorders(self, transformer_name: str) -> str:
        """Generate data recorders for monitoring"""
        return f"""object recorder {{
    parent {transformer_name};
    property power_in_A,power_in_B,power_in_C;
    interval 3600;
    file transformer_power.csv;
}};

object group_recorder {{
    group "class=triplex_meter";
    property voltage_1,voltage_2,voltage_N;
    interval 3600;
    file meter_voltages.csv;
}};

object group_recorder {{
    group "class=triplex_load";
    property constant_power_A,constant_power_B,constant_power_C;
    interval 3600;
    file load_powers.csv;
}};"""
    
    def _organize_by_feeder_and_phase(self, assignments: List[Dict], 
                                     customer_data: Dict[str, pd.DataFrame]) -> Dict:
        """Organize customers by feeder and phase"""
        feeder_structure = {}
        
        for assignment in assignments:
            customer_id = assignment['customer_id']
            feeder_id = assignment['assigned_feeder']
            phase_assignments = assignment.get('phase_assignments', [])
            
            # Initialize feeder if not exists
            if feeder_id not in feeder_structure:
                feeder_structure[feeder_id] = {
                    'Phase A': [],
                    'Phase B': [],
                    'Phase C': []
                }
            
            # Add customer to appropriate phases
            if phase_assignments:
                for phase_assignment in phase_assignments:
                    assigned_phase = phase_assignment['assigned_feeder_phase']
                    feeder_structure[feeder_id][assigned_phase].append({
                        'customer_id': customer_id,
                        'correlation': phase_assignment.get('correlation', 0)
                    })
            else:
                # Default to Phase A if no phase assignment
                feeder_structure[feeder_id]['Phase A'].append({
                    'customer_id': customer_id,
                    'correlation': assignment.get('correlation', 0)
                })
        
        return feeder_structure
    
    def _calculate_average_load(self, customer_df: Optional[pd.DataFrame]) -> Dict[str, float]:
        """Calculate average load from customer data"""
        if customer_df is None or len(customer_df) == 0:
            return {'real_power_kw': 5.0, 'reactive_power_kvar': 1.0}
        
        # Try to find power columns
        power_cols = [col for col in customer_df.columns if 'KW' in col.upper() or 'POWER' in col.upper()]
        reactive_cols = [col for col in customer_df.columns if 'KVAR' in col.upper()]
        
        real_power_kw = 5.0  # Default
        reactive_power_kvar = 1.0  # Default
        
        if power_cols:
            real_power_kw = pd.to_numeric(customer_df[power_cols[0]], errors='coerce').mean()
            if pd.isna(real_power_kw):
                real_power_kw = 5.0
        
        if reactive_cols:
            reactive_power_kvar = pd.to_numeric(customer_df[reactive_cols[0]], errors='coerce').mean()
            if pd.isna(reactive_power_kvar):
                reactive_power_kvar = 1.0
        
        return {
            'real_power_kw': float(real_power_kw),
            'reactive_power_kvar': float(reactive_power_kvar)
        }
    
    def _extract_transformer_capacity(self, transformer_data: pd.DataFrame, default_capacity: float) -> float:
        """Extract transformer capacity from transformer data"""
        try:
            # Look for kVA columns
            kva_cols = [col for col in transformer_data.columns if 'KVA' in col.upper() and 'IMPORT' in col.upper()]
            
            if kva_cols:
                kva_data = pd.to_numeric(transformer_data[kva_cols[0]], errors='coerce')
                max_kva = kva_data.max()
                
                # If we have actual load data, set capacity to 1.2x max load (20% safety margin)
                if not pd.isna(max_kva) and max_kva > 0:
                    return max(max_kva * 1.2, default_capacity)
            
            # Look for kW columns and convert to kVA (assuming 0.8 power factor)
            kw_cols = [col for col in transformer_data.columns if 'KW' in col.upper() and 'IMPORT' in col.upper()]
            
            if kw_cols:
                kw_data = pd.to_numeric(transformer_data[kw_cols[0]], errors='coerce')
                max_kw = kw_data.max()
                
                # Convert kW to kVA (assuming 0.8 power factor)
                if not pd.isna(max_kw) and max_kw > 0:
                    max_kva = max_kw / 0.8
                    return max(max_kva * 1.2, default_capacity)
            
            return default_capacity
            
        except Exception:
            return default_capacity
    
    def run_simulation(self, glm_filepath: str) -> Dict[str, Any]:
        """
        Run GridLAB-D simulation
        
        Args:
            glm_filepath: Path to .glm file
            
        Returns:
            Dictionary containing simulation results
        """
        try:
            # Check if GridLAB-D is installed
            result = subprocess.run(['gridlabd', '--version'], 
                                  capture_output=True, text=True, timeout=5)
            
            if result.returncode != 0:
                return {
                    'success': False,
                    'error': 'GridLAB-D not installed or not in PATH',
                    'message': 'Please install GridLAB-D: https://www.gridlabd.org/'
                }
            
            # Run simulation
            output_dir = os.path.dirname(glm_filepath)
            result = subprocess.run(
                ['gridlabd', glm_filepath],
                capture_output=True,
                text=True,
                cwd=output_dir,
                timeout=300  # 5 minute timeout
            )
            
            if result.returncode != 0:
                return {
                    'success': False,
                    'error': 'Simulation failed',
                    'stderr': result.stderr,
                    'stdout': result.stdout
                }
            
            # Parse output files
            results = self._parse_simulation_results(output_dir)
            
            result_dict = {
                'success': True,
                'results': results,
                'stdout': result.stdout,
                'glm_file': glm_filepath,
                'is_temp_file': self.use_temp_files and glm_filepath in self.temp_files
            }
            
            # If using temporary files, clean up the GLM file after simulation
            if self.use_temp_files and glm_filepath in self.temp_files:
                self.cleanup_specific_file(glm_filepath)
            
            return self._to_json_safe(result_dict)
            
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'error': 'Simulation timeout (>5 minutes)'
            }
        except FileNotFoundError:
            return {
                'success': False,
                'error': 'GridLAB-D not installed',
                'message': 'Please install GridLAB-D from https://www.gridlabd.org/'
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Simulation error: {str(e)}'
            }
    
    def _parse_simulation_results(self, output_dir: str) -> Dict[str, Any]:
        """Parse GridLAB-D simulation output files"""
        results = {
            'transformer_power': None,
            'meter_voltages': None,
            'load_powers': None
        }
        
        # Parse transformer power
        transformer_file = os.path.join(output_dir, 'transformer_power.csv')
        if os.path.exists(transformer_file):
            try:
                df = pd.read_csv(transformer_file)
                results['transformer_power'] = df.to_dict('records')
            except:
                pass
        
        # Parse meter voltages
        meter_file = os.path.join(output_dir, 'meter_voltages.csv')
        if os.path.exists(meter_file):
            try:
                df = pd.read_csv(meter_file)
                results['meter_voltages'] = df.to_dict('records')
            except:
                pass
        
        # Parse load powers
        load_file = os.path.join(output_dir, 'load_powers.csv')
        if os.path.exists(load_file):
            try:
                df = pd.read_csv(load_file)
                results['load_powers'] = df.to_dict('records')
            except:
                pass
        
        return results
    
    def visualize_grid_structure(self, glm_filepath: str) -> Dict[str, Any]:
        """
        Generate visualization data for the grid structure
        
        Args:
            glm_filepath: Path to .glm file
            
        Returns:
            Dictionary containing node and edge data for visualization
        """
        # Parse GLM file to extract structure
        nodes = []
        edges = []
        
        try:
            with open(glm_filepath, 'r') as f:
                content = f.read()
            
            # Simple parsing (can be enhanced with proper GLM parser)
            # Extract transformer
            nodes.append({
                'id': 'transformer',
                'type': 'transformer',
                'label': 'Main Transformer'
            })
            
            # This is a simplified version - in production, use proper GLM parsing
            result_dict = {
                'nodes': nodes,
                'edges': edges,
                'message': 'Grid structure visualization (simplified)'
            }
            
            return self._to_json_safe(result_dict)
            
        except Exception as e:
            return {
                'error': f'Error parsing GLM file: {str(e)}'
            }
    
    def cleanup_temp_files(self):
        """Clean up all temporary files and directories"""
        try:
            # Remove individual temporary files
            for temp_file in self.temp_files:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
            
            # Remove temporary directory if it exists
            if self.temp_dir and os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir)
                
            self.temp_files.clear()
            self.temp_dir = None
            
        except Exception as e:
            print(f"Warning: Error cleaning up temporary files: {e}")
    
    def cleanup_specific_file(self, filepath: str):
        """Clean up a specific temporary file"""
        try:
            if filepath in self.temp_files:
                if os.path.exists(filepath):
                    os.remove(filepath)
                self.temp_files.remove(filepath)
                return True
        except Exception as e:
            print(f"Warning: Error cleaning up file {filepath}: {e}")
        return False
    
    def get_temp_file_info(self):
        """Get information about current temporary files"""
        return {
            'temp_dir': self.temp_dir,
            'temp_files': self.temp_files,
            'use_temp_files': self.use_temp_files
        }
    
    def analyze_transformer_load_file(self, transformer_file_path: str) -> Dict[str, Any]:
        """
        Analyze transformer load data from CSV file
        
        Args:
            transformer_file_path: Path to transformer load CSV file
            
        Returns:
            Dictionary containing transformer analysis results
        """
        try:
            # Read transformer data
            transformer_df = pd.read_csv(transformer_file_path)
            
            analysis = {
                'file_info': {
                    'filename': os.path.basename(transformer_file_path),
                    'total_records': len(transformer_df),
                    'columns': list(transformer_df.columns)
                },
                'load_analysis': {},
                'voltage_analysis': {},
                'current_analysis': {},
                'power_factor_analysis': {},
                'recommendations': []
            }
            
            # Analyze load data (kW, kVA)
            load_kw_cols = [col for col in transformer_df.columns if 'KW' in col.upper() and 'IMPORT' in col.upper()]
            load_kva_cols = [col for col in transformer_df.columns if 'KVA' in col.upper() and 'IMPORT' in col.upper()]
            
            if load_kw_cols:
                load_kw = pd.to_numeric(transformer_df[load_kw_cols[0]], errors='coerce')
                analysis['load_analysis']['kw'] = {
                    'avg_load_kw': float(load_kw.mean()),
                    'max_load_kw': float(load_kw.max()),
                    'min_load_kw': float(load_kw.min()),
                    'std_load_kw': float(load_kw.std()),
                    'peak_load_percentage': float((load_kw.max() / load_kw.mean()) * 100) if load_kw.mean() > 0 else 0
                }
            
            if load_kva_cols:
                load_kva = pd.to_numeric(transformer_df[load_kva_cols[0]], errors='coerce')
                analysis['load_analysis']['kva'] = {
                    'avg_load_kva': float(load_kva.mean()),
                    'max_load_kva': float(load_kva.max()),
                    'min_load_kva': float(load_kva.min()),
                    'std_load_kva': float(load_kva.std())
                }
            
            # Analyze voltage data
            voltage_cols = [col for col in transformer_df.columns if 'VOLTAGE' in col.upper()]
            if voltage_cols:
                for col in voltage_cols[:3]:  # Analyze first 3 voltage columns (A, B, C phases)
                    voltage = pd.to_numeric(transformer_df[col], errors='coerce')
                    phase_name = col.split('_')[-1] if '_' in col else col
                    analysis['voltage_analysis'][phase_name] = {
                        'avg_voltage': float(voltage.mean()),
                        'max_voltage': float(voltage.max()),
                        'min_voltage': float(voltage.min()),
                        'std_voltage': float(voltage.std()),
                        'voltage_drop_percentage': float(((voltage.max() - voltage.min()) / voltage.max()) * 100) if voltage.max() > 0 else 0
                    }
            
            # Analyze current data
            current_cols = [col for col in transformer_df.columns if 'CURRENT' in col.upper()]
            if current_cols:
                for col in current_cols[:3]:  # Analyze first 3 current columns (A, B, C phases)
                    current = pd.to_numeric(transformer_df[col], errors='coerce')
                    phase_name = col.split('_')[-1] if '_' in col else col
                    analysis['current_analysis'][phase_name] = {
                        'avg_current': float(current.mean()),
                        'max_current': float(current.max()),
                        'min_current': float(current.min()),
                        'std_current': float(current.std())
                    }
            
            # Analyze power factor
            pf_cols = [col for col in transformer_df.columns if 'POWER_FACTOR' in col.upper()]
            if pf_cols:
                power_factor = pd.to_numeric(transformer_df[pf_cols[0]], errors='coerce')
                analysis['power_factor_analysis'] = {
                    'avg_power_factor': float(power_factor.mean()),
                    'max_power_factor': float(power_factor.max()),
                    'min_power_factor': float(power_factor.min()),
                    'std_power_factor': float(power_factor.std())
                }
            
            # Generate recommendations
            recommendations = []
            
            # Check for high load utilization
            if 'kva' in analysis['load_analysis']:
                max_kva = analysis['load_analysis']['kva']['max_load_kva']
                if max_kva > 4000:  # Assuming 5kVA transformer
                    recommendations.append({
                        'type': 'warning',
                        'message': f'High transformer utilization detected: {max_kva:.1f} kVA peak load',
                        'suggestion': 'Consider load balancing or transformer upgrade'
                    })
            
            # Check for voltage imbalance
            if len(analysis['voltage_analysis']) >= 3:
                voltages = [data['avg_voltage'] for data in analysis['voltage_analysis'].values()]
                if voltages:
                    avg_voltage = np.mean(voltages)
                    max_deviation = max(abs(v - avg_voltage) for v in voltages)
                    if max_deviation > avg_voltage * 0.05:  # 5% imbalance
                        recommendations.append({
                            'type': 'warning',
                            'message': f'Voltage imbalance detected: {max_deviation:.1f}V deviation',
                            'suggestion': 'Check phase connections and load distribution'
                        })
            
            # Check for low power factor
            if 'avg_power_factor' in analysis['power_factor_analysis']:
                avg_pf = analysis['power_factor_analysis']['avg_power_factor']
                if avg_pf < 0.85:
                    recommendations.append({
                        'type': 'info',
                        'message': f'Low power factor detected: {avg_pf:.2f}',
                        'suggestion': 'Consider power factor correction capacitors'
                    })
            
            analysis['recommendations'] = recommendations
            
            return self._to_json_safe(analysis)
            
        except Exception as e:
            return {
                'error': f'Error analyzing transformer load file: {str(e)}',
                'file_path': transformer_file_path
            }

