import React, { useState } from 'react';
import { useForm } from 'react-hook-form';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import api from '../../api/client';
import { X, Loader2 } from 'lucide-react';

interface AddMonitorModalProps {
    isOpen: boolean;
    onClose: () => void;
    projectId: number;
}

interface MonitorFormData {
    monitor_asset_id: string;
    monitor_type: string;
    monitor_sub_type: string;
    pmac_id?: string;
}

const MONITOR_SUBTYPES: Record<string, string[]> = {
    'Flow Monitor': ['Detec', 'Sigma', 'MSFM', 'ADS', 'Ultrasonic D/O', 'Pressure D/O'],
    'Rain Gauge': ['Casella/Technolog', 'Hobo', 'Telemetered'],
    'Pump Logger': ['Hobo']
};

const AddMonitorModal: React.FC<AddMonitorModalProps> = ({ isOpen, onClose, projectId }) => {
    const { register, handleSubmit, reset, watch, setValue, formState: { errors } } = useForm<MonitorFormData>();
    const queryClient = useQueryClient();
    const [monitorType, setMonitorType] = useState('Flow Monitor');

    const watchedType = watch('monitor_type', 'Flow Monitor');

    // Update subtype options when monitor type changes
    React.useEffect(() => {
        const subtypes = MONITOR_SUBTYPES[watchedType] || [];
        if (subtypes.length > 0) {
            setValue('monitor_sub_type', subtypes[0]);
        }
    }, [watchedType, setValue]);

    const { mutate, isPending } = useMutation({
        mutationFn: async (data: MonitorFormData) => {
            const response = await api.post('/monitors', {
                ...data,
                project_id: projectId
            });
            return response.data;
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['monitors', projectId] });
            reset();
            onClose();
        },
    });

    if (!isOpen) return null;

    const subtypeOptions = MONITOR_SUBTYPES[watchedType] || [];

    return (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
            <div className="bg-white rounded-xl shadow-xl w-full max-w-md p-6 relative animate-in fade-in zoom-in duration-200">
                <button
                    onClick={onClose}
                    className="absolute top-4 right-4 text-gray-400 hover:text-gray-600"
                >
                    <X size={20} />
                </button>

                <h2 className="text-xl font-bold text-gray-900 mb-6">Add Monitor</h2>

                <form onSubmit={handleSubmit((data) => mutate(data))} className="space-y-4">
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">Monitor Asset ID</label>
                        <input
                            {...register('monitor_asset_id', { required: 'Monitor Asset ID is required' })}
                            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                            placeholder="e.g. FM001"
                        />
                        {errors.monitor_asset_id && <p className="text-red-500 text-xs mt-1">{errors.monitor_asset_id.message}</p>}
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">Monitor Type</label>
                        <select
                            {...register('monitor_type')}
                            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                        >
                            <option value="Flow Monitor">Flow Monitor</option>
                            <option value="Rain Gauge">Rain Gauge</option>
                            <option value="Pump Logger">Pump Logger</option>
                        </select>
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">Sub-Type</label>
                        <select
                            {...register('monitor_sub_type')}
                            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                        >
                            {subtypeOptions.map((subtype) => (
                                <option key={subtype} value={subtype}>{subtype}</option>
                            ))}
                        </select>
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">PMAC ID (Optional)</label>
                        <input
                            {...register('pmac_id')}
                            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                            placeholder="Optional"
                        />
                    </div>

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
                            Add Monitor
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
};

export default AddMonitorModal;
