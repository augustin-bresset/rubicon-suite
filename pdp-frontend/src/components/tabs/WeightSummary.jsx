function WeightSummary({ productData }) {
    const weights = productData?.weights;

    if (!weights) {
        return (
            <div className="empty-state">
                <p>No weight data available</p>
            </div>
        );
    }

    const stoneOriginal = weights.stone_original || [];
    const stoneRecut = weights.stone_recut || [];
    const metals = weights.metal || [];

    return (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
            {/* Stone Table */}
            <div>
                <h3 style={{ marginBottom: '8px', fontSize: '14px', color: 'var(--text-secondary)' }}>
                    Stone
                </h3>
                {stoneOriginal.length > 0 ? (
                    <table className="data-table">
                        <thead>
                            <tr>
                                <th>Type</th>
                                <th>Shade</th>
                                <th>Shape</th>
                                <th className="number">Pcs</th>
                                <th className="number">Weight (ct)</th>
                            </tr>
                        </thead>
                        <tbody>
                            {stoneOriginal.map((stone, idx) => (
                                <tr key={idx}>
                                    <td>{stone.type}</td>
                                    <td>{stone.shade}</td>
                                    <td>{stone.shape}</td>
                                    <td className="number">{stone.pieces}</td>
                                    <td className="number">{stone.weight}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                ) : (
                    <p style={{ color: 'var(--text-muted)' }}>No stones</p>
                )}
            </div>

            {/* Stone after Recutting */}
            {stoneRecut.length > 0 && (
                <div>
                    <h3 style={{ marginBottom: '8px', fontSize: '14px', color: 'var(--text-secondary)' }}>
                        Stone after Recutting
                    </h3>
                    <table className="data-table">
                        <thead>
                            <tr>
                                <th>Type</th>
                                <th>Shade</th>
                                <th>Shape</th>
                                <th className="number">Pcs</th>
                                <th className="number">Weight (ct)</th>
                            </tr>
                        </thead>
                        <tbody>
                            {stoneRecut.map((stone, idx) => (
                                <tr key={idx}>
                                    <td>{stone.type}</td>
                                    <td>{stone.shade}</td>
                                    <td>{stone.shape}</td>
                                    <td className="number">{stone.pieces}</td>
                                    <td className="number">{stone.weight}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            )}

            {/* Metal Table */}
            <div>
                <h3 style={{ marginBottom: '8px', fontSize: '14px', color: 'var(--text-secondary)' }}>
                    Metal
                </h3>
                {metals.length > 0 ? (
                    <table className="data-table">
                        <thead>
                            <tr>
                                <th>Metal</th>
                                <th>Purity</th>
                                <th className="number">Weight (g)</th>
                            </tr>
                        </thead>
                        <tbody>
                            {metals.map((metal, idx) => (
                                <tr key={idx}>
                                    <td>{metal.name}</td>
                                    <td>{metal.purity}</td>
                                    <td className="number">{metal.weight}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                ) : (
                    <p style={{ color: 'var(--text-muted)' }}>No metals</p>
                )}
            </div>
        </div>
    );
}

export default WeightSummary;
