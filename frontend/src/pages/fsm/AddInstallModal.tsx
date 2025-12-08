import React, { useEffect, useMemo } from 'react';
import { useForm } from 'react-hook-form';
import { useMutation, useQueryClient, useQuery } from '@tanstack/react-query';
import api from '../../api/client';
import type { Site, Monitor, Install } from '../../api/hooks';
import { X, Loader2 } from 'lucide-react';

interface AddInstallModalProps {
    isOpen: boolean;
    onClose: () => void;
    projectId: number;
}

interface InstallFormData {
    monitor_id: number;
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

const PIPE_SHAPES = ["ARCH", "CIRC", "CNET", "EGG", "EGG2", "OVAL", "RECT", "UTOP", "USER"];

const RG_POSITIONS = [
    "Ground", "Roof (First Floor)", "Roof (Higher)", "Post"
];

const AddInstallModal: React.FC<AddInstallModalProps> = ({ isOpen, onClose, projectId }) => {
    const { register, handleSubmit, reset, watch, setValue, formState: { errors } } = useForm<InstallFormData>();
    const queryClient = useQueryClient();

    const selectedMonitorId = watch('monitor_id');
    const selectedSiteId = watch('site_id');

    // Fetch project monitors
    const { data: monitors } = useQuery({
        queryKey: ['monitors', projectId],
        queryFn: async () => {
            const { data } = await api.get<Monitor[]>(`/projects/${projectId}/monitors`);
            return data;
        },
        enabled: isOpen,
    });

    // Fetch project sites
    const { data: sites } = useQuery({
        queryKey: ['sites', projectId],
        queryFn: async () => {
            const { data } = await api.get<Site[]>(`/projects/${projectId}/sites`);
            return data;
        },
        enabled: isOpen,
    });

    // Fetch all project installs to check for active ones
    const { data: projectInstalls } = useQuery({
        queryKey: ['installs', 'project', projectId],
        queryFn: async () => {
            const { data } = await api.get<Install[]>(`/projects/${projectId}/installs`);
            return data;
        },
        enabled: isOpen,
    });

    const selectedMonitor = monitors?.find(m => m.id === Number(selectedMonitorId));
    const selectedSite = sites?.find(s => s.id === Number(selectedSiteId));

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

    // Filtered lists based on selection
    const filteredSites = useMemo(() => {
        if (!sites) return [];
        if (!selectedMonitor) return sites;

        // Filter sites based on monitor type
        return sites.filter(site => {
            if (selectedMonitor.monitor_type === 'Flow Monitor') {
                return site.site_type === 'Flow Monitor'; // Assuming "Flow Monitor" site type corresponds to Network Asset
            } else if (selectedMonitor.monitor_type === 'Rain Gauge') {
                return site.site_type === 'Rain Gauge'; // Assuming "Rain Gauge" site type corresponds to Location
            }
            return true;
        });
    }, [sites, selectedMonitor]);

    const filteredMonitors = useMemo(() => {
        if (!monitors) return [];

        // First filter out active monitors (unless it's the currently selected one, though that shouldn't happen in "Add" flow)
        let available = monitors.filter(m => !activeMonitorIds.has(m.id));

        if (!selectedSite) return available;

        // Filter monitors based on site type
        return available.filter(monitor => {
            if (selectedSite.site_type === 'Flow Monitor') {
                return monitor.monitor_type === 'Flow Monitor';
            } else if (selectedSite.site_type === 'Rain Gauge') {
                return monitor.monitor_type === 'Rain Gauge';
            }
            return true;
        });
    }, [monitors, selectedSite, activeMonitorIds]);


    // Auto-generate install ID suggestion
    useEffect(() => {
        if (selectedMonitor && selectedSite && !watch('install_id')) {
            // Optional: pre-fill logic
        }
    }, [selectedMonitor, selectedSite, setValue, watch]);

    const { mutate, isPending } = useMutation({
        mutationFn: async (data: InstallFormData) => {
            const monitor = monitors?.find(m => m.id === data.monitor_id);
            const response = await api.post('/installs', {
                ...data,
                project_id: projectId,
                install_type: monitor?.monitor_type || 'Flow Monitor'
            });
            return response.data;
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['installs'] });
            reset();
            onClose();
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

                <h2 className="text-xl font-bold text-gray-900 mb-6">Add Install</h2>

                <form onSubmit={handleSubmit((data) => mutate(data))} className="space-y-4">
                    <div className="grid grid-cols-2 gap-4">
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">Site</label>
                            <select
                                {...register('site_id', { required: 'Site is required', valueAsNumber: true })}
                                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                            >
                                <option value="">Select a site...</option>
                                {filteredSites.map((site) => (
                                    <option key={site.id} value={site.id}>
                                        {site.site_id} - {site.site_type}
                                    </option>
                                ))}
                            </select>
                            {errors.site_id && <p className="text-red-500 text-xs mt-1">{errors.site_id.message}</p>}
                        </div>

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
                        <div className="bg-blue-50 p-4 rounded-lg space-y-4">
                            <h3 className="font-semibold text-blue-900">Flow Monitor Details</h3>

                            <div className="grid grid-cols-2 gap-4">
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

                            <div className="grid grid-cols-2 gap-4">
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

                            <div className="grid grid-cols-2 gap-4">
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

                    {selectedMonitor && selectedMonitor.monitor_type === 'Rain Gauge' && (
                        <div className="bg-green-50 p-4 rounded-lg space-y-4">
                            <h3 className="font-semibold text-green-900">Rain Gauge Details</h3>
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

                    <div className="flex justify-end gap-3 mt-6">
                        <button
                            type="button"
                            onClick={onClose}
                            className="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
                        >
                            Cancel
                        </button>
                        <button
                            type="submit"
                            disabled={isPending}
                            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors flex items-center gap-2"
                        >
                            {isPending && <Loader2 size={16} className="animate-spin" />}
                            Add Install
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
};

export default AddInstallModal;
