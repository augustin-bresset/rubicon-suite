import { useState, useEffect } from 'react';
import { pdpApi } from '../../api/pdpClient';

function CostingSummary({ productData, metadata }) {
    const [currencyId, setCurrencyId] = useState(null);
    const [marginId, setMarginId] = useState(null);
    const [purity, setPurity] = useState('18K');
    const [priceData, setPriceData] = useState(null);
    const [loading, setLoading] = useState(false);
    const [warnings, setWarnings] = useState([]);

    // Auto-compute on mount or when params change
    useEffect(() => {
        if (!productData?.product?.id) return;

        const cid = currencyId || metadata?.currencies?.[0]?.id;
        const mid = marginId || metadata?.margins?.[0]?.id;

        if (!cid || !mid) return;

        setLoading(true);
        pdpApi.computePrice(productData.product.id, mid, cid)
            .then(data => {
                setPriceData(data);
                setWarnings(data.warnings || []);
            })
            .catch(err => console.error('Price compute error:', err))
            .finally(() => setLoading(false));
    }, [productData?.product?.id, currencyId, marginId, metadata]);

    const formatCurrency = (value, currency) => {
        if (value === undefined || value === null) return '-';
        const symbol = currency?.symbol || priceData?.currency?.symbol || '$';
        return `${symbol} ${parseFloat(value).toFixed(2)}`;
    };

    const costing = priceData || productData?.costing;
    const currency = priceData?.currency || productData?.costing?.currency;

    return (
        <div>
            {/* Warning Banner */}
            {warnings.length > 0 && (
                <div className="warning-banner">
                    {warnings.join(' | ')}
                </div>
            )}

            {/* Price Controls */}
            <div className="price-controls">
                <div className="price-control-group">
                    <label>Margin</label>
                    <select
                        value={marginId || ''}
                        onChange={(e) => setMarginId(e.target.value ? parseInt(e.target.value) : null)}
                    >
                        <option value="">Select...</option>
                        {metadata?.margins?.map(m => (
                            <option key={m.id} value={m.id}>{m.name}</option>
                        ))}
                    </select>
                </div>

                <div className="price-control-group">
                    <label>Purity</label>
                    <select value={purity} onChange={(e) => setPurity(e.target.value)}>
                        <option value="18K">18K</option>
                        <option value="14K">14K</option>
                        <option value="9K">9K</option>
                    </select>
                </div>

                <div className="price-control-group">
                    <label>Metal Conv.</label>
                    <select defaultValue="W">
                        <option value="W">White Gold 18K</option>
                        <option value="Y">Yellow Gold 18K</option>
                        <option value="P">Platinum</option>
                    </select>
                </div>

                <div className="price-control-group">
                    <label>Currency</label>
                    <select
                        value={currencyId || ''}
                        onChange={(e) => setCurrencyId(e.target.value ? parseInt(e.target.value) : null)}
                    >
                        <option value="">Select...</option>
                        {metadata?.currencies?.map(c => (
                            <option key={c.id} value={c.id}>{c.symbol} - {c.name}</option>
                        ))}
                    </select>
                </div>

                <div className="price-control-group">
                    <label>US$ Rate</label>
                    <input
                        type="text"
                        value={currency?.rate || '1.00'}
                        readOnly
                        style={{ width: '80px' }}
                    />
                </div>
            </div>

            {/* Costing Table */}
            {loading ? (
                <div className="empty-state">
                    <div className="spinner"></div>
                    <p>Computing prices...</p>
                </div>
            ) : costing?.lines ? (
                <table className="data-table">
                    <thead>
                        <tr>
                            <th>Component</th>
                            <th className="number">Cost</th>
                            <th className="number">Margin</th>
                            <th className="number">Price</th>
                        </tr>
                    </thead>
                    <tbody>
                        {costing.lines.map((line, idx) => (
                            <tr key={idx}>
                                <td>{line.label || line.type}</td>
                                <td className="number">{formatCurrency(line.cost, currency)}</td>
                                <td className="number">{formatCurrency(line.margin, currency)}</td>
                                <td className="number">{formatCurrency(line.price, currency)}</td>
                            </tr>
                        ))}
                    </tbody>
                    <tfoot>
                        <tr className="total-row">
                            <td><strong>TOTAL</strong></td>
                            <td className="number">
                                <strong>{formatCurrency(costing.totals?.cost, currency)}</strong>
                            </td>
                            <td className="number">
                                <strong>{formatCurrency(costing.totals?.margin, currency)}</strong>
                            </td>
                            <td className="number">
                                <strong>{formatCurrency(costing.totals?.price, currency)}</strong>
                            </td>
                        </tr>
                    </tfoot>
                </table>
            ) : (
                <div className="empty-state">
                    <p>No pricing data available</p>
                </div>
            )}
        </div>
    );
}

export default CostingSummary;
