#!/usr/bin/env python3
"""
PDP API Test Script

This script tests all PDP API endpoints to verify they work correctly.
Run this after starting Odoo with the pdp_api module installed.

Usage:
    python test_api.py [--base-url URL] [--login USER] [--password PASS]

Example:
    python test_api.py --base-url http://localhost:8069/api/v1
"""

import argparse
import json
import sys
import requests


class Colors:
    """ANSI color codes for terminal output."""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    RESET = '\033[0m'


def log_success(message):
    print(f"{Colors.GREEN}[PASS]{Colors.RESET} {message}")


def log_failure(message):
    print(f"{Colors.RED}[FAIL]{Colors.RESET} {message}")


def log_info(message):
    print(f"{Colors.YELLOW}[INFO]{Colors.RESET} {message}")


class ApiTester:
    """Test runner for PDP API endpoints."""

    def __init__(self, base_url, login, password):
        self.base_url = base_url.rstrip('/')
        self.login = login
        self.password = password
        self.token = None
        self.results = {'passed': 0, 'failed': 0}

    def run_all_tests(self):
        """Run all API tests in sequence."""
        print("\n" + "=" * 60)
        print("PDP API Test Suite")
        print("=" * 60)
        print(f"Base URL: {self.base_url}")
        print(f"Login: {self.login}")
        print("=" * 60 + "\n")

        # Authentication tests
        self.test_login()
        if not self.token:
            log_failure("Cannot proceed without authentication")
            return self.results

        self.test_auth_me()
        self.test_auth_refresh()

        # Product tests
        self.test_list_products()
        self.test_get_product()
        self.test_compute_price()

        # Metadata tests
        self.test_get_metadata()

        # Summary
        print("\n" + "=" * 60)
        print(f"Results: {self.results['passed']} passed, {self.results['failed']} failed")
        print("=" * 60 + "\n")

        return self.results

    def _request(self, method, endpoint, data=None, auth=True):
        """Make an HTTP request to the API."""
        url = f"{self.base_url}{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        if auth and self.token:
            headers['Authorization'] = f'Bearer {self.token}'

        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=10)
            elif method == 'POST':
                response = requests.post(url, headers=headers, json=data, timeout=10)
            else:
                raise ValueError(f"Unsupported method: {method}")

            return response
        except requests.exceptions.ConnectionError:
            return None
        except requests.exceptions.Timeout:
            return None

    def _record_result(self, passed, test_name, details=""):
        """Record test result."""
        if passed:
            self.results['passed'] += 1
            log_success(f"{test_name} {details}")
        else:
            self.results['failed'] += 1
            log_failure(f"{test_name} {details}")

    # =========================================================================
    # Authentication Tests
    # =========================================================================

    def test_login(self):
        """Test POST /auth/login"""
        log_info("Testing POST /auth/login")
        
        response = self._request('POST', '/auth/login', {
            'login': self.login,
            'password': self.password
        }, auth=False)

        if response is None:
            self._record_result(False, "POST /auth/login", "- Connection failed")
            return

        if response.status_code == 200:
            data = response.json()
            if 'token' in data:
                self.token = data['token']
                self._record_result(True, "POST /auth/login", f"- Token received")
            else:
                self._record_result(False, "POST /auth/login", "- No token in response")
        else:
            self._record_result(False, "POST /auth/login", f"- Status {response.status_code}: {response.text}")

    def test_auth_me(self):
        """Test GET /auth/me"""
        log_info("Testing GET /auth/me")
        
        response = self._request('GET', '/auth/me')

        if response is None:
            self._record_result(False, "GET /auth/me", "- Connection failed")
            return

        if response.status_code == 200:
            data = response.json()
            if 'login' in data:
                self._record_result(True, "GET /auth/me", f"- User: {data.get('name', 'unknown')}")
            else:
                self._record_result(False, "GET /auth/me", "- Invalid response format")
        else:
            self._record_result(False, "GET /auth/me", f"- Status {response.status_code}")

    def test_auth_refresh(self):
        """Test POST /auth/refresh"""
        log_info("Testing POST /auth/refresh")
        
        response = self._request('POST', '/auth/refresh')

        if response is None:
            self._record_result(False, "POST /auth/refresh", "- Connection failed")
            return

        if response.status_code == 200:
            data = response.json()
            if 'token' in data:
                self.token = data['token']
                self._record_result(True, "POST /auth/refresh", "- New token received")
            else:
                self._record_result(False, "POST /auth/refresh", "- No token in response")
        else:
            self._record_result(False, "POST /auth/refresh", f"- Status {response.status_code}")

    # =========================================================================
    # Product Tests
    # =========================================================================

    def test_list_products(self):
        """Test GET /pdp/products"""
        log_info("Testing GET /pdp/products")
        
        response = self._request('GET', '/pdp/products')

        if response is None:
            self._record_result(False, "GET /pdp/products", "- Connection failed")
            return

        if response.status_code == 200:
            data = response.json()
            if 'products' in data:
                count = len(data['products'])
                total = data.get('total', count)
                self._record_result(True, "GET /pdp/products", f"- {count} products (total: {total})")
            else:
                self._record_result(False, "GET /pdp/products", "- Invalid response format")
        elif response.status_code == 403:
            self._record_result(False, "GET /pdp/products", "- Permission denied")
        else:
            self._record_result(False, "GET /pdp/products", f"- Status {response.status_code}")

    def test_get_product(self):
        """Test GET /pdp/products/{id}"""
        log_info("Testing GET /pdp/products/{id}")
        
        # First get a product ID from the list
        response = self._request('GET', '/pdp/products?limit=1')
        
        if response is None or response.status_code != 200:
            self._record_result(False, "GET /pdp/products/{id}", "- Could not get product list")
            return

        data = response.json()
        products = data.get('products', [])
        
        if not products:
            log_info("No products found, skipping detail test")
            self._record_result(True, "GET /pdp/products/{id}", "- Skipped (no products)")
            return

        product_id = products[0]['id']
        response = self._request('GET', f'/pdp/products/{product_id}')

        if response is None:
            self._record_result(False, "GET /pdp/products/{id}", "- Connection failed")
            return

        if response.status_code == 200:
            data = response.json()
            if 'product' in data and 'weights' in data:
                self._record_result(True, "GET /pdp/products/{id}", f"- Product {product_id} loaded")
            else:
                self._record_result(False, "GET /pdp/products/{id}", "- Invalid response format")
        else:
            self._record_result(False, "GET /pdp/products/{id}", f"- Status {response.status_code}")

    def test_compute_price(self):
        """Test POST /pdp/products/{id}/price"""
        log_info("Testing POST /pdp/products/{id}/price")
        
        # Get a product ID and metadata
        response = self._request('GET', '/pdp/products?limit=1')
        
        if response is None or response.status_code != 200:
            self._record_result(False, "POST /pdp/products/{id}/price", "- Could not get product list")
            return

        products = response.json().get('products', [])
        if not products:
            log_info("No products found, skipping price test")
            self._record_result(True, "POST /pdp/products/{id}/price", "- Skipped (no products)")
            return

        product_id = products[0]['id']

        # Get metadata for margin and currency
        meta_response = self._request('GET', '/pdp/metadata')
        if meta_response is None or meta_response.status_code != 200:
            self._record_result(False, "POST /pdp/products/{id}/price", "- Could not get metadata")
            return

        meta = meta_response.json()
        margins = meta.get('margins', [])
        currencies = meta.get('currencies', [])

        if not margins or not currencies:
            log_info("No margins or currencies found, skipping price test")
            self._record_result(True, "POST /pdp/products/{id}/price", "- Skipped (no metadata)")
            return

        # Compute price
        response = self._request('POST', f'/pdp/products/{product_id}/price', {
            'margin_id': margins[0]['id'],
            'currency_id': currencies[0]['id']
        })

        if response is None:
            self._record_result(False, "POST /pdp/products/{id}/price", "- Connection failed")
            return

        if response.status_code == 200:
            data = response.json()
            if 'totals' in data:
                total_price = data['totals'].get('price', 0)
                self._record_result(True, "POST /pdp/products/{id}/price", f"- Total: {total_price}")
            else:
                self._record_result(False, "POST /pdp/products/{id}/price", "- Invalid response format")
        else:
            self._record_result(False, "POST /pdp/products/{id}/price", f"- Status {response.status_code}")

    # =========================================================================
    # Metadata Tests
    # =========================================================================

    def test_get_metadata(self):
        """Test GET /pdp/metadata"""
        log_info("Testing GET /pdp/metadata")
        
        response = self._request('GET', '/pdp/metadata')

        if response is None:
            self._record_result(False, "GET /pdp/metadata", "- Connection failed")
            return

        if response.status_code == 200:
            data = response.json()
            expected_keys = ['currencies', 'margins', 'models', 'metals']
            missing = [k for k in expected_keys if k not in data]
            
            if not missing:
                counts = {k: len(data.get(k, [])) for k in expected_keys}
                self._record_result(True, "GET /pdp/metadata", f"- {counts}")
            else:
                self._record_result(False, "GET /pdp/metadata", f"- Missing keys: {missing}")
        else:
            self._record_result(False, "GET /pdp/metadata", f"- Status {response.status_code}")


def main():
    parser = argparse.ArgumentParser(description='Test PDP API endpoints')
    parser.add_argument('--base-url', default='http://localhost:8069/api/v1',
                        help='API base URL (default: http://localhost:8069/api/v1)')
    parser.add_argument('--login', default='admin',
                        help='Login username (default: admin)')
    parser.add_argument('--password', default='admin',
                        help='Login password (default: admin)')
    
    args = parser.parse_args()

    tester = ApiTester(args.base_url, args.login, args.password)
    results = tester.run_all_tests()

    sys.exit(0 if results['failed'] == 0 else 1)


if __name__ == '__main__':
    main()
