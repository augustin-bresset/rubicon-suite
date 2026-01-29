import { useState, useEffect } from 'react';
import { pdpApi, ApiError } from '../api/pdpClient';

/**
 * Hook to fetch a single product
 */
export function useProduct(productId) {
    const [product, setProduct] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        if (!productId) {
            setLoading(false);
            return;
        }

        setLoading(true);
        setError(null);

        pdpApi.getProduct(productId)
            .then(data => setProduct(data))
            .catch(err => setError(err.message))
            .finally(() => setLoading(false));
    }, [productId]);

    return {
        product, loading, error, refetch: () => {
            setLoading(true);
            pdpApi.getProduct(productId)
                .then(data => setProduct(data))
                .catch(err => setError(err.message))
                .finally(() => setLoading(false));
        }
    };
}

/**
 * Hook to fetch product list
 */
export function useProducts(modelId = null) {
    const [products, setProducts] = useState([]);
    const [total, setTotal] = useState(0);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        setLoading(true);
        setError(null);

        const params = {};
        if (modelId) params.model_id = modelId;

        pdpApi.getProducts(params)
            .then(data => {
                setProducts(data.products || []);
                setTotal(data.total || 0);
            })
            .catch(err => setError(err.message))
            .finally(() => setLoading(false));
    }, [modelId]);

    return { products, total, loading, error };
}

/**
 * Hook to fetch metadata
 */
export function useMetadata() {
    const [metadata, setMetadata] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        pdpApi.getMetadata()
            .then(data => setMetadata(data))
            .catch(err => setError(err.message))
            .finally(() => setLoading(false));
    }, []);

    return { metadata, loading, error };
}

/**
 * Hook to compute price
 */
export function usePriceCompute() {
    const [result, setResult] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    const compute = async (productId, marginId, currencyId) => {
        setLoading(true);
        setError(null);
        try {
            const data = await pdpApi.computePrice(productId, marginId, currencyId);
            setResult(data);
            return data;
        } catch (err) {
            setError(err.message);
            throw err;
        } finally {
            setLoading(false);
        }
    };

    return { result, loading, error, compute };
}
