import React, { useState, useMemo, useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { useMutation, useQueryClient, useQuery } from '@tanstack/react-query';
import api from '../../api/client';
import type { Site, Monitor, Install } from '../../api/hooks';
import { X, Loader2, Plus, AlertTriangle } from 'lucide-react';

interface ManageMonitorModalProps {
    isOpen: boolean;
    onClose: () => void;
    monitor: Monitor;
    projectId: number;
}

interface InstallFormData {
    site_id: number;
    install_id: string;
    install_date: string;
    // FM Specific
    fm_pipe_shape?: string;
    fm_pipe_height_mm?: number;
    fm_pipe_width_mm?: number;
    fm_pipe_letter?: string;
    fm_pipe_depth_to_invert_mm?: number;
    fm_sensor_offset_mm?: number;
    // RG Specific
    rg_position?: string;
}

const PIPE_SHAPES = [
    "CIRC", "RECT", "ARCH", "CNET",
    "EGG", "EGG2", "OVAL", "UTOP", "USER"
];

const RG_POSITIONS = [
    "Ground", "Roof (First Floor)", "Roof (Higher)", "Post"
];

const ManageMonitorModal: React.FC<ManageMonitorModalProps> = ({ isOpen, onClose, monitor, projectId }) => {
    const { register, handleSubmit, reset, watch, setValue, formState: { errors } } = useForm<InstallFormData>();
    const queryClient = useQueryClient();
    const [showInstallForm, setShowInstallForm] = useState(false);

    // Fetch project sites
    const { data: sites } = useQuery({
        queryKey: ['sites', projectId],
        queryFn: async () => {
            const { data } = await api.get<Site[]>(`/projects/${projectId}/sites`);
            return data;
        },
        enabled: isOpen,
    });

    // Fetch monitor installs
    const { data: installs } = useQuery({
        queryKey: ['installs', monitor.id],
        queryFn: async () => {
            const { data } = await api.get<Install[]>(`/monitors/${monitor.id}/installs`);
            return data;
        },
        enabled: isOpen,
    });

    // Check if monitor is currently installed
    const activeInstall = useMemo(() => {
        return installs?.find(install => !install.removal_date);
    }, [installs]);

    // Filter sites based on monitor type
    const filteredSites = useMemo(() => {
        if (!sites) return [];
        return sites.filter(site => {
            if (monitor.monitor_type === 'Flow Monitor') {
                return site.site_type === 'Flow Monitor';
            } else if (monitor.monitor_type === 'Rain Gauge') {
                return site.site_type === 'Rain Gauge';
            }
            return true;
        });
    }, [sites, monitor]);

    // Auto-generate install ID suggestion
    useEffect(() => {
        if (showInstallForm && !watch('install_id')) {
            // Optional logic
        }
    }, [showInstallForm, watch]);

    const { mutate: createInstall, isPending } = useMutation({
        mutationFn: async (data: InstallFormData) => {
            const response = await api.post('/installs', {
                ...data,
                project_id: projectId,
                monitor_id: monitor.id,
                install_type: monitor.monitor_type
            });
            return response.data;
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['installs', monitor.id] });
            queryClient.invalidateQueries({ queryKey: ['installs', 'project', projectId] }); // Invalidate project installs too
            reset();
            setShowInstallForm(false);
        },
    });

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
            <div className="bg-white rounded-xl shadow-xl w-full max-w-2xl p-6 relative animate-in fade-in zoom-in duration-200 max-h-[90vh] overflow-y-auto">
                <button
                    onClick={onClose}
                    className="absolute top-4 right-4 text-gray-400 hover:text-gray-600"
                >
                    <X size={20} />
                </button>

                <h2 className="text-xl font-bold text-gray-900 mb-2">Manage Monitor</h2>
                <p className="text-gray-600 mb-6">{monitor.monitor_asset_id} - {monitor.monitor_type}</p>

                {/* Monitor Details */}
                <div className="bg-gray-50 rounded-lg p-4 mb-6">
                    <h3 className="font-semibold text-gray-900 mb-2">Monitor Details</h3>
                    <div className="grid grid-cols-2 gap-3 text-sm">
                        <div>
                            <span className="text-gray-500">Asset ID:</span>
                            <p className="font-medium">{monitor.monitor_asset_id}</p>
                        </div>
                        <div>
                            <span className="text-gray-500">Type:</span>
                            <p className="font-medium">{monitor.monitor_type}</p>
                        </div>
                        <div>
                            <span className="text-gray-500">Sub-Type:</span>
                            <p className="font-medium">{monitor.monitor_sub_type}</p>
                        </div>
                        <div>
                            <span className="text-gray-500">PMAC ID:</span>
                            <p className="font-medium">{monitor.pmac_id || 'N/A'}</p>
                        </div>
                    </div>
                </div>

                {/* Installs */}
                <div className="mb-6">
                    <div className="flex justify-between items-center mb-3">
                        <h3 className="font-semibold text-gray-900">Installs</h3>
                        {!activeInstall ? (
                            <button
                                onClick={() => setShowInstallForm(!showInstallForm)}
                                className="flex items-center gap-1 text-sm text-blue-600 hover:text-blue-700"
                            >
                                <Plus size={16} />
                                Add Install
                            </button>
                        ) : (
                            <div className="flex items-center gap-1 text-sm text-amber-600 bg-amber-50 px-2 py-1 rounded border border-amber-200">
                                <AlertTriangle size={14} />
                                Currently Installed
                            </div>
                        )}
                    </div>

                    {showInstallForm && (
                        <form onSubmit={handleSubmit((data) => createInstall(data))} className="bg-blue-50 rounded-lg p-4 mb-4 space-y-3">
                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-1">Site</label>
                                    <select
                                        {...register('site_id', { required: 'Site is required', valueAsNumber: true })}
                                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                                    >
                                        <option value="">Select a site...</option>
                                        {filteredSites?.map((site) => (
                                            <option key={site.id} value={site.id}>
                                                {site.site_id} - {site.site_type}
                                            </option>
                                        ))}
                                    </select>
                                    {errors.site_id && <p className="text-red-500 text-xs mt-1">{errors.site_id.message}</p>}
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-1">Install ID / Label</label>
                                    <input
                                        type="text"
                                        {...register('install_id', { required: 'Install ID is required' })}
                                        placeholder="e.g. FM001"
                                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                                    />
                                    {errors.install_id && <p className="text-red-500 text-xs mt-1">{errors.install_id.message}</p>}
                                </div>
                            </div>

                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">Install Date</label>
                                <input
                                    type="date"
                                    {...register('install_date', { required: 'Install date is required' })}
                                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                                />
                                {errors.install_date && <p className="text-red-500 text-xs mt-1">{errors.install_date.message}</p>}
                            </div>

                            {monitor.monitor_type === 'Flow Monitor' && (
                                <div className="space-y-3 pt-2 border-t border-blue-100">
                                    <h4 className="font-medium text-blue-900 text-sm">Flow Monitor Details</h4>

                                    <div className="grid grid-cols-2 gap-3">
                                        <div>
                                            <label className="block text-sm font-medium text-gray-700 mb-1">Pipe Identifier</label>
                                            <select
                                                {...register('fm_pipe_letter')}
                                                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                                            >
                                                <option value="">Select identifier...</option>
                                                <optgroup label="Incoming">
                                                    {['A', 'B', 'C', 'D', 'E', 'F', 'G'].map(l => (
                                                        <option key={l} value={l}>{l}</option>
                                                    ))}
                                                </optgroup>
                                                <optgroup label="Outgoing">
                                                    {['X', 'Y', 'Z'].map(l => (
                                                        <option key={l} value={l}>{l}</option>
                                                    ))}
                                                </optgroup>
                                            </select>
                                        </div>
                                        <div>
                                            <label className="block text-sm font-medium text-gray-700 mb-1">Pipe Shape</label>
                                            <select
                                                {...register('fm_pipe_shape')}
                                                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                                            >
                                                {PIPE_SHAPES.map(shape => (
                                                    <option key={shape} value={shape}>{shape}</option>
                                                ))}
                                            </select>
                                        </div>
                                    </div>

                                    <div className="grid grid-cols-2 gap-3">
                                        <div>
                                            <label className="block text-sm font-medium text-gray-700 mb-1">Height (mm)</label>
                                            <input
                                                type="number"
                                                {...register('fm_pipe_height_mm', { valueAsNumber: true })}
                                                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                                                defaultValue={225}
                                            />
                                        </div>
                                        <div>
                                            <label className="block text-sm font-medium text-gray-700 mb-1">Width (mm)</label>
                                            <input
                                                type="number"
                                                {...register('fm_pipe_width_mm', { valueAsNumber: true })}
                                                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                                                defaultValue={225}
                                            />
                                        </div>
                                    </div>

                                    <div className="grid grid-cols-2 gap-3">
                                        <div>
                                            <label className="block text-sm font-medium text-gray-700 mb-1">Depth to Invert (mm)</label>
                                            <input
                                                type="number"
                                                {...register('fm_pipe_depth_to_invert_mm', { valueAsNumber: true })}
                                                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                                            />
                                        </div>
                                        <div>
                                            <label className="block text-sm font-medium text-gray-700 mb-1">Sensor Offset (mm)</label>
                                            <input
                                                type="number"
                                                {...register('fm_sensor_offset_mm', { valueAsNumber: true })}
                                                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                                            />
                                        </div>
                                    </div>
                                </div>
                            )}

                            {monitor.monitor_type === 'Rain Gauge' && (
                                <div className="space-y-3 pt-2 border-t border-blue-100">
                                    <h4 className="font-medium text-blue-900 text-sm">Rain Gauge Details</h4>
                                    <div>
                                        <label className="block text-sm font-medium text-gray-700 mb-1">Position</label>
                                        <select
                                            {...register('rg_position')}
                                            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                                        >
                                            {RG_POSITIONS.map(pos => (
                                                <option key={pos} value={pos}>{pos}</option>
                                            ))}
                                        </select>
                                    </div>
                                </div>
                            )}

                            <div className="flex justify-end gap-2 pt-2">
                                <button
                                    type="button"
                                    onClick={() => setShowInstallForm(false)}
                                    className="px-3 py-1 text-sm text-gray-700 hover:bg-gray-100 rounded"
                                >
                                    Cancel
                                </button>
                                <button
                                    type="submit"
                                    disabled={isPending}
                                    className="px-3 py-1 text-sm bg-blue-600 text-white rounded hover:bg-blue-700 flex items-center gap-1"
                                >
                                    {isPending && <Loader2 size={14} className="animate-spin" />}
                                    Create Install
                                </button>
                            </div>
                        </form>
                    )}

                    <div className="space-y-2">
                        {installs?.map((install) => (
                            <div key={install.id} className={`border rounded-lg p-3 ${!install.removal_date ? 'border-green-200 bg-green-50' : 'border-gray-200'}`}>
                                <div className="flex justify-between items-start">
                                    <div>
                                        <div className="flex items-center gap-2">
                                            <p className="font-medium text-gray-900">{install.install_id}</p>
                                            {!install.removal_date && (
                                                <span className="text-xs bg-green-200 text-green-800 px-1.5 py-0.5 rounded-full">Active</span>
                                            )}
                                        </div>
                                        <p className="text-sm text-gray-500">{install.install_type}</p>
                                        {install.install_type === 'Flow Monitor' && install.fm_pipe_letter && (
                                            <p className="text-xs text-gray-500">Pipe: {install.fm_pipe_letter}</p>
                                        )}
                                    </div>
                                    <div className="text-right">
                                        <span className="block text-xs text-gray-500">
                                            Installed: {install.install_date ? new Date(install.install_date).toLocaleDateString() : 'N/A'}
                                        </span>
                                        {install.removal_date && (
                                            <span className="block text-xs text-gray-500">
                                                Removed: {new Date(install.removal_date).toLocaleDateString()}
                                            </span>
                                        )}
                                    </div>
                                </div>
                            </div>
                        ))}
                        {installs?.length === 0 && (
                            <p className="text-sm text-gray-400 italic text-center py-4">No installs yet</p>
                        )}
                    </div>
                </div>

                <div className="flex justify-end">
                    <button
                        onClick={onClose}
                        className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors"
                    >
                        Close
                    </button>
                </div>
            </div>
        </div>
    );
};

export default ManageMonitorModal;
