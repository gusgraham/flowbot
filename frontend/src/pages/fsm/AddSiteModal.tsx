import React from 'react';
import { useForm } from 'react-hook-form';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import api from '../../api/client';
import { X, Loader2 } from 'lucide-react';

interface AddSiteModalProps {
    isOpen: boolean;
    onClose: () => void;
    projectId: number;
}

interface SiteFormData {
    site_id: string;
    site_type: string;
    address?: string;
    mh_ref?: string;
    w3w?: string;
    easting?: number;
    northing?: number;
}

const AddSiteModal: React.FC<AddSiteModalProps> = ({ isOpen, onClose, projectId }) => {
    const { register, handleSubmit, reset, formState: { errors } } = useForm<SiteFormData>();
    const queryClient = useQueryClient();

    const { mutate, isPending } = useMutation({
        mutationFn: async (data: SiteFormData) => {
            const response = await api.post('/sites', {
                ...data,
                project_id: projectId
            });
            return response.data;
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['sites', projectId] });
            reset();
            onClose();
        },
    });

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
            <div className="bg-white rounded-xl shadow-xl w-full max-w-md p-6 relative animate-in fade-in zoom-in duration-200">
                <button
                    onClick={onClose}
                    className="absolute top-4 right-4 text-gray-400 hover:text-gray-600"
                >
                    <X size={20} />
                </button>

                <h2 className="text-xl font-bold text-gray-900 mb-6">Add New Site</h2>

                <form onSubmit={handleSubmit((data) => mutate(data))} className="space-y-4">
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">Site ID</label>
                        <input
                            {...register('site_id', { required: 'Site ID is required' })}
                            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                            placeholder="e.g. MH123"
                        />
                        {errors.site_id && <p className="text-red-500 text-xs mt-1">{errors.site_id.message}</p>}
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">Site Type</label>
                        <select
                            {...register('site_type')}
                            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                        >
                            <option value="Flow Monitor">Flow Monitor</option>
                            <option value="Rain Gauge">Rain Gauge</option>
                            <option value="Pump Station">Pump Station</option>
                        </select>
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">Address / Location</label>
                        <input
                            {...register('address')}
                            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                            placeholder="Optional"
                        />
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">MH Ref</label>
                            <input
                                {...register('mh_ref')}
                                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                                placeholder="Optional"
                            />
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">What3Words</label>
                            <input
                                {...register('w3w')}
                                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                                placeholder="///word.word.word"
                            />
                        </div>
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
                            Add Site
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
};

export default AddSiteModal;
