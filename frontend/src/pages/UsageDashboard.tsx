import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import api from '../api/client';
import { BarChart3, HardDrive, Activity, TrendingUp, Database, Folder } from 'lucide-react';

// Module colors
const MODULE_COLORS: Record<string, string> = {
    'FSM': 'bg-blue-500',
    'FSA': 'bg-purple-500',
    'WQ': 'bg-green-500',
    'VER': 'bg-orange-500',
    'SSD': 'bg-pink-500',
};

const MODULE_BG_COLORS: Record<string, string> = {
    'FSM': 'bg-blue-900/30 border-blue-800 text-blue-400',
    'FSA': 'bg-purple-900/30 border-purple-800 text-purple-400',
    'WQ': 'bg-green-900/30 border-green-800 text-green-400',
    'VER': 'bg-orange-900/30 border-orange-800 text-orange-400',
    'SSD': 'bg-pink-900/30 border-pink-800 text-pink-400',
};

interface UsageData {
    year_month: string;
    total_requests: number;
    total_weighted: number;
    by_module: Array<{
        module: string;
        request_count: number;
        weighted_total: number;
        percentage: number;
    }>;
}

interface StorageData {
    snapshot_date: string | null;
    total_bytes: number;
    total_mb: number;
    projects: Array<{
        project_id: number;
        module: string;
        size_bytes: number;
        size_mb: number;
    }>;
}

const useMyUsage = (yearMonth?: string) => {
    return useQuery({
        queryKey: ['my-usage', yearMonth],
        queryFn: async () => {
            const params = yearMonth ? `?year_month=${yearMonth}` : '';
            const { data } = await api.get<UsageData>(`/users/me/usage${params}`);
            return data;
        },
    });
};

const useMyStorage = () => {
    return useQuery({
        queryKey: ['my-storage'],
        queryFn: async () => {
            const { data } = await api.get<StorageData>('/users/me/storage');
            return data;
        },
    });
};

