import React, { useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { useUpdateInstall } from '../../api/hooks';
import type { Install, Site, Monitor } from '../../api/hooks';
import { X, Loader2 } from 'lucide-react';

interface EditInstallModalProps {
    isOpen: boolean;
    onClose: () => void;
    install: Install;
    sites: Site[];
    monitors: Monitor[];
}

interface InstallFormData {
    install_id: string;
    install_date: string;
    removal_date?: string;
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
const RG_POSITIONS = ["Ground", "Roof (First Floor)", "Roof (Higher)", "Post"];

const EditInstallModal: React.FC<EditInstallModalProps> = ({ isOpen, onClose, install, sites, monitors }) => {
    const { register, handleSubmit, reset, formState: { errors } } = useForm<InstallFormData>({
        defaultValues: {
            install_id: install.install_id,
            install_date: install.install_date ? new Date(install.install_date).toISOString().split('T')[0] : '',
            removal_date: install.removal_date ? new Date(install.removal_date).toISOString().split('T')[0] : undefined,
            fm_pipe_shape: install.fm_pipe_shape,
            fm_pipe_height_mm: install.fm_pipe_height_mm,
            fm_pipe_width_mm: install.fm_pipe_width_mm,
            fm_pipe_letter: install.fm_pipe_letter,
            fm_pipe_depth_to_invert_mm: install.fm_pipe_depth_to_invert_mm,
            fm_sensor_offset_mm: install.fm_sensor_offset_mm,
            rg_position: install.rg_position
        }
    });

    const { mutate, isPending } = useUpdateInstall();

    // Find associated objects
    const associatedSite = sites.find(s => s.id === install.site_id);
    const associatedMonitor = monitors.find(m => m.id === install.monitor_id);

    useEffect(() => {
        if (isOpen && install) {
            reset({
                install_id: install.install_id,
                install_date: install.install_date ? new Date(install.install_date).toISOString().split('T')[0] : '',
                removal_date: install.removal_date ? new Date(install.removal_date).toISOString().split('T')[0] : undefined,
                fm_pipe_shape: install.fm_pipe_shape,
                fm_pipe_height_mm: install.fm_pipe_height_mm,
                fm_pipe_width_mm: install.fm_pipe_width_mm,
                fm_pipe_letter: install.fm_pipe_letter,
                fm_pipe_depth_to_invert_mm: install.fm_pipe_depth_to_invert_mm,
                fm_sensor_offset_mm: install.fm_sensor_offset_mm,
                rg_position: install.rg_position
            });
        }
    }, [isOpen, install, reset]);

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

                <h2 className="text-xl font-bold text-gray-900 mb-6">Edit Install</h2>

                <form onSubmit={handleSubmit((data) => mutate({
                    installId: install.id,
                    ...data,
                    removal_date: data.removal_date || null
                }, {
                    onSuccess: () => onClose()
                }))} className="space-y-4">

                    {/* Read-only info */}
                    <div className="bg-gray-50 p-4 rounded-lg grid grid-cols-2 gap-4 mb-4">
                        <div>
                            <span className="block text-xs text-gray-500 uppercase font-semibold">Monitor</span>
                            <span className="font-medium text-gray-700">{associatedMonitor?.monitor_asset_id || install.monitor_id}</span>
                            <p className="text-xs text-gray-400 mt-1">To change monitor, create a new install.</p>
                        </div>
                        <div>
                            <span className="block text-xs text-gray-500 uppercase font-semibold">Site</span>
                            <span className="font-medium text-gray-700">{associatedSite?.site_id || install.site_id}</span>
                            <p className="text-xs text-gray-400 mt-1">To change site, create a new install.</p>
                        </div>
                    </div>


                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">Install ID / Label</label>
                        <input
                            type="text"
                            {...register('install_id', { required: 'Install ID is required' })}
                            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                        />
                        {errors.install_id && <p className="text-red-500 text-xs mt-1">{errors.install_id.message}</p>}
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">Install Date</label>
                            <input
                                type="date"
                                {...register('install_date', { required: 'Install date is required' })}
                                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                            />
                            {errors.install_date && <p className="text-red-500 text-xs mt-1">{errors.install_date.message}</p>}
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">Removal Date</label>
                            <input
                                type="date"
                                {...register('removal_date')}
                                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                            />
                        </div>
                    </div>

                    {install.install_type === 'Flow Monitor' && (
                        <div className="bg-blue-50 p-4 rounded-lg space-y-4">
                            <h3 className="font-semibold text-blue-900">Flow Monitor Details</h3>
                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-1">Pipe Identifier</label>
                                    <select {...register('fm_pipe_letter')} className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500">
                                        <option value="">Select identifier...</option>
                                        <optgroup label="Incoming">{['A', 'B', 'C', 'D', 'E', 'F', 'G'].map(l => <option key={l} value={l}>{l}</option>)}</optgroup>
                                        <optgroup label="Outgoing">{['X', 'Y', 'Z'].map(l => <option key={l} value={l}>{l}</option>)}</optgroup>
                                    </select>
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-1">Pipe Shape</label>
                                    <select {...register('fm_pipe_shape')} className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500">
                                        {PIPE_SHAPES.map(shape => <option key={shape} value={shape}>{shape}</option>)}
                                    </select>
                                </div>
                            </div>
                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-1">Height (mm)</label>
                                    <input type="number" {...register('fm_pipe_height_mm', { valueAsNumber: true })} className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500" />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-1">Width (mm)</label>
                                    <input type="number" {...register('fm_pipe_width_mm', { valueAsNumber: true })} className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500" />
                                </div>
                            </div>
                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-1">Depth to Invert (mm)</label>
                                    <input type="number" {...register('fm_pipe_depth_to_invert_mm', { valueAsNumber: true })} className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500" />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-1">Sensor Offset (mm)</label>
                                    <input type="number" {...register('fm_sensor_offset_mm', { valueAsNumber: true })} className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500" />
                                </div>
                            </div>
                        </div>
                    )}

                    {install.install_type === 'Rain Gauge' && (
                        <div className="bg-green-50 p-4 rounded-lg space-y-4">
                            <h3 className="font-semibold text-green-900">Rain Gauge Details</h3>
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">Position</label>
                                <select {...register('rg_position')} className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500">
                                    {RG_POSITIONS.map(pos => <option key={pos} value={pos}>{pos}</option>)}
                                </select>
                            </div>
                        </div>
                    )}

                    <div className="flex justify-end gap-3 mt-6">
                        <button type="button" onClick={onClose} className="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-lg transition-colors">Cancel</button>
                        <button type="submit" disabled={isPending} className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors flex items-center gap-2">
                            {isPending && <Loader2 size={16} className="animate-spin" />}
                            Save Changes
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
};

export default EditInstallModal;
