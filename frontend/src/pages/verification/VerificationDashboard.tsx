import React, { useState } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { useProject, useSites, useMonitors } from '../../api/hooks';
import { ArrowLeft, Upload, BarChart2, Loader2, Pencil } from 'lucide-react';

const VerificationDashboard: React.FC = () => {
    const { projectId } = useParams<{ projectId: string }>();
    const navigate = useNavigate();
    const id = parseInt(projectId || '0');

    const { data: project } = useProject(id);
    const { data: sites } = useSites(id);

    const [selectedSiteId, setSelectedSiteId] = useState<number | null>(null);
    const [selectedMonitorId, setSelectedMonitorId] = useState<number | null>(null);

    const { data: monitors } = useMonitors(selectedSiteId || 0);

    React.useEffect(() => {
        if (sites && sites.length > 0 && !selectedSiteId) {
            setSelectedSiteId(sites[0].id);
        }
    }, [sites]);

    React.useEffect(() => {
        if (monitors && monitors.length > 0 && !selectedMonitorId) {
            setSelectedMonitorId(monitors[0].id);
        }
    }, [monitors]);

    if (!project) return <div className="p-8"><Loader2 className="animate-spin" /></div>;

    return (
        <div className="h-[calc(100vh-8rem)] flex flex-col">
            <div className="mb-6">
                <Link to="/verification" className="inline-flex items-center text-sm text-gray-500 hover:text-gray-900 mb-2">
                    <ArrowLeft size={16} className="mr-1" /> Back to Projects
                </Link>
                <div className="flex items-center justify-between">
                    <h1 className="text-2xl font-bold text-gray-900">{project.name} - Verification</h1>
                    <button
                        onClick={() => navigate('/verification', { state: { editProjectId: id } })}
                        className="flex items-center gap-2 px-3 py-1.5 text-sm text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors"
                    >
                        <Pencil size={16} />
                        Edit Project
                    </button>
                </div>
            </div>

            <div className="flex-1 flex gap-6 overflow-hidden">
                {/* Sidebar */}
                <div className="w-64 bg-white border border-gray-200 rounded-xl p-4 flex flex-col gap-4 overflow-y-auto">
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">Site</label>
                        <select
                            className="w-full border-gray-300 rounded-md shadow-sm focus:ring-green-500 focus:border-green-500"
                            value={selectedSiteId || ''}
                            onChange={(e) => {
                                setSelectedSiteId(Number(e.target.value));
                                setSelectedMonitorId(null);
                            }}
                        >
                            {sites?.map(site => (
                                <option key={site.id} value={site.id}>{site.name}</option>
                            ))}
                        </select>
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">Monitor</label>
                        <select
                            className="w-full border-gray-300 rounded-md shadow-sm focus:ring-green-500 focus:border-green-500"
                            value={selectedMonitorId || ''}
                            onChange={(e) => setSelectedMonitorId(Number(e.target.value))}
                            disabled={!selectedSiteId}
                        >
                            {monitors?.map(monitor => (
                                <option key={monitor.id} value={monitor.id}>{monitor.monitor_asset_id}</option>
                            ))}
                        </select>
                    </div>
                </div>

                {/* Main Content */}
                <div className="flex-1 bg-white border border-gray-200 rounded-xl p-6 overflow-y-auto">
                    {selectedMonitorId ? (
                        <div className="space-y-8">
                            <div className="flex justify-between items-center">
                                <h2 className="text-xl font-bold text-gray-900">Model Comparison</h2>
                                <button className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700">
                                    <Upload size={18} /> Upload Model Results
                                </button>
                            </div>

                            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                                <div className="lg:col-span-2 bg-gray-50 rounded-lg border border-dashed border-gray-300 h-96 flex items-center justify-center">
                                    <p className="text-gray-500">Comparison Chart Placeholder</p>
                                </div>

                                <div className="space-y-4">
                                    <div className="bg-white border border-gray-200 rounded-lg p-4 shadow-sm">
                                        <h3 className="font-semibold text-gray-900 mb-3 flex items-center gap-2">
                                            <BarChart2 size={18} /> Goodness of Fit
                                        </h3>
                                        <div className="space-y-3 text-sm">
                                            <div className="flex justify-between">
                                                <span className="text-gray-500">NSE</span>
                                                <span className="font-mono font-medium">--</span>
                                            </div>
                                            <div className="flex justify-between">
                                                <span className="text-gray-500">R²</span>
                                                <span className="font-mono font-medium">--</span>
                                            </div>
                                            <div className="flex justify-between">
                                                <span className="text-gray-500">Peak Error</span>
                                                <span className="font-mono font-medium">--</span>
                                            </div>
                                            <div className="flex justify-between">
                                                <span className="text-gray-500">Vol Error</span>
                                                <span className="font-mono font-medium">--</span>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    ) : (
                        <div className="flex items-center justify-center h-full text-gray-500">
                            Select a monitor to verify.
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

export default VerificationDashboard;
