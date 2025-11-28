import React, { useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useProject, useSites, useProjectMonitors, useProjectInstalls } from '../../api/hooks';
import type { Site, Monitor } from '../../api/hooks';
import {
    ArrowLeft, MapPin, Loader2, Plus, Building2, CloudRain,
    ChevronDown, ChevronRight, Activity, Droplets
} from 'lucide-react';
import AddSiteModal from './AddSiteModal';
import EditProjectModal from './EditProjectModal';
import AddMonitorModal from './AddMonitorModal';
import ManageSiteModal from './ManageSiteModal';
import ManageMonitorModal from './ManageMonitorModal';
import AddInstallModal from './AddInstallModal';

const SurveyDashboard: React.FC = () => {
    const { projectId } = useParams<{ projectId: string }>();
    const id = parseInt(projectId || '0');

    const { data: project, isLoading: projectLoading } = useProject(id);
    const { data: sites, isLoading: sitesLoading } = useSites(id);
    const { data: monitors } = useProjectMonitors(id);
    const { data: installs } = useProjectInstalls(id);

    const [isAddSiteModalOpen, setIsAddSiteModalOpen] = useState(false);
    const [isEditProjectModalOpen, setIsEditProjectModalOpen] = useState(false);
    const [isAddMonitorModalOpen, setIsAddMonitorModalOpen] = useState(false);
    const [isAddInstallModalOpen, setIsAddInstallModalOpen] = useState(false);
    const [managingSite, setManagingSite] = useState<Site | null>(null);
    const [managingMonitor, setManagingMonitor] = useState<Monitor | null>(null);

    // Section Collapse State
    const [isMonitorsOpen, setIsMonitorsOpen] = useState(true);
    const [isSitesOpen, setIsSitesOpen] = useState(true);
    const [isInstallsOpen, setIsInstallsOpen] = useState(true);

    // Group sites by type
    const networkAssets = sites?.filter(s => s.site_type === 'Flow Monitor' || s.site_type === 'Pump Station') || [];
    const locations = sites?.filter(s => s.site_type === 'Rain Gauge') || [];

    // Group monitors by type
    const flowMonitors = monitors?.filter(m => m.monitor_type === 'Flow Monitor') || [];
    const rainGauges = monitors?.filter(m => m.monitor_type === 'Raingauge') || [];
    const otherMonitors = monitors?.filter(m => m.monitor_type !== 'Flow Monitor' && m.monitor_type !== 'Raingauge') || [];

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
                            <h1 className="text-3xl font-bold text-gray-900">
                                {(project as any).job_name || project.name}
                            </h1>
                            <span className="px-3 py-1 bg-blue-100 text-blue-800 text-sm font-medium rounded-full">
                                {project.job_number}
                            </span>
                        </div>
                        <p className="text-gray-500">{project.client}</p>
                    </div>

                    <button
                        onClick={() => setIsEditProjectModalOpen(true)}
                        className="px-4 py-2 bg-white border border-gray-300 text-gray-700 font-medium rounded-lg hover:bg-gray-50"
                    >
                        Edit Project
                    </button>
                </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                {/* Left Column: Project Overview */}
                <div className="lg:col-span-2 space-y-6">

                    {/* Project Monitors */}
                    <div className="bg-white border border-gray-200 rounded-xl shadow-sm overflow-hidden">
                        <div
                            className="p-6 flex justify-between items-center cursor-pointer hover:bg-gray-50 transition-colors"
                            onClick={() => setIsMonitorsOpen(!isMonitorsOpen)}
                        >
                            <div className="flex items-center gap-2">
                                {isMonitorsOpen ? <ChevronDown size={20} className="text-gray-400" /> : <ChevronRight size={20} className="text-gray-400" />}
                                <h2 className="text-xl font-bold text-gray-900">Project Monitors</h2>
                            </div>
                            <button
                                onClick={(e) => {
                                    e.stopPropagation();
                                    setIsAddMonitorModalOpen(true);
                                }}
                                className="flex items-center gap-1 text-sm bg-blue-600 text-white px-3 py-1.5 rounded-lg hover:bg-blue-700"
                            >
                                <Plus size={16} />
                                Add Monitor
                            </button>
                        </div>

                        {isMonitorsOpen && (
                            <div className="px-6 pb-6 space-y-6 border-t border-gray-100 pt-4">
                                {/* Flow Monitors */}
                                {flowMonitors.length > 0 && (
                                    <div>
                                        <div className="flex items-center gap-2 mb-3">
                                            <Activity size={18} className="text-blue-600" />
                                            <h3 className="text-lg font-semibold text-gray-900">Flow Monitors</h3>
                                            <span className="text-sm text-gray-500">({flowMonitors.length})</span>
                                        </div>
                                        <div className="grid grid-cols-2 gap-3 pl-6">
                                            {flowMonitors.map((monitor) => (
                                                <div key={monitor.id} className="border border-gray-200 rounded-lg p-3 flex justify-between items-start bg-blue-50/30">
                                                    <div>
                                                        <p className="font-medium text-gray-900">{monitor.monitor_asset_id}</p>
                                                        <p className="text-sm text-gray-500">{monitor.monitor_type}</p>
                                                        <p className="text-xs text-gray-400">{monitor.monitor_sub_type}</p>
                                                    </div>
                                                    <button
                                                        onClick={() => setManagingMonitor(monitor)}
                                                        className="text-sm text-blue-600 hover:underline"
                                                    >
                                                        Manage
                                                    </button>
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                )}

                                {/* Rain Gauges */}
                                {rainGauges.length > 0 && (
                                    <div>
                                        <div className="flex items-center gap-2 mb-3">
                                            <Droplets size={18} className="text-cyan-600" />
                                            <h3 className="text-lg font-semibold text-gray-900">Rain Gauges</h3>
                                            <span className="text-sm text-gray-500">({rainGauges.length})</span>
                                        </div>
                                        <div className="grid grid-cols-2 gap-3 pl-6">
                                            {rainGauges.map((monitor) => (
                                                <div key={monitor.id} className="border border-gray-200 rounded-lg p-3 flex justify-between items-start bg-cyan-50/30">
                                                    <div>
                                                        <p className="font-medium text-gray-900">{monitor.monitor_asset_id}</p>
                                                        <p className="text-sm text-gray-500">{monitor.monitor_type}</p>
                                                    </div>
                                                    <button
                                                        onClick={() => setManagingMonitor(monitor)}
                                                        className="text-sm text-blue-600 hover:underline"
                                                    >
                                                        Manage
                                                    </button>
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                )}

                                {/* Other Monitors */}
                                {otherMonitors.length > 0 && (
                                    <div>
                                        <div className="flex items-center gap-2 mb-3">
                                            <h3 className="text-lg font-semibold text-gray-900">Other Monitors</h3>
                                            <span className="text-sm text-gray-500">({otherMonitors.length})</span>
                                        </div>
                                        <div className="grid grid-cols-2 gap-3 pl-6">
                                            {otherMonitors.map((monitor) => (
                                                <div key={monitor.id} className="border border-gray-200 rounded-lg p-3 flex justify-between items-start">
                                                    <div>
                                                        <p className="font-medium text-gray-900">{monitor.monitor_asset_id}</p>
                                                        <p className="text-sm text-gray-500">{monitor.monitor_type}</p>
                                                    </div>
                                                    <button
                                                        onClick={() => setManagingMonitor(monitor)}
                                                        className="text-sm text-blue-600 hover:underline"
                                                    >
                                                        Manage
                                                    </button>
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                )}

                                {monitors?.length === 0 && (
                                    <p className="text-sm text-gray-400 italic text-center py-4">No monitors added yet</p>
                                )}
                            </div>
                        )}
                    </div>

                    {/* Project Sites */}
                    <div className="bg-white border border-gray-200 rounded-xl shadow-sm overflow-hidden">
                        <div
                            className="p-6 flex justify-between items-center cursor-pointer hover:bg-gray-50 transition-colors"
                            onClick={() => setIsSitesOpen(!isSitesOpen)}
                        >
                            <div className="flex items-center gap-2">
                                {isSitesOpen ? <ChevronDown size={20} className="text-gray-400" /> : <ChevronRight size={20} className="text-gray-400" />}
                                <h2 className="text-xl font-bold text-gray-900">Project Sites</h2>
                            </div>
                            <button
                                onClick={(e) => {
                                    e.stopPropagation();
                                    setIsAddSiteModalOpen(true);
                                }}
                                className="flex items-center gap-1 text-sm bg-blue-600 text-white px-3 py-1.5 rounded-lg hover:bg-blue-700"
                            >
                                <Plus size={16} />
                                Add Site
                            </button>
                        </div>

                        {isSitesOpen && (
                            <div className="px-6 pb-6 space-y-6 border-t border-gray-100 pt-4">
                                {/* Network Assets */}
                                {networkAssets.length > 0 && (
                                    <div>
                                        <div className="flex items-center gap-2 mb-3">
                                            <Building2 size={18} className="text-blue-600" />
                                            <h3 className="text-lg font-semibold text-gray-900">Network Assets</h3>
                                            <span className="text-sm text-gray-500">({networkAssets.length})</span>
                                        </div>
                                        <div className="space-y-2 pl-6">
                                            {networkAssets.map((site) => (
                                                <div key={site.id} className="border border-gray-200 rounded-lg p-3 flex justify-between items-center bg-blue-50/30">
                                                    <div>
                                                        <p className="font-medium text-gray-900">{site.site_id}</p>
                                                        <p className="text-sm text-gray-500">{site.site_type}</p>
                                                    </div>
                                                    <button
                                                        onClick={() => setManagingSite(site)}
                                                        className="text-sm text-blue-600 hover:underline"
                                                    >
                                                        Manage
                                                    </button>
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                )}

                                {/* Locations */}
                                {locations.length > 0 && (
                                    <div>
                                        <div className="flex items-center gap-2 mb-3">
                                            <CloudRain size={18} className="text-purple-600" />
                                            <h3 className="text-lg font-semibold text-gray-900">Locations</h3>
                                            <span className="text-sm text-gray-500">({locations.length})</span>
                                        </div>
                                        <div className="space-y-2 pl-6">
                                            {locations.map((site) => (
                                                <div key={site.id} className="border border-gray-200 rounded-lg p-3 flex justify-between items-center bg-purple-50/30">
                                                    <div>
                                                        <p className="font-medium text-gray-900">{site.site_id}</p>
                                                        <p className="text-sm text-gray-500">{site.site_type}</p>
                                                    </div>
                                                    <button
                                                        onClick={() => setManagingSite(site)}
                                                        className="text-sm text-purple-600 hover:underline"
                                                    >
                                                        Manage
                                                    </button>
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                )}

                                {sites?.length === 0 && (
                                    <p className="text-sm text-gray-400 italic text-center py-4">No sites added yet</p>
                                )}
                            </div>
                        )}
                    </div>

                    {/* Project Installs */}
                    <div className="bg-white border border-gray-200 rounded-xl shadow-sm overflow-hidden">
                        <div
                            className="p-6 flex justify-between items-center cursor-pointer hover:bg-gray-50 transition-colors"
                            onClick={() => setIsInstallsOpen(!isInstallsOpen)}
                        >
                            <div className="flex items-center gap-2">
                                {isInstallsOpen ? <ChevronDown size={20} className="text-gray-400" /> : <ChevronRight size={20} className="text-gray-400" />}
                                <h2 className="text-xl font-bold text-gray-900">Project Installs</h2>
                            </div>
                            <button
                                onClick={(e) => {
                                    e.stopPropagation();
                                    setIsAddInstallModalOpen(true);
                                }}
                                className="flex items-center gap-1 text-sm bg-blue-600 text-white px-3 py-1.5 rounded-lg hover:bg-blue-700"
                            >
                                <Plus size={16} />
                                Add Install
                            </button>
                        </div>

                        {isInstallsOpen && (
                            <div className="px-6 pb-6 border-t border-gray-100 pt-4">
                                <div className="space-y-3">
                                    {installs?.map((install) => (
                                        <div key={install.id} className="border border-gray-200 rounded-lg p-3">
                                            <div className="flex justify-between items-start">
                                                <div>
                                                    <p className="font-medium text-gray-900">{install.install_id}</p>
                                                    <p className="text-sm text-gray-500">{install.install_type}</p>
                                                </div>
                                                <span className="text-xs text-gray-500">
                                                    {install.install_date ? new Date(install.install_date).toLocaleDateString() : 'N/A'}
                                                </span>
                                            </div>
                                        </div>
                                    ))}
                                    {installs?.length === 0 && (
                                        <p className="text-sm text-gray-400 italic text-center py-4">No installs created yet</p>
                                    )}
                                </div>
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
                                <span className="text-gray-500">Network Assets</span>
                                <span className="font-medium text-blue-600">{networkAssets.length}</span>
                            </div>
                            <div className="flex justify-between items-center">
                                <span className="text-gray-500">Locations</span>
                                <span className="font-medium text-purple-600">{locations.length}</span>
                            </div>
                            <div className="flex justify-between items-center">
                                <span className="text-gray-500">Total Monitors</span>
                                <span className="font-medium text-green-600">{monitors?.length || 0}</span>
                            </div>
                            <div className="flex justify-between items-center">
                                <span className="text-gray-500">Total Installs</span>
                                <span className="font-medium text-orange-600">{installs?.length || 0}</span>
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

            <AddSiteModal
                isOpen={isAddSiteModalOpen}
                onClose={() => setIsAddSiteModalOpen(false)}
                projectId={id}
            />

            <EditProjectModal
                isOpen={isEditProjectModalOpen}
                onClose={() => setIsEditProjectModalOpen(false)}
                project={project}
            />

            <AddMonitorModal
                isOpen={isAddMonitorModalOpen}
                onClose={() => setIsAddMonitorModalOpen(false)}
                projectId={id}
            />

            {managingSite && (
                <ManageSiteModal
                    isOpen={!!managingSite}
                    onClose={() => setManagingSite(null)}
                    site={managingSite}
                    projectId={id}
                />
            )}

            {managingMonitor && (
                <ManageMonitorModal
                    isOpen={!!managingMonitor}
                    onClose={() => setManagingMonitor(null)}
                    monitor={managingMonitor}
                    projectId={id}
                />
            )}

            <AddInstallModal
                isOpen={isAddInstallModalOpen}
                onClose={() => setIsAddInstallModalOpen(false)}
                projectId={id}
            />
        </div>
    );
};

export default SurveyDashboard;
