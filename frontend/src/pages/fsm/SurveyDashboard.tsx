import React from 'react';
import { useParams, Link } from 'react-router-dom';
import { useProject, useSites, useMonitors } from '../../api/hooks';
import { ArrowLeft, MapPin, Activity, AlertCircle, CheckCircle2, Loader2 } from 'lucide-react';

const MonitorCard = ({ siteId }: { siteId: number }) => {
    const { data: monitors, isLoading } = useMonitors(siteId);

    if (isLoading) return <div className="animate-pulse h-20 bg-gray-100 rounded-lg"></div>;

    return (
        <div className="space-y-3">
            {monitors?.map((monitor) => (
                <div key={monitor.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg border border-gray-100">
                    <div className="flex items-center gap-3">
                        <Activity size={16} className="text-blue-500" />
                        <div>
                            <p className="text-sm font-medium text-gray-900">{monitor.name}</p>
                            <p className="text-xs text-gray-500">{monitor.type}</p>
                        </div>
                    </div>
                    <div className="flex items-center gap-2">
                        {monitor.status === 'Active' ? (
                            <span className="flex items-center gap-1 text-xs font-medium text-green-600 bg-green-50 px-2 py-1 rounded-full">
                                <CheckCircle2 size={12} /> Active
                            </span>
                        ) : (
                            <span className="flex items-center gap-1 text-xs font-medium text-amber-600 bg-amber-50 px-2 py-1 rounded-full">
                                <AlertCircle size={12} /> Issue
                            </span>
                        )}
                        <Link
                            to={`/fsm/monitor/${monitor.id}`}
                            className="text-xs font-medium text-blue-600 hover:underline ml-2"
                        >
                            View
                        </Link>
                    </div>
                </div>
            ))}
            {monitors?.length === 0 && (
                <p className="text-xs text-gray-400 italic">No monitors configured.</p>
            )}
        </div>
    );
};

const SurveyDashboard: React.FC = () => {
    const { projectId } = useParams<{ projectId: string }>();
    const id = parseInt(projectId || '0');

    const { data: project, isLoading: projectLoading } = useProject(id);
    const { data: sites, isLoading: sitesLoading } = useSites(id);

    if (projectLoading || sitesLoading) {
        return (
            <div className="flex justify-center items-center h-64">
                <Loader2 className="animate-spin text-blue-500" size={32} />
            </div>
        );
    }

    if (!project) return <div>Project not found</div>;

    return (
        <div className="max-w-6xl mx-auto">
            <div className="mb-8">
                <Link to="/fsm" className="inline-flex items-center text-sm text-gray-500 hover:text-gray-900 mb-4">
                    <ArrowLeft size={16} className="mr-1" /> Back to Surveys
                </Link>

                <div className="flex justify-between items-start">
                    <div>
                        <div className="flex items-center gap-3 mb-2">
                            <h1 className="text-3xl font-bold text-gray-900">{project.name}</h1>
                            <span className="px-3 py-1 bg-blue-100 text-blue-800 text-sm font-medium rounded-full">
                                {project.job_number}
                            </span>
                        </div>
                        <p className="text-gray-500">{project.client}</p>
                    </div>

                    <div className="flex gap-3">
                        <button className="px-4 py-2 bg-white border border-gray-300 text-gray-700 font-medium rounded-lg hover:bg-gray-50">
                            Edit Project
                        </button>
                        <button className="px-4 py-2 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700">
                            Add Site
                        </button>
                    </div>
                </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                {/* Left Column: Sites & Monitors */}
                <div className="lg:col-span-2 space-y-6">
                    <h2 className="text-xl font-bold text-gray-900">Sites & Monitors</h2>

                    <div className="grid gap-6">
                        {sites?.map((site) => (
                            <div key={site.id} className="bg-white border border-gray-200 rounded-xl p-6 shadow-sm">
                                <div className="flex items-start justify-between mb-4">
                                    <div className="flex items-center gap-3">
                                        <div className="p-2 bg-gray-100 rounded-lg text-gray-600">
                                            <MapPin size={20} />
                                        </div>
                                        <div>
                                            <h3 className="text-lg font-semibold text-gray-900">{site.name}</h3>
                                            <p className="text-sm text-gray-500">{site.catchment}</p>
                                        </div>
                                    </div>
                                    <button className="text-sm text-blue-600 hover:underline">Manage Site</button>
                                </div>

                                <div className="pl-12">
                                    <MonitorCard siteId={site.id} />
                                </div>
                            </div>
                        ))}

                        {sites?.length === 0 && (
                            <div className="text-center py-12 bg-gray-50 rounded-xl border border-dashed border-gray-300">
                                <p className="text-gray-500">No sites added yet.</p>
                            </div>
                        )}
                    </div>
                </div>

                {/* Right Column: Map & Stats */}
                <div className="space-y-6">
                    <div className="bg-white border border-gray-200 rounded-xl p-6 shadow-sm">
                        <h3 className="font-bold text-gray-900 mb-4">Project Stats</h3>
                        <div className="space-y-4">
                            <div className="flex justify-between items-center">
                                <span className="text-gray-500">Total Sites</span>
                                <span className="font-medium">{sites?.length || 0}</span>
                            </div>
                            <div className="flex justify-between items-center">
                                <span className="text-gray-500">Active Monitors</span>
                                <span className="font-medium text-green-600">--</span>
                            </div>
                            <div className="flex justify-between items-center">
                                <span className="text-gray-500">Open Issues</span>
                                <span className="font-medium text-amber-600">--</span>
                            </div>
                        </div>
                    </div>

                    <div className="bg-gray-100 rounded-xl h-64 flex items-center justify-center border border-gray-200">
                        <p className="text-gray-400 font-medium flex items-center gap-2">
                            <MapPin size={20} /> Map View Coming Soon
                        </p>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default SurveyDashboard;
