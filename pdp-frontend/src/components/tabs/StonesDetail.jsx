function StonesDetail({ productData }) {
    const stones = productData?.stones || [];

    if (stones.length === 0) {
        return (
            <div className="empty-state">
                <p>No stone data available</p>
            </div>
        );
    }

    return (
        <div>
            <table className="data-table">
                <thead>
                    <tr>
                        <th>LineNum</th>
                        <th>Type</th>
                        <th>Shape</th>
                        <th>Shade</th>
                        <th>Size</th>
                        <th className="number">Pcs</th>
                        <th className="number">Weight</th>
                        <th>Setting</th>
                        <th>RecShape</th>
                        <th>RecSize</th>
                        <th className="number">RecWgt</th>
                    </tr>
                </thead>
                <tbody>
                    {stones.map((stone, idx) => (
                        <tr key={idx}>
                            <td>{stone.line_num || idx + 1}</td>
                            <td>{stone.type}</td>
                            <td>{stone.shape}</td>
                            <td>{stone.shade}</td>
                            <td>{stone.size}</td>
                            <td className="number">{stone.pieces}</td>
                            <td className="number">{stone.weight}</td>
                            <td>{stone.setting || '-'}</td>
                            <td>{stone.rec_shape || '-'}</td>
                            <td>{stone.rec_size || '-'}</td>
                            <td className="number">{stone.rec_weight || '-'}</td>
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    );
}

export default StonesDetail;
