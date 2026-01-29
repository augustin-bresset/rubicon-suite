import { useState, useCallback } from 'react';

function ModelSelector({
    modelCode,
    onModelSearch,
    designs,
    selectedDesign,
    onDesignSelect,
    loading
}) {
    const [inputValue, setInputValue] = useState(modelCode);

    const handleKeyDown = (e) => {
        if (e.key === 'Enter') {
            onModelSearch(inputValue);
        }
    };

    const handleDesignChange = (e) => {
        const designId = parseInt(e.target.value);
        const design = designs.find(d => d.id === designId);
        if (design) {
            onDesignSelect(design);
        }
    };

    return (
        <div className="model-selector">
            <div className="model-input-group">
                <label>Model:</label>
                <input
                    type="text"
                    className="model-input"
                    value={inputValue}
                    onChange={(e) => setInputValue(e.target.value.toUpperCase())}
                    onKeyDown={handleKeyDown}
                    placeholder="R132"
                />
                <button
                    className="btn"
                    onClick={() => onModelSearch(inputValue)}
                    disabled={loading}
                >
                    Search
                </button>
                <button className="btn">
                    List
                </button>
            </div>

            <div className="model-input-group">
                <label>Design:</label>
                <select
                    className="design-select"
                    value={selectedDesign?.id || ''}
                    onChange={handleDesignChange}
                    disabled={loading || designs.length === 0}
                >
                    {designs.length === 0 ? (
                        <option value="">No designs found</option>
                    ) : (
                        designs.map(d => (
                            <option key={d.id} value={d.id}>
                                {d.code}
                            </option>
                        ))
                    )}
                </select>
            </div>

            <div className="toolbar-spacer"></div>

            <button className="btn">New</button>
            <button className="btn btn-primary" disabled={!selectedDesign}>
                Save
            </button>
        </div>
    );
}

export default ModelSelector;
