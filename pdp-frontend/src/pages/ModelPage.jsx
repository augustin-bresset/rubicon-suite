import { useState, useEffect, useMemo, useCallback } from 'react';
import { useAuth } from '../hooks/useAuth';
import { useMetadata } from '../hooks/usePdp';
import { pdpApi } from '../api/pdpClient';
import ModelSelector from '../components/ModelSelector';
import DesignTable from '../components/DesignTable';
import ModelPreview from '../components/ModelPreview';
import DetailTabs from '../components/DetailTabs';
import Toolbar from '../components/Toolbar';

function ModelPage() {
    const { user, logout } = useAuth();
    const { metadata, loading: metaLoading } = useMetadata();

    // State
    const [modelCode, setModelCode] = useState('');
    const [designs, setDesigns] = useState([]);
    const [selectedDesign, setSelectedDesign] = useState(null);
    const [productData, setProductData] = useState(null);
    const [loading, setLoading] = useState(false);

    // Load designs when model code changes
    const loadDesigns = useCallback(async (code) => {
        if (!code) {
            setDesigns([]);
            setSelectedDesign(null);
            return;
        }

        setLoading(true);
        try {
            // Search products by model code pattern
            const data = await pdpApi.getProducts({ model_code: code });
            setDesigns(data.products || []);
            if (data.products?.length > 0) {
                setSelectedDesign(data.products[0]);
            }
        } catch (err) {
            console.error('Failed to load designs:', err);
            setDesigns([]);
        } finally {
            setLoading(false);
        }
    }, []);

    // Load product data when design is selected
    useEffect(() => {
        if (!selectedDesign?.id) {
            setProductData(null);
            return;
        }

        setLoading(true);
        pdpApi.getProduct(selectedDesign.id)
            .then(data => setProductData(data))
            .catch(err => console.error('Failed to load product:', err))
            .finally(() => setLoading(false));
    }, [selectedDesign?.id]);

    const handleModelSearch = (code) => {
        setModelCode(code);
        loadDesigns(code);
    };

    const handleDesignSelect = (design) => {
        setSelectedDesign(design);
    };

    return (
        <div className="app-container">
            {/* Toolbar */}
            <Toolbar user={user} onLogout={logout} />

            {/* Model Selector */}
            <ModelSelector
                modelCode={modelCode}
                onModelSearch={handleModelSearch}
                designs={designs}
                selectedDesign={selectedDesign}
                onDesignSelect={handleDesignSelect}
                loading={loading}
            />

            {/* Main Content */}
            <div className="main-content">
                {/* Left Panel - Design Table */}
                <div className="left-panel">
                    <DesignTable
                        designs={designs}
                        selectedDesign={selectedDesign}
                        onSelect={handleDesignSelect}
                        loading={loading}
                    />
                </div>

                {/* Center Panel - Detail Tabs */}
                <div className="center-panel">
                    <DetailTabs
                        productData={productData}
                        metadata={metadata}
                        loading={loading}
                    />
                </div>

                {/* Right Panel - Model Preview */}
                <div className="right-panel">
                    <ModelPreview
                        productData={productData}
                        modelCode={modelCode}
                    />
                </div>
            </div>
        </div>
    );
}

export default ModelPage;
