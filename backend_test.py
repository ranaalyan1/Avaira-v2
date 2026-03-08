#!/usr/bin/env python3

import requests
import json
import sys
from datetime import datetime

class AVAIRAProtocolTester:
    def __init__(self, base_url="https://execution-shield.preview.emergentagent.com/api"):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0
        self.failed_tests = []
        self.agent_ids = []
        self.execution_ids = []
        self.underwriter_ids = []
        self.mission_ids = []
        
    def log_result(self, test_name, success, status_code=None, response_data=None, error_msg=None):
        """Log test result"""
        self.tests_run += 1
        status = "✅ PASS" if success else "❌ FAIL"
        
        print(f"\n{status} | {test_name}")
        if status_code:
            print(f"     Status: {status_code}")
        if error_msg:
            print(f"     Error: {error_msg}")
        elif response_data and isinstance(response_data, dict):
            if 'id' in response_data:
                print(f"     ID: {response_data['id']}")
            if 'message' in response_data:
                print(f"     Message: {response_data['message']}")
            
        if success:
            self.tests_passed += 1
        else:
            self.failed_tests.append(f"{test_name}: {error_msg or f'Status {status_code}'}")
            
        return success, response_data

    def make_request(self, method, endpoint, data=None, params=None):
        """Make API request"""
        url = f"{self.base_url}/{endpoint}" if not endpoint.startswith('http') else endpoint
        headers = {'Content-Type': 'application/json'}
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, params=params, timeout=30)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=30)
            elif method == 'PATCH':
                response = requests.patch(url, json=data, headers=headers, params=params, timeout=30)
            else:
                return False, None, f"Unsupported method: {method}"
                
            return True, response, None
            
        except requests.exceptions.RequestException as e:
            return False, None, str(e)

    def test_root_endpoint(self):
        """Test GET /api/ - root endpoint"""
        success, response, error = self.make_request('GET', '')
        if not success:
            return self.log_result("Root Endpoint", False, error_msg=error)
            
        if response.status_code == 200:
            data = response.json()
            expected_keys = ['message', 'status']
            has_keys = all(key in data for key in expected_keys)
            return self.log_result("Root Endpoint", has_keys, response.status_code, data, 
                                 None if has_keys else "Missing expected keys")
        else:
            return self.log_result("Root Endpoint", False, response.status_code, 
                                 error_msg="Expected status 200")

    def test_register_agent(self, name_suffix=""):
        """Test POST /api/agents/register"""
        agent_data = {
            "name": f"TestAgent{name_suffix}",
            "wallet_address": f"0x{'a' * 40}",
            "collateral_amount": 5.0,
            "mission_intent": "Test DeFi operations",
            "risk_envelope": {
                "max_tx_value": 10.0,
                "max_daily_txns": 50,
                "allowed_actions": ["transfer", "swap", "stake"],
                "max_slippage": 0.05
            }
        }
        
        success, response, error = self.make_request('POST', 'agents/register', agent_data)
        if not success:
            return self.log_result("Register Agent", False, error_msg=error)
            
        if response.status_code == 200:
            data = response.json()
            if 'id' in data:
                self.agent_ids.append(data['id'])
            required_fields = ['id', 'name', 'wallet_address', 'status', 'collateral_amount']
            has_fields = all(field in data for field in required_fields)
            return self.log_result("Register Agent", has_fields, response.status_code, data,
                                 None if has_fields else "Missing required fields")
        else:
            return self.log_result("Register Agent", False, response.status_code,
                                 error_msg=f"Expected status 200, got {response.status_code}")

    def test_list_agents(self):
        """Test GET /api/agents"""
        success, response, error = self.make_request('GET', 'agents')
        if not success:
            return self.log_result("List Agents", False, error_msg=error)
            
        if response.status_code == 200:
            data = response.json()
            is_list = isinstance(data, list)
            return self.log_result("List Agents", is_list, response.status_code, 
                                 f"Found {len(data)} agents" if is_list else data,
                                 None if is_list else "Expected list response")
        else:
            return self.log_result("List Agents", False, response.status_code)

    def test_update_agent_status(self):
        """Test PATCH /api/agents/{id}/status"""
        if not self.agent_ids:
            return self.log_result("Update Agent Status", False, error_msg="No agents to test")
            
        agent_id = self.agent_ids[0]
        success, response, error = self.make_request('PATCH', f'agents/{agent_id}/status', 
                                                   params={'status': 'paused'})
        if not success:
            return self.log_result("Update Agent Status", False, error_msg=error)
            
        if response.status_code == 200:
            data = response.json()
            has_message = 'message' in data
            return self.log_result("Update Agent Status", has_message, response.status_code, data,
                                 None if has_message else "Missing message field")
        else:
            return self.log_result("Update Agent Status", False, response.status_code)

    def test_create_execution_valid(self):
        """Test POST /api/executions/request - valid execution"""
        if not self.agent_ids:
            return self.log_result("Create Valid Execution", False, error_msg="No agents to test")
            
        # First ensure agent is active
        agent_id = self.agent_ids[0]
        self.make_request('PATCH', f'agents/{agent_id}/status', params={'status': 'active'})
        
        execution_data = {
            "agent_id": agent_id,
            "action": "transfer",
            "target_address": f"0x{'b' * 40}",
            "value": 2.0,
            "chain_id": "43113"
        }
        
        success, response, error = self.make_request('POST', 'executions/request', execution_data)
        if not success:
            return self.log_result("Create Valid Execution", False, error_msg=error)
            
        if response.status_code == 200:
            data = response.json()
            if 'id' in data:
                self.execution_ids.append(data['id'])
            required_fields = ['id', 'status', 'lifecycle']
            has_fields = all(field in data for field in required_fields)
            is_completed = data.get('status') == 'completed'
            
            success_result = has_fields and is_completed
            return self.log_result("Create Valid Execution", success_result, response.status_code, data,
                                 None if success_result else f"Status: {data.get('status')}, Missing fields: {[f for f in required_fields if f not in data]}")
        else:
            return self.log_result("Create Valid Execution", False, response.status_code)

    def test_create_execution_deviation(self):
        """Test POST /api/executions/request - deviation execution"""
        if not self.agent_ids:
            return self.log_result("Create Deviation Execution", False, error_msg="No agents to test")
            
        # Ensure agent is active first
        agent_id = self.agent_ids[0]  
        self.make_request('PATCH', f'agents/{agent_id}/status', params={'status': 'active'})
        
        execution_data = {
            "agent_id": agent_id,
            "action": "liquidate",  # Not in allowed_actions
            "target_address": f"0x{'c' * 40}",
            "value": 15.0,  # Exceeds max_tx_value of 10.0
            "chain_id": "43113"
        }
        
        success, response, error = self.make_request('POST', 'executions/request', execution_data)
        if not success:
            return self.log_result("Create Deviation Execution", False, error_msg=error)
            
        if response.status_code == 200:
            data = response.json()
            is_rejected = data.get('status') == 'rejected_deviation'
            return self.log_result("Create Deviation Execution", is_rejected, response.status_code, data,
                                 None if is_rejected else f"Expected 'rejected_deviation', got '{data.get('status')}'")
        else:
            return self.log_result("Create Deviation Execution", False, response.status_code)

    def test_list_executions(self):
        """Test GET /api/executions"""
        success, response, error = self.make_request('GET', 'executions')
        if not success:
            return self.log_result("List Executions", False, error_msg=error)
            
        if response.status_code == 200:
            data = response.json()
            is_list = isinstance(data, list)
            return self.log_result("List Executions", is_list, response.status_code,
                                 f"Found {len(data)} executions" if is_list else data,
                                 None if is_list else "Expected list response")
        else:
            return self.log_result("List Executions", False, response.status_code)

    def test_freeze_agent(self):
        """Test POST /api/freeze/{agent_id}"""
        if not self.agent_ids:
            return self.log_result("Freeze Agent", False, error_msg="No agents to test")
            
        agent_id = self.agent_ids[0]
        freeze_data = {"reason": "Testing freeze functionality"}
        
        success, response, error = self.make_request('POST', f'freeze/{agent_id}', freeze_data)
        if not success:
            return self.log_result("Freeze Agent", False, error_msg=error)
            
        if response.status_code == 200:
            data = response.json()
            required_fields = ['id', 'type', 'reason']
            has_fields = all(field in data for field in required_fields)
            is_freeze = data.get('type') == 'freeze'
            
            success_result = has_fields and is_freeze
            return self.log_result("Freeze Agent", success_result, response.status_code, data,
                                 None if success_result else "Missing required fields or wrong type")
        else:
            return self.log_result("Freeze Agent", False, response.status_code)

    def test_slash_agent(self):
        """Test POST /api/slash/{agent_id}"""
        if not self.agent_ids:
            return self.log_result("Slash Agent", False, error_msg="No agents to test")
            
        agent_id = self.agent_ids[0]
        slash_data = {"reason": "Testing slash functionality", "amount": 1.0}
        
        success, response, error = self.make_request('POST', f'slash/{agent_id}', slash_data)
        if not success:
            return self.log_result("Slash Agent", False, error_msg=error)
            
        if response.status_code == 200:
            data = response.json()
            required_fields = ['id', 'type', 'collateral_slashed', 'collateral_remaining']
            has_fields = all(field in data for field in required_fields)
            is_slash = data.get('type') == 'slash'
            
            success_result = has_fields and is_slash
            return self.log_result("Slash Agent", success_result, response.status_code, data,
                                 None if success_result else "Missing required fields or wrong type")
        else:
            return self.log_result("Slash Agent", False, response.status_code)

    def test_freeze_events(self):
        """Test GET /api/freeze/events"""
        success, response, error = self.make_request('GET', 'freeze/events')
        if not success:
            return self.log_result("List Freeze Events", False, error_msg=error)
            
        if response.status_code == 200:
            data = response.json()
            is_list = isinstance(data, list)
            return self.log_result("List Freeze Events", is_list, response.status_code,
                                 f"Found {len(data)} events" if is_list else data,
                                 None if is_list else "Expected list response")
        else:
            return self.log_result("List Freeze Events", False, response.status_code)

    def test_treasury_stats(self):
        """Test GET /api/treasury/stats"""
        success, response, error = self.make_request('GET', 'treasury/stats')
        if not success:
            return self.log_result("Treasury Stats", False, error_msg=error)
            
        if response.status_code == 200:
            data = response.json()
            required_fields = ['total_fees', 'total_trust_pool', 'total_protocol_revenue', 'transaction_count']
            has_fields = all(field in data for field in required_fields)
            return self.log_result("Treasury Stats", has_fields, response.status_code, data,
                                 None if has_fields else f"Missing fields: {[f for f in required_fields if f not in data]}")
        else:
            return self.log_result("Treasury Stats", False, response.status_code)

    def test_treasury_transactions(self):
        """Test GET /api/treasury/transactions"""
        success, response, error = self.make_request('GET', 'treasury/transactions')
        if not success:
            return self.log_result("Treasury Transactions", False, error_msg=error)
            
        if response.status_code == 200:
            data = response.json()
            is_list = isinstance(data, list)
            return self.log_result("Treasury Transactions", is_list, response.status_code,
                                 f"Found {len(data)} transactions" if is_list else data,
                                 None if is_list else "Expected list response")
        else:
            return self.log_result("Treasury Transactions", False, response.status_code)

    def test_reputation_leaderboard(self):
        """Test GET /api/reputation/leaderboard"""
        success, response, error = self.make_request('GET', 'reputation/leaderboard')
        if not success:
            return self.log_result("Reputation Leaderboard", False, error_msg=error)
            
        if response.status_code == 200:
            data = response.json()
            is_list = isinstance(data, list)
            return self.log_result("Reputation Leaderboard", is_list, response.status_code,
                                 f"Found {len(data)} agents" if is_list else data,
                                 None if is_list else "Expected list response")
        else:
            return self.log_result("Reputation Leaderboard", False, response.status_code)

    def test_reputation_history(self):
        """Test GET /api/reputation/history"""
        success, response, error = self.make_request('GET', 'reputation/history')
        if not success:
            return self.log_result("Reputation History", False, error_msg=error)
            
        if response.status_code == 200:
            data = response.json()
            is_list = isinstance(data, list)
            return self.log_result("Reputation History", is_list, response.status_code,
                                 f"Found {len(data)} history entries" if is_list else data,
                                 None if is_list else "Expected list response")
        else:
            return self.log_result("Reputation History", False, response.status_code)

    def test_dashboard_stats(self):
        """Test GET /api/dashboard/stats"""
        success, response, error = self.make_request('GET', 'dashboard/stats')
        if not success:
            return self.log_result("Dashboard Stats", False, error_msg=error)
            
        if response.status_code == 200:
            data = response.json()
            required_fields = ['total_agents', 'active_agents', 'total_executions', 'total_fees_collected']
            has_fields = all(field in data for field in required_fields)
            return self.log_result("Dashboard Stats", has_fields, response.status_code, data,
                                 None if has_fields else f"Missing fields: {[f for f in required_fields if f not in data]}")
        else:
            return self.log_result("Dashboard Stats", False, response.status_code)

    def test_dashboard_activity(self):
        """Test GET /api/dashboard/activity"""
        success, response, error = self.make_request('GET', 'dashboard/activity')
        if not success:
            return self.log_result("Dashboard Activity", False, error_msg=error)
            
        if response.status_code == 200:
            data = response.json()
            is_list = isinstance(data, list)
            return self.log_result("Dashboard Activity", is_list, response.status_code,
                                 f"Found {len(data)} activities" if is_list else data,
                                 None if is_list else "Expected list response")
        else:
            return self.log_result("Dashboard Activity", False, response.status_code)

    def test_simulate_lifecycle(self):
        """Test POST /api/simulate/lifecycle"""
        success, response, error = self.make_request('POST', 'simulate/lifecycle')
        if not success:
            return self.log_result("Simulate Lifecycle", False, error_msg=error)
            
        if response.status_code == 200:
            data = response.json()
            required_fields = ['simulation_id', 'steps', 'final_agent_state', 'treasury_stats']
            has_fields = all(field in data for field in required_fields)
            has_steps = isinstance(data.get('steps'), list) and len(data.get('steps', [])) > 0
            
            success_result = has_fields and has_steps
            return self.log_result("Simulate Lifecycle", success_result, response.status_code, 
                                 f"Completed {len(data.get('steps', []))} steps" if has_steps else data,
                                 None if success_result else "Missing fields or no steps")
        else:
            return self.log_result("Simulate Lifecycle", False, response.status_code)

    def test_contracts_architecture(self):
        """Test GET /api/contracts"""
        success, response, error = self.make_request('GET', 'contracts')
        if not success:
            return self.log_result("Smart Contracts", False, error_msg=error)
            
        if response.status_code == 200:
            data = response.json()
            has_contracts = 'contracts' in data and isinstance(data['contracts'], list)
            contract_count = len(data.get('contracts', [])) if has_contracts else 0
            expected_contracts = 6  # Based on the backend code
            
            success_result = has_contracts and contract_count >= expected_contracts
            return self.log_result("Smart Contracts", success_result, response.status_code,
                                 f"Found {contract_count} contracts" if has_contracts else data,
                                 None if success_result else f"Expected at least {expected_contracts} contracts")
        else:
            return self.log_result("Smart Contracts", False, response.status_code)

    # ─── NEW AVAIRA SCORE ENGINE TESTS ─────────────────────────────────
    def test_scores_all(self):
        """Test GET /api/scores/all - returns agents with AAA-D grades"""
        success, response, error = self.make_request('GET', 'scores/all')
        if not success:
            return self.log_result("Avaira Scores All", False, error_msg=error)
            
        if response.status_code == 200:
            data = response.json()
            is_list = isinstance(data, list)
            if is_list and len(data) > 0:
                # Check first score entry has required fields
                first_score = data[0]
                required_fields = ['agent_id', 'agent_name', 'status', 'grade', 'composite_score']
                has_fields = all(field in first_score for field in required_fields)
                valid_grade = first_score.get('grade') in ['AAA', 'AA', 'A', 'BBB', 'BB', 'B', 'CCC', 'D']
                
                success_result = has_fields and valid_grade
                return self.log_result("Avaira Scores All", success_result, response.status_code,
                                     f"Found {len(data)} agents with scores" if success_result else data,
                                     None if success_result else f"Missing fields or invalid grade: {first_score.get('grade')}")
            else:
                return self.log_result("Avaira Scores All", is_list, response.status_code,
                                     f"Found {len(data)} agents" if is_list else data,
                                     None if is_list else "Expected list response")
        else:
            return self.log_result("Avaira Scores All", False, response.status_code)

    def test_agent_score_detail(self):
        """Test GET /api/agents/{id}/score - returns detailed score with factors and weights"""
        if not self.agent_ids:
            return self.log_result("Agent Score Detail", False, error_msg="No agents to test")
            
        agent_id = self.agent_ids[0]
        success, response, error = self.make_request('GET', f'agents/{agent_id}/score')
        if not success:
            return self.log_result("Agent Score Detail", False, error_msg=error)
            
        if response.status_code == 200:
            data = response.json()
            required_fields = ['composite_score', 'grade', 'factors', 'weights', 'agent_id', 'agent_name']
            has_fields = all(field in data for field in required_fields)
            
            # Check factors structure
            factors = data.get('factors', {})
            expected_factors = ['success_rate', 'behavioral_consistency', 'collateral_ratio', 'mission_complexity', 'time_on_network', 'deviation_penalty']
            has_factors = all(factor in factors for factor in expected_factors)
            
            # Check weights structure
            weights = data.get('weights', {})
            has_weights = all(factor in weights for factor in expected_factors)
            
            valid_grade = data.get('grade') in ['AAA', 'AA', 'A', 'BBB', 'BB', 'B', 'CCC', 'D']
            
            success_result = has_fields and has_factors and has_weights and valid_grade
            return self.log_result("Agent Score Detail", success_result, response.status_code, 
                                 f"Grade: {data.get('grade')}, Score: {data.get('composite_score')}" if success_result else data,
                                 None if success_result else "Missing required score structure")
        else:
            return self.log_result("Agent Score Detail", False, response.status_code)

    # ─── UNDERWRITER SYSTEM TESTS ──────────────────────────────────────
    def test_register_underwriter(self):
        """Test POST /api/underwriters/register - register a new underwriter"""
        underwriter_data = {
            "name": "TestUnderwriter1",
            "capital_amount": 10.0
        }
        
        success, response, error = self.make_request('POST', 'underwriters/register', underwriter_data)
        if not success:
            return self.log_result("Register Underwriter", False, error_msg=error)
            
        if response.status_code == 200:
            data = response.json()
            if 'id' in data:
                self.underwriter_ids = getattr(self, 'underwriter_ids', [])
                self.underwriter_ids.append(data['id'])
            required_fields = ['id', 'name', 'capital_amount', 'capital_available', 'status']
            has_fields = all(field in data for field in required_fields)
            return self.log_result("Register Underwriter", has_fields, response.status_code, data,
                                 None if has_fields else "Missing required fields")
        else:
            return self.log_result("Register Underwriter", False, response.status_code)

    def test_list_underwriters(self):
        """Test GET /api/underwriters - list underwriters"""
        success, response, error = self.make_request('GET', 'underwriters')
        if not success:
            return self.log_result("List Underwriters", False, error_msg=error)
            
        if response.status_code == 200:
            data = response.json()
            is_list = isinstance(data, list)
            return self.log_result("List Underwriters", is_list, response.status_code,
                                 f"Found {len(data)} underwriters" if is_list else data,
                                 None if is_list else "Expected list response")
        else:
            return self.log_result("List Underwriters", False, response.status_code)

    # ─── MISSION SYSTEM TESTS ──────────────────────────────────────────
    def test_create_mission(self):
        """Test POST /api/missions/create - create a new mission"""
        if not self.agent_ids:
            return self.log_result("Create Mission", False, error_msg="No agents to test")
        
        # Ensure agent is active before creating mission
        agent_id = self.agent_ids[0]
        success, response, error = self.make_request('PATCH', f'agents/{agent_id}/status', params={'status': 'active'})
        if not success or response.status_code != 200:
            return self.log_result("Create Mission", False, error_msg="Failed to activate agent")
            
        mission_data = {
            "agent_id": agent_id,
            "description": "Test DeFi rebalance mission",
            "target_value": 5.0,
            "duration_hours": 24,
            "risk_level": "medium"
        }
        
        success, response, error = self.make_request('POST', 'missions/create', mission_data)
        if not success:
            return self.log_result("Create Mission", False, error_msg=error)
            
        if response.status_code == 200:
            data = response.json()
            if 'id' in data:
                self.mission_ids = getattr(self, 'mission_ids', [])
                self.mission_ids.append(data['id'])
            required_fields = ['id', 'agent_id', 'agent_name', 'agent_grade', 'description', 'status', 'fee_split']
            has_fields = all(field in data for field in required_fields)
            is_open = data.get('status') == 'open'
            
            success_result = has_fields and is_open
            return self.log_result("Create Mission", success_result, response.status_code, data,
                                 None if success_result else f"Status: {data.get('status')}, Missing fields")
        else:
            return self.log_result("Create Mission", False, response.status_code)

    def test_list_missions(self):
        """Test GET /api/missions - list missions"""
        success, response, error = self.make_request('GET', 'missions')
        if not success:
            return self.log_result("List Missions", False, error_msg=error)
            
        if response.status_code == 200:
            data = response.json()
            is_list = isinstance(data, list)
            return self.log_result("List Missions", is_list, response.status_code,
                                 f"Found {len(data)} missions" if is_list else data,
                                 None if is_list else "Expected list response")
        else:
            return self.log_result("List Missions", False, response.status_code)

    def test_stake_on_mission(self):
        """Test POST /api/missions/{id}/stake - underwriter stakes on a mission"""
        if not hasattr(self, 'mission_ids') or not self.mission_ids:
            return self.log_result("Stake on Mission", False, error_msg="No missions to test")
        if not hasattr(self, 'underwriter_ids') or not self.underwriter_ids:
            return self.log_result("Stake on Mission", False, error_msg="No underwriters to test")
            
        mission_id = self.mission_ids[0]
        stake_data = {
            "underwriter_id": self.underwriter_ids[0],
            "amount": 2.0
        }
        
        success, response, error = self.make_request('POST', f'missions/{mission_id}/stake', stake_data)
        if not success:
            return self.log_result("Stake on Mission", False, error_msg=error)
            
        if response.status_code == 200:
            data = response.json()
            has_underwriters = 'underwriters' in data and len(data['underwriters']) > 0
            has_staked_amount = 'total_staked' in data and data['total_staked'] > 0
            
            success_result = has_underwriters and has_staked_amount
            return self.log_result("Stake on Mission", success_result, response.status_code,
                                 f"Staked: {data.get('total_staked')} AVAX" if success_result else data,
                                 None if success_result else "Missing stake data")
        else:
            return self.log_result("Stake on Mission", False, response.status_code)

    def test_settle_mission_success(self):
        """Test POST /api/missions/{id}/settle?success=true - settle mission successfully"""
        if not hasattr(self, 'mission_ids') or not self.mission_ids:
            return self.log_result("Settle Mission Success", False, error_msg="No missions to test")
            
        mission_id = self.mission_ids[0]
        success, response, error = self.make_request('POST', f'missions/{mission_id}/settle?success=true')
        if not success:
            return self.log_result("Settle Mission Success", False, error_msg=error)
            
        if response.status_code == 200:
            data = response.json()
            required_fields = ['status', 'result', 'agent_payout', 'underwriter_payout', 'protocol_fee']
            has_fields = all(field in data for field in required_fields)
            is_settled = data.get('status') == 'settled' and data.get('result') == 'success'
            
            success_result = has_fields and is_settled
            return self.log_result("Settle Mission Success", success_result, response.status_code, data,
                                 None if success_result else f"Status: {data.get('status')}, Result: {data.get('result')}")
        else:
            return self.log_result("Settle Mission Success", False, response.status_code)

    def test_settle_mission_fail(self):
        """Test POST /api/missions/{id}/settle?success=false - settle mission as failed"""
        # Create another mission for fail test
        if not self.agent_ids:
            return self.log_result("Settle Mission Fail", False, error_msg="No agents to test")
            
        # First create a new mission
        mission_data = {
            "agent_id": self.agent_ids[0],
            "description": "Test mission for failure",
            "target_value": 3.0,
            "duration_hours": 12,
            "risk_level": "high"
        }
        
        success, response, error = self.make_request('POST', 'missions/create', mission_data)
        if not success or response.status_code != 200:
            return self.log_result("Settle Mission Fail", False, error_msg="Failed to create test mission")
            
        mission_id = response.json()['id']
        
        # Now settle as failed
        success, response, error = self.make_request('POST', f'missions/{mission_id}/settle?success=false')
        if not success:
            return self.log_result("Settle Mission Fail", False, error_msg=error)
            
        if response.status_code == 200:
            data = response.json()
            required_fields = ['status', 'result', 'coverage_provided']
            has_fields = all(field in data for field in required_fields)
            is_failed = data.get('status') == 'settled' and data.get('result') == 'failed'
            
            success_result = has_fields and is_failed
            return self.log_result("Settle Mission Fail", success_result, response.status_code, data,
                                 None if success_result else f"Status: {data.get('status')}, Result: {data.get('result')}")
        else:
            return self.log_result("Settle Mission Fail", False, response.status_code)

    # ─── REVENUE STREAMS TESTS ─────────────────────────────────────────
    def test_revenue_streams(self):
        """Test GET /api/revenue/streams - returns 4 revenue streams"""
        success, response, error = self.make_request('GET', 'revenue/streams')
        if not success:
            return self.log_result("Revenue Streams", False, error_msg=error)
            
        if response.status_code == 200:
            data = response.json()
            has_streams = 'streams' in data and isinstance(data['streams'], list)
            has_total = 'total_revenue' in data
            
            if has_streams:
                streams = data['streams']
                expected_count = 4
                has_expected_count = len(streams) == expected_count
                
                # Check each stream has required fields
                stream_fields = ['name', 'description', 'amount', 'transactions', 'icon']
                all_streams_valid = all(
                    all(field in stream for field in stream_fields) 
                    for stream in streams
                )
                
                success_result = has_expected_count and all_streams_valid and has_total
                return self.log_result("Revenue Streams", success_result, response.status_code,
                                     f"Found {len(streams)} streams, Total: {data.get('total_revenue', 0)}" if success_result else data,
                                     None if success_result else f"Expected {expected_count} streams with all fields")
            else:
                return self.log_result("Revenue Streams", False, response.status_code,
                                     error_msg="Missing streams field or not a list")
        else:
            return self.log_result("Revenue Streams", False, response.status_code)

    # ─── SDK DOCUMENTATION TESTS ───────────────────────────────────────
    def test_sdk_docs(self):
        """Test GET /api/sdk/docs - returns SDK documentation data"""
        success, response, error = self.make_request('GET', 'sdk/docs')
        if not success:
            return self.log_result("SDK Documentation", False, error_msg=error)
            
        if response.status_code == 200:
            data = response.json()
            required_fields = ['sdk_name', 'languages', 'version', 'install', 'functions', 'quick_start']
            has_fields = all(field in data for field in required_fields)
            
            # Check functions structure
            functions = data.get('functions', [])
            expected_functions = ['register', 'declareIntent', 'execute', 'settle']
            has_expected_functions = len(functions) >= len(expected_functions)
            
            if has_expected_functions and functions:
                function_names = [f.get('name') for f in functions]
                all_expected_present = all(name in function_names for name in expected_functions)
            else:
                all_expected_present = False
                
            success_result = has_fields and has_expected_functions and all_expected_present
            return self.log_result("SDK Documentation", success_result, response.status_code,
                                 f"SDK: {data.get('sdk_name')}, Functions: {len(functions)}" if success_result else data,
                                 None if success_result else "Missing required SDK structure")
        else:
            return self.log_result("SDK Documentation", False, response.status_code)

    def run_all_tests(self):
        """Run comprehensive test suite"""
        print("🚀 AVAIRA Protocol Backend Testing - ITERATION 2")
        print("Testing: Avaira Score Engine + Underwriter System + Revenue Streams + SDK Docs")
        print("=" * 80)
        
        # Core API tests
        self.test_root_endpoint()
        
        # Agent management (needed for other tests)
        self.test_register_agent("_1")
        self.test_register_agent("_2")  # Register multiple agents for testing
        self.test_list_agents()
        self.test_update_agent_status()
        
        # NEW: Avaira Score Engine tests
        print("\n🎯 AVAIRA SCORE ENGINE TESTS")
        self.test_scores_all()
        self.test_agent_score_detail()
        
        # NEW: Underwriter system tests  
        print("\n👥 UNDERWRITER SYSTEM TESTS")
        self.test_register_underwriter()
        self.test_list_underwriters()
        
        # NEW: Mission system tests
        print("\n🎯 MISSION MARKETPLACE TESTS")
        self.test_create_mission()
        self.test_list_missions()
        self.test_stake_on_mission()
        self.test_settle_mission_success()
        self.test_settle_mission_fail()
        
        # NEW: Revenue streams tests
        print("\n💰 REVENUE STREAMS TESTS")
        self.test_revenue_streams()
        
        # NEW: SDK documentation tests
        print("\n📚 SDK DOCUMENTATION TESTS")
        self.test_sdk_docs()
        
        # Execution flow (core functionality)
        print("\n⚡ EXECUTION FLOW TESTS")
        self.test_create_execution_valid()
        self.test_create_execution_deviation()
        self.test_list_executions()
        
        # Freeze & Slash
        print("\n❄️ FREEZE/SLASH TESTS")
        self.test_freeze_agent()
        self.test_slash_agent()
        self.test_freeze_events()
        
        # Treasury
        print("\n🏦 TREASURY TESTS")
        self.test_treasury_stats()
        self.test_treasury_transactions()
        
        # Reputation
        print("\n⭐ REPUTATION TESTS")
        self.test_reputation_leaderboard()
        self.test_reputation_history()
        
        # Dashboard
        print("\n📊 DASHBOARD TESTS")
        self.test_dashboard_stats()
        self.test_dashboard_activity()
        
        # Simulation & Contracts
        print("\n🔬 SIMULATION & CONTRACTS TESTS")
        self.test_simulate_lifecycle()
        self.test_contracts_architecture()
        
        # Print summary
        print("\n" + "=" * 80)
        print(f"📊 TEST SUMMARY - ITERATION 2")
        print(f"Total Tests: {self.tests_run}")
        print(f"Passed: {self.tests_passed}")
        print(f"Failed: {self.tests_run - self.tests_passed}")
        print(f"Success Rate: {(self.tests_passed / self.tests_run * 100):.1f}%")
        
        if self.failed_tests:
            print(f"\n❌ FAILED TESTS:")
            for failure in self.failed_tests:
                print(f"   • {failure}")
        else:
            print(f"\n✅ ALL TESTS PASSED!")
        
        return self.tests_passed, self.tests_run, self.failed_tests

if __name__ == "__main__":
    tester = AVAIRAProtocolTester()
    passed, total, failures = tester.run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if passed == total else 1)