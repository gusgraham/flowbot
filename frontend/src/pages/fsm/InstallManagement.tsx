import React, { useState, useCallback } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { ArrowLeft, Database, Settings, FileText, Camera, Calendar, Loader2, LineChart } from 'lucide-react';
import { useInstall, useRawDataSettings, useUpdateRawDataSettings, useProjectInstalls } from '../../api/hooks';
import { useToast } from '../../contexts/ToastContext';
import DataIngestionTab from './DataIngestionTab';
import RainGaugeCalibration from './RainGaugeCalibration';
import PumpLoggerCalibration from './PumpLoggerCalibration';
import FlowMonitorCalibration from './FlowMonitorCalibration';
import DataViewerTab from './DataViewerTab';

const InstallManagement: React.FC = () => {
    const { installId } = useParams<{ installId: string }>();
    const navigate = useNavigate();
    const id = parseInt(installId || '0');
    const [activeTab, setActiveTab] = useState<'data-ingestion' | 'calibration' | 'data-viewer' | 'inspections' | 'photos' | 'schedule'>('data-ingestion');

    const { data: install, isLoading } = useInstall(id);
    const { data: rawSettings } = useRawDataSettings(id);
    const { data: projectInstalls } = useProjectInstalls(install?.project_id || 0);
    const { mutate: updateSettings, isPending: isUpdating } = useUpdateRawDataSettings();
    const { showToast } = useToast();

    const handleCalibrationSave = useCallback((data: any) => {
        updateSettings(
            { installId: id, settings: data },
            {
                onSuccess: () => {
                    showToast('Calibration settings saved successfully', 'success');
                },
                onError: (error) => {
                    console.error('Failed to save settings:', error);
                    showToast('Failed to save calibration settings', 'error');
                }
            }
        );
    }, [id, updateSettings, showToast]);

    const tabs = [
        { id: 'data-ingestion', label: 'Data Ingestion', icon: Database, color: 'green' },
        { id: 'calibration', label: 'Calibration', icon: Settings, color: 'orange' },
        { id: 'data-viewer', label: 'Data Viewer', icon: LineChart, color: 'indigo' },
        { id: 'inspections', label: 'Inspections', icon: FileText, color: 'blue' },
        { id: 'photos', label: 'Photographs', icon: Camera, color: 'purple' },
        { id: 'schedule', label: 'Visit Schedule', icon: Calendar, color: 'cyan' },
    ];

    if (isLoading) {
        return (
            <div className="flex justify-center items-center h-64">
                <Loader2 className="animate-spin text-gray-400" size={32} />
            </div>
        );
    }

    if (!install) {
        return (
            <div className="text-center py-12">
                <p className="text-gray-500">Install not found</p>
            </div>
        );
    }

    return (
        <div className="max-w-7xl mx-auto">
            <div className="mb-6">
                <Link to={`/fsm/${install.project_id}`} className="inline-flex items-center text-sm text-gray-500 hover:text-gray-900 mb-4">
                    <ArrowLeft size={16} className="mr-1" /> Back to Project
                </Link>

                <div className="flex items-center justify-between">
                    <div>
                        <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-3">
                            Install Management
                        </h1>
                        <div className="mt-2">
                            {projectInstalls ? (
                                <select
                                    value={install.id}
                                    onChange={(e) => navigate(`/fsm/install/${e.target.value}`)}
                                    className="text-lg font-medium text-gray-700 border-gray-300 rounded-md shadow-sm focus:border-blue-500 focus:ring-blue-500 bg-transparent py-1 pl-2 pr-8"
                                >
                                    {projectInstalls.map((inst) => (
                                        <option key={inst.id} value={inst.id}>
                                            {inst.install_id} - {inst.install_type}
                                        </option>
                                    ))}
                                </select>
                            ) : (
                                <p className="text-gray-500 text-lg">
                                    {install.install_id} - {install.install_type}
                                </p>
                            )}
                        </div>
                    </div>
                </div>
            </div>

            {/* Tab Navigation */}
            <div className="border-b border-gray-200 mb-6">
                <nav className="-mb-px flex space-x-8">
                    {tabs.map((tab) => {
                        const Icon = tab.icon;
                        const isActive = activeTab === tab.id;
                        return (
                            <button
                                key={tab.id}
                                onClick={() => setActiveTab(tab.id as any)}
                                className={`
                                    flex items-center gap-2 py-4 px-1 border-b-2 font-medium text-sm
                                    ${isActive
                                        ? 'border-blue-500 text-blue-600'
                                        : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                                    }
                                `}
                            >
                                <Icon size={18} />
                                {tab.label}
                            </button>
                        );
                    })}
                </nav>
            </div>

            {/* Tab Content */}
            <div className="bg-white border border-gray-200 rounded-xl shadow-sm">
                {activeTab === 'data-ingestion' && (
                    <div className="p-6">
                        <h2 className="text-xl font-bold text-gray-900 mb-4">Data Ingestion Settings</h2>
                        <p className="text-gray-500 mb-6">
                            Configure file paths and formats for automated data import from monitoring equipment.
                        </p>

                        <DataIngestionTab installId={id} installType={install.install_type} />
                    </div>
                )}

                {activeTab === 'calibration' && (
                    <div className="p-6">
                        <h2 className="text-xl font-bold text-gray-900 mb-4">Calibration Settings</h2>
                        <p className="text-gray-500 mb-6">
                            Manage calibration settings, correction factors, and adjustment tables.
                        </p>

                        {install.install_type === 'Rain Gauge' && (
                            <RainGaugeCalibration
                                installId={id}
                                settings={rawSettings}
                                onSave={handleCalibrationSave}
                                isSaving={isUpdating}
                            />
                        )}

                        {install.install_type === 'Pump Logger' && (
                            <PumpLoggerCalibration
                                installId={id}
                                settings={rawSettings}
                                onSave={handleCalibrationSave}
                                isSaving={isUpdating}
                            />
                        )}

                        {(install.install_type === 'Flow Monitor' || install.install_type === 'Depth Monitor') && (
                            <FlowMonitorCalibration
                                installId={id}
                                settings={rawSettings}
                                onSave={handleCalibrationSave}
                                isSaving={isUpdating}
                            />
                        )}
                    </div>
                )}

                {activeTab === 'data-viewer' && (
                    <div className="p-6">
                        <h2 className="text-xl font-bold text-gray-900 mb-4">Data Viewer</h2>
                        <p className="text-gray-500 mb-6">
                            View raw and processed time series data for this install.
                        </p>
                        <DataViewerTab installId={id} installType={install.install_type} />
                    </div>
                )}

                {activeTab === 'inspections' && (
                    <div className="p-6">
                        <h2 className="text-xl font-bold text-gray-900 mb-4">Inspections</h2>
                        <p className="text-gray-500 mb-6">
                            Manage site inspections, maintenance records, and field notes.
                        </p>
                        <div className="text-center py-12 text-gray-400">
                            Coming Soon
                        </div>
                    </div>
                )}

                {activeTab === 'photos' && (
                    <div className="p-6">
                        <h2 className="text-xl font-bold text-gray-900 mb-4">Photographs</h2>
                        <p className="text-gray-500 mb-6">
                            Upload and manage installation photographs and site imagery.
                        </p>
                        <div className="text-center py-12 text-gray-400">
                            Coming Soon
                        </div>
                    </div>
                )}

                {activeTab === 'schedule' && (
                    <div className="p-6">
                        <h2 className="text-xl font-bold text-gray-900 mb-4">Visit Schedule</h2>
                        <p className="text-gray-500 mb-6">
                            Plan and track site visits, maintenance schedules, and data downloads.
                        </p>
                        <div className="text-center py-12 text-gray-400">
                            Coming Soon
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
};

export default InstallManagement;
