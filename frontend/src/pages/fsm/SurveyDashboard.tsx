import React, { useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useProject, useSites, useProjectMonitors, useProjectInstalls, useDeleteInstall, useUninstallInstall, useIngestProject, useProcessProject, useProjectInterims } from '../../api/hooks';
import { useToast } from '../../contexts/ToastContext';
import type { Site, Monitor, Install, Interim } from '../../api/hooks';
import {
    ArrowLeft, MapPin, Loader2, Plus, Building2, CloudRain,
    ChevronDown, ChevronRight, Activity, Droplets, Trash2, Database, HardDrive, Play, Calendar, FileText, Pencil
} from 'lucide-react';
import AddSiteModal from './AddSiteModal';
import EditProjectModal from './EditProjectModal';
import AddMonitorModal from './AddMonitorModal';
import ManageSiteModal from './ManageSiteModal';
import ManageMonitorModal from './ManageMonitorModal';
import AddInstallModal from './AddInstallModal';
import DeleteInstallModal from './DeleteInstallModal';
import CreateInterimModal from './CreateInterimModal';
import EditInterimModal from './EditInterimModal';
import DeleteInterimConfirmModal from './DeleteInterimConfirmModal';

const SurveyDashboard: React.FC = () => {
    const { projectId } = useParams<{ projectId: string }>();
    const id = parseInt(projectId || '0');

    const { data: project, isLoading: projectLoading } = useProject(id);
    const { data: sites, isLoading: sitesLoading } = useSites(id);
    const { data: monitors } = useProjectMonitors(id);
    const { data: installs } = useProjectInstalls(id);
    const { data: interims } = useProjectInterims(id);

    const [isAddSiteModalOpen, setIsAddSiteModalOpen] = useState(false);
    const [isEditProjectModalOpen, setIsEditProjectModalOpen] = useState(false);
    const [isAddMonitorModalOpen, setIsAddMonitorModalOpen] = useState(false);
    const [isAddInstallModalOpen, setIsAddInstallModalOpen] = useState(false);
    const [managingSite, setManagingSite] = useState<Site | null>(null);
    const [managingMonitor, setManagingMonitor] = useState<Monitor | null>(null);
    const [deletingInstall, setDeletingInstall] = useState<Install | null>(null);

    // Section Collapse State
    const [isMonitorsOpen, setIsMonitorsOpen] = useState(false);
    const [isSitesOpen, setIsSitesOpen] = useState(false);
    const [isInstallsOpen, setIsInstallsOpen] = useState(false);
    const [isDataProcessingOpen, setIsDataProcessingOpen] = useState(false);
    const [isInterimsOpen, setIsInterimsOpen] = useState(true);
    const [isCreateInterimModalOpen, setIsCreateInterimModalOpen] = useState(false);
    const [editingInterim, setEditingInterim] = useState<Interim | null>(null);
    const [deletingInterimConfirm, setDeletingInterimConfirm] = useState<Interim | null>(null);

    // Group sites by type
    const networkAssets = sites?.filter(s => s.site_type === 'Flow Monitor' || s.site_type === 'Pump Station') || [];
    const locations = sites?.filter(s => s.site_type === 'Rain Gauge') || [];

    // Group monitors by type
    const flowMonitors = monitors?.filter(m => m.monitor_type === 'Flow Monitor') || [];
    const rainGauges = monitors?.filter(m => m.monitor_type === 'Rain Gauge') || [];
    const otherMonitors = monitors?.filter(m => m.monitor_type !== 'Flow Monitor' && m.monitor_type !== 'Rain Gauge') || [];

    // Delete and uninstall mutations
    const { mutate: deleteInstall } = useDeleteInstall();
    const { mutate: uninstallInstall } = useUninstallInstall();
    const { mutate: ingestProject, isPending: isIngesting } = useIngestProject();
    const { mutate: processProject, isPending: isProcessing } = useProcessProject();
    const { showToast } = useToast();

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
                                {project.name}
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
                                                <div className="flex-1">
                                                    <p className="font-medium text-gray-900">{install.install_id}</p>
                                                    <p className="text-sm text-gray-500">{install.install_type}</p>
                                                    {install.removal_date && (
                                                        <p className="text-xs text-red-500 mt-1">
                                                            Removed: {new Date(install.removal_date).toLocaleDateString()}
                                                        </p>
                                                    )}
                                                </div>
                                                <div className="flex items-center gap-2">
                                                    <span className="text-xs text-gray-500">
                                                        {install.install_date ? new Date(install.install_date).toLocaleDateString() : 'N/A'}
                                                    </span>
                                                    <Link
                                                        to={`/fsm/install/${install.id}`}
                                                        className="text-sm text-blue-600 hover:underline"
                                                    >
                                                        Manage
                                                    </Link>
                                                    <button
                                                        onClick={() => setDeletingInstall(install)}
                                                        className="text-red-600 hover:text-red-700"
                                                    >
                                                        <Trash2 size={16} />
                                                    </button>
                                                </div>
                                            </div>

                                            {/* Data Status Indicators */}
                                            <div className="mt-3 pt-2 border-t border-gray-100 flex gap-4 text-xs">
                                                <div className="flex items-center gap-1.5 text-gray-500" title="Last Data Ingested (Raw)">
                                                    <CloudRain size={12} className="text-blue-400" />
                                                    {install.last_data_ingested
                                                        ? new Date(install.last_data_ingested).toLocaleString(undefined, {
                                                            month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit'
                                                        })
                                                        : <span className="text-gray-400">No data</span>}
                                                </div>
                                                <div className="flex items-center gap-1.5 text-gray-500" title="Last Data Processed">
                                                    <Play size={12} className="text-green-500" />
                                                    {install.last_data_processed
                                                        ? new Date(install.last_data_processed).toLocaleString(undefined, {
                                                            month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit'
                                                        })
                                                        : <span className="text-gray-400">Not processed</span>}
                                                </div>
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

                    {/* Data Processing */}
                    <div className="bg-white border border-gray-200 rounded-xl shadow-sm overflow-hidden">
                        <div
                            className="p-6 flex justify-between items-center cursor-pointer hover:bg-gray-50 transition-colors"
                            onClick={() => setIsDataProcessingOpen(!isDataProcessingOpen)}
                        >
                            <div className="flex items-center gap-2">
                                {isDataProcessingOpen ? <ChevronDown size={20} className="text-gray-400" /> : <ChevronRight size={20} className="text-gray-400" />}
                                <div>
                                    <h2 className="text-xl font-bold text-gray-900 flex items-center gap-2">
                                        <Database size={20} className="text-gray-400" />
                                        Data Processing
                                    </h2>
                                    <p className="text-sm text-gray-500 mt-1 font-normal">
                                        Ingest raw data and run processing pipelines.
                                    </p>
                                </div>
                            </div>
                        </div>

                        {isDataProcessingOpen && (
                            <div className="px-6 pb-6 space-y-6 border-t border-gray-100 pt-4">
                                {/* Ingestion Section */}
                                <div>
                                    <div className="flex justify-between items-center mb-2">
                                        <h3 className="text-sm font-semibold text-gray-900">1. Data Ingestion</h3>
                                        {project.last_ingestion_date && (
                                            <span className="text-xs text-gray-500">
                                                Last: {new Date(project.last_ingestion_date).toLocaleString()}
                                            </span>
                                        )}
                                    </div>
                                    <div className="bg-gray-50 rounded-lg p-4 flex flex-col sm:flex-row items-center justify-between gap-4">
                                        <div className="flex-1 w-full relative">
                                            <p className="text-xs text-gray-500 font-medium uppercase tracking-wider mb-1">Source Path</p>
                                            <div className="flex items-center gap-2 text-sm text-gray-700 font-mono bg-white border border-gray-200 px-3 py-2 rounded">
                                                <HardDrive size={14} className="text-gray-400 shrink-0" />
                                                <span className="truncate" title={project.default_download_path || "Not configured"}>
                                                    {project.default_download_path || "No default path configured"}
                                                </span>
                                            </div>
                                        </div>

                                        <button
                                            onClick={() => ingestProject(project.id, {
                                                onSuccess: () => showToast('Ingestion started successfully', 'success'),
                                                onError: () => showToast('Failed to start ingestion', 'error')
                                            })}
                                            disabled={isIngesting || !project.default_download_path}
                                            className="w-full sm:w-auto px-4 py-2 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                                        >
                                            {isIngesting ? <Loader2 size={18} className="animate-spin" /> : <CloudRain size={18} />}
                                            Run Ingestion
                                        </button>
                                    </div>
                                    {!project.default_download_path && (
                                        <p className="text-xs text-amber-600 mt-2 flex items-center gap-1">
                                            <Activity size={12} />
                                            Please configure a Default Ingestion Path in Project Settings to enable ingestion.
                                        </p>
                                    )}
                                </div>

                                <div className="border-t border-gray-100"></div>

                                {/* Processing Section */}
                                <div>
                                    <div className="flex justify-between items-center mb-2">
                                        <h3 className="text-sm font-semibold text-gray-900">2. Data Processing</h3>
                                    </div>
                                    <div className="bg-gray-50 rounded-lg p-4 flex flex-col sm:flex-row items-center justify-between gap-4">
                                        <div className="flex-1">
                                            <p className="text-sm text-gray-600">
                                                Process raw data for all installs in this project. This calculates flow rates and applies calibrations.
                                            </p>
                                        </div>
                                        <button
                                            onClick={() => processProject(project.id, {
                                                onSuccess: (data: any) => {
                                                    const successCount = data.success || 0;
                                                    const failedCount = data.failed || 0;
                                                    if (failedCount > 0) {
                                                        showToast(`Processed ${successCount} successfully. ${failedCount} failed.`, 'error');
                                                    } else {
                                                        showToast(`Successfully processed ${successCount} installs.`, 'success');
                                                    }
                                                },
                                                onError: (err) => showToast(`Processing failed: ${err.message}`, 'error')
                                            })}
                                            disabled={isProcessing}
                                            className="w-full sm:w-auto px-4 py-2 bg-green-600 text-white font-medium rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                                        >
                                            {isProcessing ? <Loader2 size={18} className="animate-spin" /> : <Play size={18} />}
                                            Run Processing
                                        </button>
                                    </div>
                                </div>
                            </div>
                        )}
                    </div>

                    {/* Interims */}
                    <div className="bg-white border border-gray-200 rounded-xl shadow-sm overflow-hidden">
                        <div
                            className="p-6 flex justify-between items-center cursor-pointer hover:bg-gray-50 transition-colors"
                            onClick={() => setIsInterimsOpen(!isInterimsOpen)}
                        >
                            <div className="flex items-center gap-2">
                                {isInterimsOpen ? <ChevronDown size={20} className="text-gray-400" /> : <ChevronRight size={20} className="text-gray-400" />}
                                <h2 className="text-xl font-bold text-gray-900 flex items-center gap-2">
                                    <Calendar size={20} className="text-purple-500" />
                                    Interims
                                </h2>
                                {interims && interims.length > 0 && (
                                    <span className="text-sm text-gray-500">({interims.length})</span>
                                )}
                            </div>
                            <button
                                onClick={(e) => {
                                    e.stopPropagation();
                                    setIsCreateInterimModalOpen(true);
                                }}
                                className="flex items-center gap-1 text-sm bg-purple-600 text-white px-3 py-1.5 rounded-lg hover:bg-purple-700"
                            >
                                <Plus size={16} />
                                New Interim
                            </button>
                        </div>

                        {isInterimsOpen && (
                            <div className="px-6 pb-6 border-t border-gray-100 pt-4">
                                {interims && interims.length > 0 ? (
                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                        {interims.map((interim) => {
                                            const reviewCount = interim.review_count || 0;
                                            const reviewsComplete = interim.reviews_complete || 0;
                                            const progressPct = reviewCount > 0 ? Math.round((reviewsComplete / reviewCount) * 100) : 0;

                                            const statusColors: Record<string, string> = {
                                                draft: 'bg-gray-100 text-gray-600',
                                                in_progress: 'bg-blue-100 text-blue-700',
                                                complete: 'bg-green-100 text-green-700',
                                                locked: 'bg-purple-100 text-purple-700',
                                            };

                                            return (
                                                <div
                                                    key={interim.id}
                                                    className="border border-gray-200 rounded-lg p-4 bg-purple-50/30 hover:bg-purple-50/50 transition-colors"
                                                >
                                                    <div className="flex justify-between items-start mb-3">
                                                        <div>
                                                            <p className="font-medium text-gray-900">
                                                                {new Date(interim.start_date).toLocaleDateString()} - {new Date(interim.end_date).toLocaleDateString()}
                                                            </p>
                                                            <span className={`text-xs px-2 py-0.5 rounded-full ${statusColors[interim.status] || statusColors.draft}`}>
                                                                {interim.status.replace('_', ' ')}
                                                            </span>
                                                        </div>
                                                        <div className="flex gap-2">
                                                            <Link
                                                                to={`/fsm/interim/${interim.id}`}
                                                                className="text-sm text-purple-600 hover:underline"
                                                            >
                                                                Manage
                                                            </Link>
                                                            {interim.status !== 'locked' && (
                                                                <>
                                                                    <button
                                                                        onClick={() => setEditingInterim(interim)}
                                                                        className="text-gray-400 hover:text-purple-600"
                                                                        title="Edit dates"
                                                                    >
                                                                        <Pencil size={14} />
                                                                    </button>
                                                                    <button
                                                                        onClick={() => setDeletingInterimConfirm(interim)}
                                                                        className="text-gray-400 hover:text-red-600"
                                                                        title="Delete interim"
                                                                    >
                                                                        <Trash2 size={14} />
                                                                    </button>
                                                                </>
                                                            )}
                                                            {interim.status === 'complete' && (
                                                                <button className="text-sm text-gray-500 hover:text-gray-700 flex items-center gap-1">
                                                                    <FileText size={14} />
                                                                    Report
                                                                </button>
                                                            )}
                                                        </div>
                                                    </div>

                                                    {/* Progress bar */}
                                                    <div className="mb-2">
                                                        <div className="flex justify-between text-xs text-gray-500 mb-1">
                                                            <span>Reviews</span>
                                                            <span>{reviewsComplete}/{reviewCount}</span>
                                                        </div>
                                                        <div className="w-full bg-gray-200 rounded-full h-2">
                                                            <div
                                                                className={`h-2 rounded-full transition-all ${progressPct === 100 ? 'bg-green-500' : 'bg-purple-500'
                                                                    }`}
                                                                style={{ width: `${progressPct}%` }}
                                                            />
                                                        </div>
                                                    </div>
                                                </div>
                                            );
                                        })}
                                    </div>
                                ) : (
                                    <p className="text-sm text-gray-400 italic text-center py-4">
                                        No interims created yet. Click "New Interim" to start a review period.
                                    </p>
                                )}
                            </div>
                        )}
                    </div>

                </div>

                {/* Right Column: Map & Stats */}
                <div className="space-y-6">
                    <div className="bg-white border border-gray-200 rounded-xl p-6 shadow-sm">
                        <h3 className="font-bold text-gray-900 mb-4">Project Stats</h3>
                        <div className="space-y-3">
                            {/* Sites Section */}
                            <div className="flex justify-between items-center">
                                <span className="text-gray-700 font-semibold">Total Sites</span>
                                <span className="font-bold">{sites?.length || 0}</span>
                            </div>
                            <div className="flex justify-between items-center pl-4">
                                <span className="text-gray-500 text-sm">Network Assets</span>
                                <span className="font-medium text-blue-600 text-sm">{networkAssets.length}</span>
                            </div>
                            <div className="flex justify-between items-center pl-4">
                                <span className="text-gray-500 text-sm">Locations</span>
                                <span className="font-medium text-purple-600 text-sm">{locations.length}</span>
                            </div>

                            <div className="border-t border-gray-100 pt-3 mt-3"></div>

                            {/* Monitors Section */}
                            <div className="flex justify-between items-center">
                                <span className="text-gray-700 font-semibold">Total Monitors</span>
                                <span className="font-bold">{monitors?.length || 0}</span>
                            </div>
                            <div className="flex justify-between items-center pl-4">
                                <span className="text-gray-500 text-sm">Flow Monitors</span>
                                <span className="font-medium text-blue-600 text-sm">{flowMonitors.length}</span>
                            </div>
                            <div className="flex justify-between items-center pl-4">
                                <span className="text-gray-500 text-sm">Rain Gauges</span>
                                <span className="font-medium text-cyan-600 text-sm">{rainGauges.length}</span>
                            </div>
                            {otherMonitors.length > 0 && (
                                <div className="flex justify-between items-center pl-4">
                                    <span className="text-gray-500 text-sm">Other</span>
                                    <span className="font-medium text-gray-600 text-sm">{otherMonitors.length}</span>
                                </div>
                            )}
                            <div className="flex justify-between items-center pl-4 pt-1">
                                <span className="text-gray-400 text-xs italic">Installed</span>
                                <span className="font-medium text-green-600 text-xs">
                                    {installs?.filter(i => !i.removal_date).length || 0}
                                </span>
                            </div>
                            <div className="flex justify-between items-center pl-4">
                                <span className="text-gray-400 text-xs italic">Available</span>
                                <span className="font-medium text-gray-500 text-xs">
                                    {(monitors?.length || 0) - (installs?.filter(i => !i.removal_date).length || 0)}
                                </span>
                            </div>

                            <div className="border-t border-gray-100 pt-3 mt-3"></div>

                            {/* Installs Section */}
                            <div className="flex justify-between items-center">
                                <span className="text-gray-700 font-semibold">Total Installs</span>
                                <span className="font-bold">{installs?.length || 0}</span>
                            </div>
                            <div className="flex justify-between items-center pl-4">
                                <span className="text-gray-500 text-sm">Flow Monitors</span>
                                <span className="font-medium text-blue-600 text-sm">
                                    {installs?.filter(i => i.install_type === 'Flow Monitor').length || 0}
                                </span>
                            </div>
                            <div className="flex justify-between items-center pl-4">
                                <span className="text-gray-500 text-sm">Rain Gauges</span>
                                <span className="font-medium text-cyan-600 text-sm">
                                    {installs?.filter(i => i.install_type === 'Rain Gauge').length || 0}
                                </span>
                            </div>
                            {installs?.some(i => i.install_type !== 'Flow Monitor' && i.install_type !== 'Rain Gauge') && (
                                <div className="flex justify-between items-center pl-4">
                                    <span className="text-gray-500 text-sm">Other</span>
                                    <span className="font-medium text-gray-600 text-sm">
                                        {installs?.filter(i => i.install_type !== 'Flow Monitor' && i.install_type !== 'Rain Gauge').length || 0}
                                    </span>
                                </div>
                            )}
                            <div className="flex justify-between items-center pl-4 pt-1">
                                <span className="text-gray-400 text-xs italic">Active</span>
                                <span className="font-medium text-green-600 text-xs">
                                    {installs?.filter(i => !i.removal_date).length || 0}
                                </span>
                            </div>
                            <div className="flex justify-between items-center pl-4">
                                <span className="text-gray-400 text-xs italic">Removed</span>
                                <span className="font-medium text-gray-400 text-xs">
                                    {installs?.filter(i => i.removal_date).length || 0}
                                </span>
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

            {deletingInstall && (
                <DeleteInstallModal
                    isOpen={!!deletingInstall}
                    onClose={() => setDeletingInstall(null)}
                    install={deletingInstall}
                    onDelete={() => {
                        deleteInstall(deletingInstall.id);
                        setDeletingInstall(null);
                    }}
                    onUninstall={(removalDate) => {
                        uninstallInstall({ installId: deletingInstall.id, removalDate });
                        setDeletingInstall(null);
                    }}
                />
            )}

            <CreateInterimModal
                isOpen={isCreateInterimModalOpen}
                onClose={() => setIsCreateInterimModalOpen(false)}
                projectId={id}
            />

            {editingInterim && (
                <EditInterimModal
                    isOpen={!!editingInterim}
                    onClose={() => setEditingInterim(null)}
                    interim={editingInterim}
                />
            )}

            {deletingInterimConfirm && (
                <DeleteInterimConfirmModal
                    isOpen={!!deletingInterimConfirm}
                    onClose={() => setDeletingInterimConfirm(null)}
                    interim={deletingInterimConfirm}
                />
            )}
        </div>
    );
};

export default SurveyDashboard;