const UsageDashboard = () => {
    const currentMonth = new Date().toISOString().slice(0, 7);
    const [selectedMonth, setSelectedMonth] = useState(currentMonth);

    const { data: usageData, isLoading: usageLoading } = useMyUsage(selectedMonth);
    const { data: storageData, isLoading: storageLoading } = useMyStorage();

    // Generate last 6 months for dropdown
    const getLastMonths = () => {
        const months = [];
        const now = new Date();
        for (let i = 0; i < 6; i++) {
            const d = new Date(now.getFullYear(), now.getMonth() - i, 1);
            months.push(d.toISOString().slice(0, 7));
        }
        return months;
    };

    return (
        <div className="p-6 max-w-6xl mx-auto">
            <div className="mb-8">
                <h1 className="text-2xl font-bold text-gray-800 mb-2">Usage Dashboard</h1>
                <p className="text-gray-500">View your activity and storage usage</p>
            </div>

            {/* Month Selector */}
            <div className="mb-6">
                <select
                    value={selectedMonth}
                    onChange={(e) => setSelectedMonth(e.target.value)}
                    className="bg-gray-800 border border-gray-700 rounded-lg px-4 py-2 text-white focus:ring-2 focus:ring-blue-500 outline-none"
                >
                    {getLastMonths().map((m) => (
                        <option key={m} value={m}>{m}</option>
                    ))}
                </select>
            </div>

            {/* Stats Cards */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
                <div className="bg-gray-800 rounded-xl border border-gray-700 p-6">
                    <div className="flex items-center gap-3 mb-4">
                        <div className="p-3 bg-blue-900/30 rounded-lg">
                            <Activity className="text-blue-400" size={24} />
                        </div>
                        <div>
                            <p className="text-gray-400 text-sm">Total Requests</p>
                            <p className="text-2xl font-bold text-white">
                                {usageLoading ? '...' : usageData?.total_requests || 0}
                            </p>
                        </div>
                    </div>
                </div>

                <div className="bg-gray-800 rounded-xl border border-gray-700 p-6">
                    <div className="flex items-center gap-3 mb-4">
                        <div className="p-3 bg-purple-900/30 rounded-lg">
                            <TrendingUp className="text-purple-400" size={24} />
                        </div>
                        <div>
                            <p className="text-gray-400 text-sm">Weighted Usage</p>
                            <p className="text-2xl font-bold text-white">
                                {usageLoading ? '...' : usageData?.total_weighted?.toFixed(1) || 0}
                            </p>
                        </div>
                    </div>
                </div>

                <div className="bg-gray-800 rounded-xl border border-gray-700 p-6">
                    <div className="flex items-center gap-3 mb-4">
                        <div className="p-3 bg-green-900/30 rounded-lg">
                            <HardDrive className="text-green-400" size={24} />
                        </div>
                        <div>
                            <p className="text-gray-400 text-sm">Storage Used</p>
                            <p className="text-2xl font-bold text-white">
                                {storageLoading ? '...' : `${storageData?.total_mb || 0} MB`}
                            </p>
                        </div>
                    </div>
                </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Usage by Module */}
                <div className="bg-gray-800 rounded-xl border border-gray-700 p-6">
                    <div className="flex items-center gap-2 mb-6">
                        <BarChart3 className="text-blue-400" size={20} />
                        <h2 className="text-lg font-semibold text-white">Usage by Module</h2>
                    </div>

                    {usageLoading ? (
                        <div className="text-gray-400">Loading...</div>
                    ) : usageData?.by_module && usageData.by_module.length > 0 ? (
                        <div className="space-y-4">
                            {usageData.by_module.map((item) => (
                                <div key={item.module} className="space-y-2">
                                    <div className="flex justify-between text-sm">
                                        <span className={`px-2 py-1 rounded border ${MODULE_BG_COLORS[item.module] || 'bg-gray-900/30 border-gray-700 text-gray-400'}`}>
                                            {item.module}
                                        </span>
                                        <span className="text-gray-400">
                                            {item.request_count} requests ({item.percentage}%)
                                        </span>
                                    </div>
                                    <div className="h-2 bg-gray-900 rounded-full overflow-hidden">
                                        <div
                                            className={`h-full ${MODULE_COLORS[item.module] || 'bg-gray-500'} transition-all duration-500`}
                                            style={{ width: `${item.percentage}%` }}
                                        />
                                    </div>
                                </div>
                            ))}
                        </div>
                    ) : (
                        <div className="text-center py-8 text-gray-500">
                            No usage data for this month
                        </div>
                    )}
                </div>

                {/* Storage by Project */}
                <div className="bg-gray-800 rounded-xl border border-gray-700 p-6">
                    <div className="flex items-center gap-2 mb-6">
                        <Database className="text-green-400" size={20} />
                        <h2 className="text-lg font-semibold text-white">Storage by Project</h2>
                    </div>

                    {storageLoading ? (
                        <div className="text-gray-400">Loading...</div>
                    ) : storageData?.projects && storageData.projects.length > 0 ? (
                        <div className="space-y-3">
                            {storageData.projects.slice(0, 10).map((project) => (
                                <div key={`${project.module}-${project.project_id}`} className="flex items-center justify-between py-2 border-b border-gray-700 last:border-0">
                                    <div className="flex items-center gap-3">
                                        <Folder className="text-gray-500" size={18} />
                                        <div>
                                            <span className={`text-xs px-2 py-0.5 rounded border ${MODULE_BG_COLORS[project.module] || 'bg-gray-900/30 border-gray-700 text-gray-400'}`}>
                                                {project.module}
                                            </span>
                                            <span className="text-gray-400 ml-2">Project #{project.project_id}</span>
                                        </div>
                                    </div>
                                    <span className="text-white font-mono">{project.size_mb} MB</span>
                                </div>
                            ))}
                            {storageData.projects.length > 10 && (
                                <p className="text-gray-500 text-sm text-center pt-2">
                                    + {storageData.projects.length - 10} more projects
                                </p>
                            )}
                        </div>
                    ) : (
                        <div className="text-center py-8 text-gray-500">
                            <HardDrive className="mx-auto mb-2 text-gray-600" size={32} />
                            <p>No storage data available</p>
                            <p className="text-xs mt-1">Storage snapshots are taken periodically</p>
                        </div>
                    )}

                    {storageData?.snapshot_date && (
                        <p className="text-xs text-gray-500 mt-4">
                            Last snapshot: {storageData.snapshot_date}
                        </p>
                    )}
                </div>
            </div>
        </div>
    );
};

export default UsageDashboard;
