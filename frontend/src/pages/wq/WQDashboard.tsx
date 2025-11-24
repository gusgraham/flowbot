import React, { useState } from 'react';
import { useSites, useMonitors, useWQData, useWQCorrelation } from '../../api/hooks';
import { Droplets, Activity, Loader2 } from 'lucide-react';

const WQDashboard: React.FC = () => {
    // For WQ, we might not have a project context passed in URL if it's a general dashboard.
    // But usually we'd select a project first. 
    // For this demo, let's assume we pick a project from a dropdown or just list all sites if possible.
    // To keep it simple and consistent, let's just show a "Select Monitor" interface similar to Workbench
    // but maybe without the project context wrapper for now, or we hardcode a project ID for demo.
    // Actually, let's just fetch all projects or let user select.
    // I'll implement a simple selector for Project -> Site -> Monitor.

    // Wait, I don't have a "get all sites" endpoint, only "get sites for project".
    // So I need to select a project first.
    // I'll reuse the "Project List" pattern or just hardcode for now to save time?
    // No, let's do it properly. I'll make a WQProjectList page?
    // Or just make WQDashboard handle project selection if no ID is present?
    // Let's make WQDashboard require a monitor selection flow.

    // I'll implement a simplified view where we just select from the first available project for demo purposes
    // or add a project selector.

    // Let's add a project selector state.
    const [selectedProjectId, setSelectedProjectId] = useState<number | null>(null);
    const [selectedSiteId, setSelectedSiteId] = useState<number | null>(null);
    const [selectedMonitorId, setSelectedMonitorId] = useState<number | null>(null);

    // We need a hook to get all projects
    // We have useProjects()
    const { data: projects } = React.useMemo(() => ({ data: [] as any[] }), []); // Placeholder to avoid hook rules issue if I call it conditionally? 
    // No, hooks must be top level.
    // I'll import useProjects.

    return (
        <div className="p-8">
            <h1 className="text-2xl font-bold text-gray-900 mb-6">Water Quality Dashboard</h1>
            <div className="bg-yellow-50 border border-yellow-200 p-4 rounded-lg text-yellow-800">
                Work in progress. Please select a monitor to view WQ data.
            </div>
        </div>
    );
};

// Re-implementing properly
import { useProjects } from '../../api/hooks';

const WQDashboardReal: React.FC = () => {
    const { data: projects } = useProjects();
    const [selectedProjectId, setSelectedProjectId] = useState<number | null>(null);
    const [selectedSiteId, setSelectedSiteId] = useState<number | null>(null);
    const [selectedMonitorId, setSelectedMonitorId] = useState<number | null>(null);

    const { data: sites } = useSites(selectedProjectId || 0);
    const { data: monitors } = useMonitors(selectedSiteId || 0);

    const { data: wqData, isLoading: wqLoading } = useWQData(selectedMonitorId || 0);
    const { data: correlation, isLoading: corrLoading } = useWQCorrelation(selectedMonitorId || 0);

    return (
        <div className="h-[calc(100vh-8rem)] flex flex-col">
            <div className="mb-6">
                <h1 className="text-2xl font-bold text-gray-900">Water Quality Analysis</h1>
                <p className="text-gray-500">Analyze chemical and physical parameters.</p>
            </div>

            <div className="flex-1 flex gap-6 overflow-hidden">
                {/* Sidebar: Selection */}
                <div className="w-64 bg-white border border-gray-200 rounded-xl p-4 flex flex-col gap-4 overflow-y-auto">
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">Project</label>
                        <select
                            className="w-full border-gray-300 rounded-md shadow-sm focus:ring-cyan-500 focus:border-cyan-500"
                            value={selectedProjectId || ''}
                            onChange={(e) => {
                                setSelectedProjectId(Number(e.target.value));
                                setSelectedSiteId(null);
                                setSelectedMonitorId(null);
                            }}
                        >
                            <option value="">Select Project...</option>
                            {projects?.map(p => (
                                <option key={p.id} value={p.id}>{p.name}</option>
                            ))}
                        </select>
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">Site</label>
                        <select
                            className="w-full border-gray-300 rounded-md shadow-sm focus:ring-cyan-500 focus:border-cyan-500"
                            value={selectedSiteId || ''}
                            onChange={(e) => {
                                setSelectedSiteId(Number(e.target.value));
                                setSelectedMonitorId(null);
                            }}
                            disabled={!selectedProjectId}
                        >
                            <option value="">Select Site...</option>
                            {sites?.map(site => (
                                <option key={site.id} value={site.id}>{site.name}</option>
                            ))}
                        </select>
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">Monitor</label>
                        <select
                            className="w-full border-gray-300 rounded-md shadow-sm focus:ring-cyan-500 focus:border-cyan-500"
                            value={selectedMonitorId || ''}
                            onChange={(e) => setSelectedMonitorId(Number(e.target.value))}
                            disabled={!selectedSiteId}
                        >
                            <option value="">Select Monitor...</option>
                            {monitors?.map(monitor => (
                                <option key={monitor.id} value={monitor.id}>{monitor.name}</option>
                            ))}
                        </select>
                    </div>
                </div>

                {/* Main Content */}
                <div className="flex-1 bg-white border border-gray-200 rounded-xl p-6 overflow-y-auto">
                    {selectedMonitorId ? (
                        <div className="space-y-8">
                            {/* Time Series */}
                            <div>
                                <h2 className="text-lg font-bold text-gray-900 mb-4 flex items-center gap-2">
                                    <Droplets size={20} className="text-cyan-600" />
                                    Time Series Data
                                </h2>
                                {wqLoading ? (
                                    <div className="h-64 flex items-center justify-center"><Loader2 className="animate-spin" /></div>
                                ) : (
                                    <div className="grid gap-4">
                                        {wqData?.map((series) => (
                                            <div key={series.variable} className="bg-gray-50 p-4 rounded-lg border border-gray-100">
                                                <h3 className="font-medium text-gray-900 mb-2">{series.variable}</h3>
                                                <div className="h-32 bg-white border border-dashed border-gray-300 flex items-center justify-center text-sm text-gray-400">
                                                    Chart: {series.data.length} points
                                                </div>
                                            </div>
                                        ))}
                                        {wqData?.length === 0 && <p className="text-gray-500">No WQ data found.</p>}
                                    </div>
                                )}
                            </div>

                            {/* Correlation */}
                            <div>
                                <h2 className="text-lg font-bold text-gray-900 mb-4 flex items-center gap-2">
                                    <Activity size={20} className="text-cyan-600" />
                                    Flow Correlation
                                </h2>
                                {corrLoading ? (
                                    <div className="h-64 flex items-center justify-center"><Loader2 className="animate-spin" /></div>
                                ) : (
                                    <div className="grid gap-4">
                                        {correlation?.correlations && Object.entries(correlation.correlations).map(([variable, points]) => (
                                            <div key={variable} className="bg-gray-50 p-4 rounded-lg border border-gray-100">
                                                <h3 className="font-medium text-gray-900 mb-2">{variable} vs Flow</h3>
                                                <div className="h-48 bg-white border border-dashed border-gray-300 flex items-center justify-center text-sm text-gray-400">
                                                    Scatter Plot: {points.length} points
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                )}
                            </div>
                        </div>
                    ) : (
                        <div className="flex items-center justify-center h-full text-gray-500">
                            Select a monitor to view water quality data.
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

export default WQDashboardReal;
