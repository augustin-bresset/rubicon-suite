/**
 * PDP API Client
 * Handles all API communication with the Odoo backend
 */

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8069/api/v1';

class PdpApiClient {
    constructor() {
        this.token = localStorage.getItem('pdp_token');
    }

    setToken(token) {
        this.token = token;
        if (token) {
            localStorage.setItem('pdp_token', token);
        } else {
            localStorage.removeItem('pdp_token');
        }
    }

    getToken() {
        return this.token || localStorage.getItem('pdp_token');
    }

    async request(endpoint, options = {}) {
        const url = `${API_URL}${endpoint}`;
        const headers = {
            'Content-Type': 'application/json',
            ...options.headers,
        };

        if (this.getToken()) {
            headers['Authorization'] = `Bearer ${this.getToken()}`;
        }

        const response = await fetch(url, {
            ...options,
            headers,
        });

        const data = await response.json();

        if (!response.ok) {
            throw new ApiError(data.error || 'Request failed', response.status);
        }

        return data;
    }

    // ========================================
    // Auth Endpoints
    // ========================================

    async login(login, password) {
        const data = await this.request('/auth/login', {
            method: 'POST',
            body: JSON.stringify({ login, password }),
        });
        this.setToken(data.token);
        return data;
    }

    async refresh() {
        const data = await this.request('/auth/refresh', {
            method: 'POST',
        });
        this.setToken(data.token);
        return data;
    }

    async me() {
        return this.request('/auth/me');
    }

    logout() {
        this.setToken(null);
    }

    // ========================================
    // Product Endpoints
    // ========================================

    async getProducts(params = {}) {
        const queryString = new URLSearchParams(params).toString();
        const endpoint = queryString ? `/pdp/products?${queryString}` : '/pdp/products';
        return this.request(endpoint);
    }

    async getProduct(productId) {
        return this.request(`/pdp/products/${productId}`);
    }

    async computePrice(productId, marginId, currencyId) {
        return this.request(`/pdp/products/${productId}/price`, {
            method: 'POST',
            body: JSON.stringify({
                margin_id: marginId,
                currency_id: currencyId,
            }),
        });
    }

    // ========================================
    // Metadata Endpoints
    // ========================================

    async getMetadata() {
        return this.request('/pdp/metadata');
    }
}

class ApiError extends Error {
    constructor(message, status) {
        super(message);
        this.name = 'ApiError';
        this.status = status;
    }
}

// Singleton instance
export const pdpApi = new PdpApiClient();
export { ApiError };
