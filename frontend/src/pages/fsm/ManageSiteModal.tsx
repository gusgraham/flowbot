import React, { useState, useEffect, useMemo } from 'react';
import { useForm } from 'react-hook-form';
import { useMutation, useQueryClient, useQuery } from '@tanstack/react-query';
import api from '../../api/client';
import type { Site, Monitor, Install } from '../../api/hooks';
import { X, Loader2, Plus } from 'lucide-react';

interface ManageSiteModalProps {
    isOpen: boolean;
    onClose: () => void;
    site: Site;
    projectId: number;
}

interface InstallFormData {
    monitor_id: number;
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
    "Circular", "Rectangular", "Arched", "Cunette",
    "Egg", "Egg 2", "Oval", "U-Shaped", "Other"
];

const RG_POSITIONS = [
    "Ground", "Roof (First Floor)", "Roof (Higher)", "Post"
];

const ManageSiteModal: React.FC<ManageSiteModalProps> = ({ isOpen, onClose, site, projectId }) => {
    const { register, handleSubmit, reset, watch, setValue, formState: { errors } } = useForm<InstallFormData>();
    const queryClient = useQueryClient();
    const [showInstallForm, setShowInstallForm] = useState(false);

    const selectedMonitorId = watch('monitor_id');

    // Fetch project monitors
    const { data: monitors } = useQuery({
        queryKey: ['monitors', projectId],
        queryFn: async () => {
            const { data } = await api.get<Monitor[]>(`/projects/${projectId}/monitors`);
            return data;
        },
        enabled: isOpen,
    });

    // Fetch site installs
    const { data: installs } = useQuery({
        queryKey: ['installs', site.id],
        queryFn: async () => {
            const { data } = await api.get<Install[]>(`/sites/${site.id}/installs`);
            return data;
        },
        enabled: isOpen,
    });

    // Fetch all project installs to check for active monitors
    const { data: projectInstalls } = useQuery({
        queryKey: ['installs', 'project', projectId],
        queryFn: async () => {
            const { data } = await api.get<Install[]>(`/projects/${projectId}/installs`);
            return data;
        },
        enabled: isOpen,
    });

    const selectedMonitor = monitors?.find(m => m.id === Number(selectedMonitorId));

    // Determine active monitors (those with an install that has no removal date)
    const activeMonitorIds = useMemo(() => {
        if (!projectInstalls) return new Set<number>();
        const activeIds = new Set<number>();
        projectInstalls.forEach(install => {
            if (!install.removal_date) {
                activeIds.add(install.monitor_id);
            }
        });
        return activeIds;
    }, [projectInstalls]);

    // Filter monitors based on site type and active status
    const filteredMonitors = useMemo(() => {
        if (!monitors) return [];

        // Filter out active monitors
        let available = monitors.filter(m => !activeMonitorIds.has(m.id));

        // Filter based on site type
        return available.filter(monitor => {
            if (site.site_type === 'Flow Monitor') {
                return monitor.monitor_type === 'Flow Monitor';
            } else if (site.site_type === 'Rain Gauge') {
                return monitor.monitor_type === 'Raingauge';
            }
            return true;
        });
    }, [monitors, site, activeMonitorIds]);

    // Auto-generate install ID suggestion
    useEffect(() => {
        if (showInstallForm && selectedMonitor && !watch('install_id')) {
            // Optional: pre-fill logic
            // setValue('install_id', `${site.site_id}_${selectedMonitor.monitor_asset_id}`);
        }
    }, [showInstallForm, selectedMonitor, site, setValue, watch]);

    const { mutate: createInstall, isPending } = useMutation({
        mutationFn: async (data: InstallFormData) => {
            const monitor = monitors?.find(m => m.id === data.monitor_id);
            const response = await api.post('/installs', {
                ...data,
                project_id: projectId,
                site_id: site.id,
                install_type: monitor?.monitor_type || 'Flow Monitor'
            });
            return response.data;
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['installs', site.id] });
            queryClient.invalidateQueries({ queryKey: ['monitors', site.id] });
            queryClient.invalidateQueries({ queryKey: ['installs', 'project', projectId] }); // Invalidate project installs
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

                <h2 className="text-xl font-bold text-gray-900 mb-2">Manage Site</h2>
                <p className="text-gray-600 mb-6">{site.site_id} - {site.site_type}</p>

                {/* Site Details */}
                <div className="bg-gray-50 rounded-lg p-4 mb-6">
                    <h3 className="font-semibold text-gray-900 mb-2">Site Details</h3>
                    <div className="grid grid-cols-2 gap-3 text-sm">
                        <div>
                            <span className="text-gray-500">Address:</span>
                            <p className="font-medium">{site.address || 'N/A'}</p>
                        </div>
                        <div>
                            <span className="text-gray-500">MH Ref:</span>
                            <p className="font-medium">{site.mh_ref || 'N/A'}</p>
                        </div>
                        <div>
                            <span className="text-gray-500">What3Words:</span>
                            <p className="font-medium">{site.w3w || 'N/A'}</p>
                        </div>
                        <div>
                            <span className="text-gray-500">Coordinates:</span>
                            <p className="font-medium">{site.easting}, {site.northing}</p>
                        </div>
                    </div>
                </div>

                {/* Installs */}
                <div className="mb-6">
                    <div className="flex justify-between items-center mb-3">
                        <h3 className="font-semibold text-gray-900">Installs</h3>
                        <button
                            onClick={() => setShowInstallForm(!showInstallForm)}
                            className="flex items-center gap-1 text-sm text-blue-600 hover:text-blue-700"
                        >
                            <Plus size={16} />
                            Add Install
                        </button>
                    </div>

                    {showInstallForm && (
                        <form onSubmit={handleSubmit((data) => createInstall(data))} className="bg-blue-50 rounded-lg p-4 mb-4 space-y-3">
                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-1">Monitor</label>
                                    <select
                                        {...register('monitor_id', { required: 'Monitor is required', valueAsNumber: true })}
                                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                                    >
                                        <option value="">Select a monitor...</option>
                                        {filteredMonitors.map((monitor) => (
                                            <option key={monitor.id} value={monitor.id}>
                                                {monitor.monitor_asset_id} - {monitor.monitor_type}
                                            </option>
                                        ))}
                                    </select>
                                    {errors.monitor_id && <p className="text-red-500 text-xs mt-1">{errors.monitor_id.message}</p>}
                                    {filteredMonitors.length === 0 && monitors && monitors.length > 0 && (
                                        <p className="text-xs text-amber-600 mt-1">
                                            No compatible monitors available (check site type or if monitors are already installed).
                                        </p>
                                    )}
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

                            {selectedMonitor && selectedMonitor.monitor_type === 'Flow Monitor' && (
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

                            {selectedMonitor && selectedMonitor.monitor_type === 'Raingauge' && (
                                <div className="space-y-3 pt-2 border-t border-blue-100">
                                    <h4 className="font-medium text-blue-900 text-sm">Raingauge Details</h4>
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
                            <div key={install.id} className="border border-gray-200 rounded-lg p-3">
                                <div className="flex justify-between items-start">
                                    <div>
                                        <p className="font-medium text-gray-900">{install.install_id}</p>
                                        <p className="text-sm text-gray-500">{install.install_type}</p>
                                        {install.install_type === 'Flow Monitor' && install.fm_pipe_letter && (
                                            <p className="text-xs text-gray-500">Pipe: {install.fm_pipe_letter}</p>
                                        )}
                                    </div>
                                    <span className="text-xs text-gray-500">
                                        {install.install_date ? new Date(install.install_date).toLocaleDateString() : 'N/A'}
                                    </span>
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

export default ManageSiteModal;
