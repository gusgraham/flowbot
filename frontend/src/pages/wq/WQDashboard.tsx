import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import axios from 'axios';
import { ArrowLeft, Droplets, Loader2, Pencil, X, Settings, Users, Plus, Upload } from 'lucide-react';
import WQDataImport from './components/WQDataImport';
import WQGraph from './components/WQGraph';

const API_URL = 'http://localhost:8001/api';

const WQDashboard: React.FC = () => {
    const { projectId } = useParams<{ projectId: string }>();
    const id = parseInt(projectId || '0');

    // Fetch Project
    const { data: project, isLoading: loadingProject } = useQuery({
        queryKey: ['wq-project', id],
        queryFn: async () => {
            const res = await axios.get(`${API_URL}/wq/projects/${id}`);
            return res.data;
        }
    });

    // Fetch Monitors
    const { data: monitors, isLoading: loadingMonitors, refetch: refetchMonitors } = useQuery({
        queryKey: ['wq-monitors', id],
        queryFn: async () => {
            const res = await axios.get(`${API_URL}/wq/projects/${id}/monitors`);
            return res.data;
        }
    });

    const [activeMonitorId, setActiveMonitorId] = useState<number | null>(null);
    const [importMode, setImportMode] = useState(false);

    // Auto-select first monitor
    useEffect(() => {
        if (monitors && monitors.length > 0 && !activeMonitorId) {
            setActiveMonitorId(monitors[0].id);
        }
    }, [monitors]);

    if (loadingProject) return <div className="flex justify-center p-8"><Loader2 className="animate-spin" /></div>;
    if (!project) return <div>Project not found</div>;

    return (
        <div className="max-w-7xl mx-auto p-4">
            {/* Header */}
            <div className="mb-6">
                <Link to="/wq" className="inline-flex items-center text-sm text-gray-500 hover:text-gray-900 mb-2">
                    <ArrowLeft size={16} className="mr-1" /> Back to Projects
                </Link>
                <div className="flex justify-between items-center">
                    <div className="flex items-center gap-3">
                        <div className="p-2 bg-cyan-100 text-cyan-700 rounded-lg">
                            <Droplets size={24} />
                        </div>
                        <div>
                            <h1 className="text-2xl font-bold text-gray-900">{project.name}</h1>
                            <p className="text-sm text-gray-500">{project.client} • {project.job_number}</p>
                        </div>
                    </div>

                    <button
                        onClick={() => setImportMode(!importMode)}
                        className={`flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-colors ${importMode
                            ? 'bg-gray-100 text-gray-700'
                            : 'bg-cyan-600 text-white hover:bg-cyan-700'}`}
                    >
                        {importMode ? <X size={18} /> : <Upload size={18} />}
                        {importMode ? "Cancel Import" : "Import Data"}
                    </button>
                </div>
            </div>

            {/* Main Content */}
            {importMode ? (
                <div className="max-w-2xl mx-auto mt-8">
                    <WQDataImport
                        onComplete={() => {
                            setImportMode(false);
                            refetchMonitors();
                        }}
                        onError={(msg) => alert(msg)}
                    />
                </div>
            ) : (
                <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
                    {/* Sidebar List */}
                    <div className="lg:col-span-1 bg-white border border-gray-200 rounded-xl p-4 h-[calc(100vh-200px)] overflow-y-auto">
                        <h3 className="font-bold text-gray-700 mb-3 flex justify-between items-center">
                            Monitors
                            <button onClick={() => setImportMode(true)} className="p-1 hover:bg-gray-100 rounded text-cyan-600">
                                <Plus size={16} />
                            </button>
                        </h3>

                        {loadingMonitors ? (
                            <div className="text-center py-4"><Loader2 className="animate-spin mx-auto" /></div>
                        ) : monitors?.length === 0 ? (
                            <div className="text-center py-8 text-gray-400 text-sm">
                                No monitors found.<br />Import data to get started.
                            </div>
                        ) : (
                            <ul className="space-y-1">
                                {monitors?.map((m: any) => (
                                    <li key={m.id}>
                                        <button
                                            onClick={() => setActiveMonitorId(m.id)}
                                            className={`w-full text-left px-3 py-2 rounded-lg text-sm font-medium transition-colors ${activeMonitorId === m.id
                                                    ? 'bg-cyan-50 text-cyan-700'
                                                    : 'text-gray-600 hover:bg-gray-50'
                                                }`}
                                        >
                                            {m.name}
                                        </button>
                                    </li>
                                ))}
                            </ul>
                        )}
                    </div>

                    {/* Graph Area */}
                    <div className="lg:col-span-3 space-y-4">
                        {activeMonitorId ? (
                            <WQGraph monitorId={activeMonitorId} />
                        ) : (
                            <div className="bg-gray-50 border border-gray-200 border-dashed rounded-xl h-96 flex items-center justify-center text-gray-400">
                                Select a monitor to view data
                            </div>
                        )}
                    </div>
                </div>
            )}
        </div>
    );
};

export default WQDashboard;
