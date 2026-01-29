function DesignTable({ designs, selectedDesign, onSelect, loading }) {
    if (loading) {
        return (
            <div className="design-table-container">
                <div className="empty-state">
                    <div className="spinner"></div>
                    <p>Loading designs...</p>
                </div>
            </div>
        );
    }

    if (designs.length === 0) {
        return (
            <div className="design-table-container">
                <div className="empty-state">
                    <h2>No Model Selected</h2>
                    <p>Enter a model code and press Enter to search</p>
                </div>
            </div>
        );
    }

    return (
        <div className="design-table-container">
            <table className="design-table">
                <thead>
                    <tr>
                        <th>Design Ref#</th>
                    </tr>
                </thead>
                <tbody>
                    {designs.map(design => (
                        <tr
                            key={design.id}
                            className={selectedDesign?.id === design.id ? 'active' : ''}
                            onClick={() => onSelect(design)}
                            style={{ cursor: 'pointer' }}
                        >
                            <td>{design.code}</td>
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    );
}

export default DesignTable;
