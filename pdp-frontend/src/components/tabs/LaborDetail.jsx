function LaborDetail({ productData }) {
    const labor = productData?.labor || [];
    const parts = productData?.parts || [];
    const addons = productData?.addons || [];

    return (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
            {/* Labor Table */}
            <div>
                <h3 style={{ marginBottom: '8px', fontSize: '14px', color: 'var(--text-secondary)' }}>
                    Labor (Model Level)
                </h3>
                {labor.length > 0 ? (
                    <table className="data-table">
                        <thead>
                            <tr>
                                <th>Type</th>
                                <th className="number">Cost</th>
                            </tr>
                        </thead>
                        <tbody>
                            {labor.map((item, idx) => (
                                <tr key={idx}>
                                    <td>{item.name || item.type}</td>
                                    <td className="number">{item.cost || '-'}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                ) : (
                    <p style={{ color: 'var(--text-muted)' }}>No labor costs</p>
                )}
            </div>

            {/* Parts Table */}
            <div>
                <h3 style={{ marginBottom: '8px', fontSize: '14px', color: 'var(--text-secondary)' }}>
                    Parts
                </h3>
                {parts.length > 0 ? (
                    <table className="data-table">
                        <thead>
                            <tr>
                                <th>Part Name</th>
                                <th className="number">Qty</th>
                                <th className="number">Cost</th>
                            </tr>
                        </thead>
                        <tbody>
                            {parts.map((part, idx) => (
                                <tr key={idx}>
                                    <td>{part.name}</td>
                                    <td className="number">{part.quantity || 1}</td>
                                    <td className="number">{part.cost || '-'}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                ) : (
                    <p style={{ color: 'var(--text-muted)' }}>No parts</p>
                )}
            </div>

            {/* Addons (Misc) Table */}
            <div>
                <h3 style={{ marginBottom: '8px', fontSize: '14px', color: 'var(--text-secondary)' }}>
                    Addon (Laser, Paint, etc.)
                </h3>
                {addons.length > 0 ? (
                    <table className="data-table">
                        <thead>
                            <tr>
                                <th>Type</th>
                                <th className="number">Cost</th>
                            </tr>
                        </thead>
                        <tbody>
                            {addons.map((addon, idx) => (
                                <tr key={idx}>
                                    <td>{addon.name || addon.type}</td>
                                    <td className="number">{addon.cost || '-'}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                ) : (
                    <p style={{ color: 'var(--text-muted)' }}>No addons</p>
                )}
            </div>
        </div>
    );
}

export default LaborDetail;
