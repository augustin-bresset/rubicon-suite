import { useState } from 'react';
import CostingSummary from './tabs/CostingSummary';
import WeightSummary from './tabs/WeightSummary';
import StonesDetail from './tabs/StonesDetail';
import MetalsDetail from './tabs/MetalsDetail';
import LaborDetail from './tabs/LaborDetail';

const TABS = [
    { id: 'costing', label: 'Costing Summary', component: CostingSummary },
    { id: 'weight', label: 'Weight Summary', component: WeightSummary },
    { id: 'stones', label: 'Stones', component: StonesDetail },
    { id: 'metals', label: 'Metals', component: MetalsDetail },
    { id: 'labor', label: 'Labor etc.', component: LaborDetail },
];

function DetailTabs({ productData, metadata, loading }) {
    const [activeTab, setActiveTab] = useState('costing');

    const ActiveComponent = TABS.find(t => t.id === activeTab)?.component;

    if (!productData && !loading) {
        return (
            <div className="detail-tabs-container">
                <div className="detail-tabs-header">
                    {TABS.map(tab => (
                        <button
                            key={tab.id}
                            className={`detail-tab ${activeTab === tab.id ? 'active' : ''}`}
                            onClick={() => setActiveTab(tab.id)}
                        >
                            {tab.label}
                        </button>
                    ))}
                </div>
                <div className="detail-tabs-content">
                    <div className="empty-state">
                        <h2>Select a Design</h2>
                        <p>Choose a model and design to view details</p>
                    </div>
                </div>
            </div>
        );
    }

    return (
        <div className="detail-tabs-container">
            <div className="detail-tabs-header">
                {TABS.map(tab => (
                    <button
                        key={tab.id}
                        className={`detail-tab ${activeTab === tab.id ? 'active' : ''}`}
                        onClick={() => setActiveTab(tab.id)}
                    >
                        {tab.label}
                    </button>
                ))}
            </div>
            <div className="detail-tabs-content">
                {loading ? (
                    <div className="empty-state">
                        <div className="spinner"></div>
                        <p>Loading...</p>
                    </div>
                ) : (
                    ActiveComponent && (
                        <ActiveComponent
                            productData={productData}
                            metadata={metadata}
                        />
                    )
                )}
            </div>
        </div>
    );
}

export default DetailTabs;
