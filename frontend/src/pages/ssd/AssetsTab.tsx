import React, { useState } from 'react';
import { Container, MapPin, Building } from 'lucide-react';
import CSOAssetsTab from './CSOAssetsTab';

type AssetTabId = 'cso' | 'catchments' | 'wwtw';

interface AssetsTabProps {
    projectId: number;
}

const assetTabs: { id: AssetTabId; label: string; icon: React.ElementType }[] = [
    { id: 'cso', label: 'CSO Assets', icon: Container },
    { id: 'catchments', label: 'Catchments', icon: MapPin },
    { id: 'wwtw', label: 'WwTW Assets', icon: Building },
];

const AssetsTab: React.FC<AssetsTabProps> = ({ projectId }) => {
    const [activeSubTab, setActiveSubTab] = useState<AssetTabId>('cso');

    return (
        <div className="p-6">
            <h2 className="text-xl font-bold text-gray-900 mb-2">Asset Management</h2>
            <p className="text-gray-500 mb-6">
                Define and manage CSO, catchment, and WwTW assets for your project.
            </p>

            {/* Sub-tabs */}
            <div className="border-b border-gray-200 mb-6">
                <nav className="-mb-px flex gap-6">
                    {assetTabs.map((tab) => {
                        const Icon = tab.icon;
                        const isActive = activeSubTab === tab.id;
                        return (
                            <button
                                key={tab.id}
                                onClick={() => setActiveSubTab(tab.id)}
                                className={`flex items-center gap-2 py-3 px-1 border-b-2 text-sm font-medium transition-colors ${isActive
                                        ? 'border-orange-500 text-orange-600'
                                        : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                                    }`}
                            >
                                <Icon size={16} />
                                {tab.label}
                            </button>
                        );
                    })}
                </nav>
            </div>

            {/* Sub-tab Content */}
            {activeSubTab === 'cso' && (
                <div>
                    <p className="text-gray-600 mb-4">
                        Define Combined Sewer Overflow (CSO) configurations and link mappings.
                    </p>
                    <CSOAssetsTab projectId={projectId} />
                </div>
            )}

            {activeSubTab === 'catchments' && (
                <div className="text-center py-16 text-gray-400">
                    <MapPin size={48} className="mx-auto mb-4 opacity-50" />
                    <p className="text-lg">Coming Soon</p>
                    <p className="text-sm mt-2">Catchment management will be available in a future update.</p>
                </div>
            )}

            {activeSubTab === 'wwtw' && (
                <div className="text-center py-16 text-gray-400">
                    <Building size={48} className="mx-auto mb-4 opacity-50" />
                    <p className="text-lg">Coming Soon</p>
                    <p className="text-sm mt-2">WwTW asset management will be available in a future update.</p>
                </div>
            )}
        </div>
    );
};

export default AssetsTab;
