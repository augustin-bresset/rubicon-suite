import { useState } from 'react';

function ModelPreview({ productData, modelCode }) {
    const [activeTab, setActiveTab] = useState('model');

    // Get image URL from product data if available
    const imageUrl = productData?.product?.image_url || null;
    const drawingRef = productData?.product?.drawing_ref || null;

    return (
        <div className="model-preview">
            <div className="preview-tabs">
                <button
                    className={`preview-tab ${activeTab === 'model' ? 'active' : ''}`}
                    onClick={() => setActiveTab('model')}
                >
                    Model
                </button>
                <button
                    className={`preview-tab ${activeTab === 'drawing' ? 'active' : ''}`}
                    onClick={() => setActiveTab('drawing')}
                >
                    Drawing
                </button>
            </div>

            <div className="preview-image">
                {activeTab === 'model' ? (
                    imageUrl ? (
                        <img src={imageUrl} alt={`Model ${modelCode}`} />
                    ) : (
                        <div className="empty-state">
                            <p>No image available</p>
                        </div>
                    )
                ) : (
                    <div className="empty-state">
                        {drawingRef ? (
                            <p>Drawing: {drawingRef}</p>
                        ) : (
                            <p>No drawing reference</p>
                        )}
                    </div>
                )}
            </div>
        </div>
    );
}

export default ModelPreview;
