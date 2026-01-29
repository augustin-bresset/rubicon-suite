function MetalsDetail({ productData }) {
    const metals = productData?.metals || [];

    if (metals.length === 0) {
        return (
            <div className="empty-state">
                <p>No metal data available</p>
            </div>
        );
    }

    return (
        <div>
            <table className="data-table">
                <thead>
                    <tr>
                        <th>Metal</th>
                        <th>Purity</th>
                        <th className="number">Weight (g)</th>
                        <th className="number">Cost/g</th>
                        <th className="number">Total Cost</th>
                    </tr>
                </thead>
                <tbody>
                    {metals.map((metal, idx) => (
                        <tr key={idx}>
                            <td>{metal.name}</td>
                            <td>{metal.purity}</td>
                            <td className="number">{metal.weight}</td>
                            <td className="number">{metal.cost_per_gram || '-'}</td>
                            <td className="number">{metal.total_cost || '-'}</td>
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    );
}

export default MetalsDetail;
