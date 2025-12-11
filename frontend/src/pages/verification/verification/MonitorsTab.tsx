import React, { useState } from 'react';
import { Plus, Trash2, MapPin, AlertTriangle, Droplets } from 'lucide-react';
import {
    useVerificationMonitors,
    useCreateVerificationMonitor,
    useUpdateVerificationMonitor,
    useDeleteVerificationMonitor,
} from '../../../api/hooks';
import type { VerificationFlowMonitor } from '../../../api/hooks';

interface MonitorsTabProps {
    projectId: number;
}

export default function MonitorsTab({ projectId }: MonitorsTabProps) {
    const { data: monitors, isLoading } = useVerificationMonitors(projectId);
    const createMonitor = useCreateVerificationMonitor();
    const updateMonitor = useUpdateVerificationMonitor();
    const deleteMonitor = useDeleteVerificationMonitor();

    // State for new monitor form
    const [showNewForm, setShowNewForm] = useState(false);
    const [newMonitor, setNewMonitor] = useState({ name: '', icm_node_reference: '' });

    const handleCreate = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!newMonitor.name.trim()) return;

        await createMonitor.mutateAsync({
            projectId,
            monitor: newMonitor
        });

        setNewMonitor({ name: '', icm_node_reference: '' });
        setShowNewForm(false);
    };

    const toggleCritical = (monitor: VerificationFlowMonitor) => {
        updateMonitor.mutate({
            monitorId: monitor.id,
            update: { is_critical: !monitor.is_critical },
            projectId
        });
    };

    const toggleSurcharged = (monitor: VerificationFlowMonitor) => {
        updateMonitor.mutate({
            monitorId: monitor.id,
            update: { is_surcharged: !monitor.is_surcharged },
            projectId
        });
    };

    if (isLoading) {
        return <div className="text-gray-500">Loading monitors...</div>;
    }

    return (
        <div className="space-y-6">
            {/* New Monitor Button */}
            {!showNewForm && (
                <button
                    onClick={() => setShowNewForm(true)}
                    className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
                >
                    <Plus size={18} /> Add Monitor
                </button>
            )}

            {/* New Monitor Form */}
            {showNewForm && (
                <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
                    <h3 className="font-semibold text-gray-900 mb-4">New Flow Monitor</h3>
                    <form onSubmit={handleCreate} className="space-y-4">
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">Monitor Name</label>
                                <input
                                    type="text"
                                    value={newMonitor.name}
                                    onChange={(e) => setNewMonitor({ ...newMonitor, name: e.target.value })}
                                    placeholder="e.g., F01, FM_01"
                                    className="w-full border-gray-300 rounded-md shadow-sm focus:ring-green-500 focus:border-green-500"
                                    required
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">ICM Link Reference</label>
                                <input
                                    type="text"
                                    value={newMonitor.icm_node_reference}
                                    onChange={(e) => setNewMonitor({ ...newMonitor, icm_node_reference: e.target.value })}
                                    placeholder="e.g., SJ24658202.1"
                                    className="w-full border-gray-300 rounded-md shadow-sm focus:ring-green-500 focus:border-green-500"
                                />
                            </div>
                        </div>
                        <div className="flex gap-2">
                            <button
                                type="submit"
                                disabled={createMonitor.isPending}
                                className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50"
                            >
                                {createMonitor.isPending ? 'Creating...' : 'Create Monitor'}
                            </button>
                            <button
                                type="button"
                                onClick={() => setShowNewForm(false)}
                                className="px-4 py-2 text-gray-600 hover:text-gray-900"
                            >
                                Cancel
                            </button>
                        </div>
                    </form>
                </div>
            )}

            {/* Monitors List */}
            {monitors && monitors.length > 0 ? (
                <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-gray-200">
                        <thead className="bg-gray-50">
                            <tr>
                                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Monitor Name</th>
                                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">ICM Link</th>
                                <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">Critical</th>
                                <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">Surcharged</th>
                                <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
                            </tr>
                        </thead>
                        <tbody className="bg-white divide-y divide-gray-200">
                            {monitors.map((monitor: VerificationFlowMonitor) => (
                                <tr key={monitor.id} className="hover:bg-gray-50">
                                    <td className="px-4 py-3 whitespace-nowrap">
                                        <div className="flex items-center gap-2">
                                            <MapPin size={16} className="text-gray-400" />
                                            <span className="font-medium text-gray-900">{monitor.name}</span>
                                        </div>
                                    </td>
                                    <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-500">
                                        {monitor.icm_node_reference || '-'}
                                    </td>
                                    <td className="px-4 py-3 text-center">
                                        <button
                                            onClick={() => toggleCritical(monitor)}
                                            className={`inline-flex items-center gap-1 px-2 py-1 text-xs rounded-full ${monitor.is_critical
                                                    ? 'bg-red-100 text-red-700'
                                                    : 'bg-gray-100 text-gray-500 hover:bg-gray-200'
                                                }`}
                                        >
                                            <AlertTriangle size={12} />
                                            {monitor.is_critical ? 'Critical' : 'Normal'}
                                        </button>
                                    </td>
                                    <td className="px-4 py-3 text-center">
                                        <button
                                            onClick={() => toggleSurcharged(monitor)}
                                            className={`inline-flex items-center gap-1 px-2 py-1 text-xs rounded-full ${monitor.is_surcharged
                                                    ? 'bg-blue-100 text-blue-700'
                                                    : 'bg-gray-100 text-gray-500 hover:bg-gray-200'
                                                }`}
                                        >
                                            <Droplets size={12} />
                                            {monitor.is_surcharged ? 'Yes' : 'No'}
                                        </button>
                                    </td>
                                    <td className="px-4 py-3 text-center">
                                        <button
                                            onClick={() => deleteMonitor.mutate({ monitorId: monitor.id, projectId })}
                                            className="p-1.5 text-red-500 hover:bg-red-50 rounded"
                                            title="Delete Monitor"
                                        >
                                            <Trash2 size={16} />
                                        </button>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            ) : (
                <div className="text-center py-12 bg-gray-50 rounded-lg border-2 border-dashed border-gray-200">
                    <MapPin className="mx-auto text-gray-400 mb-3" size={48} />
                    <p className="text-gray-500 mb-2">No monitors defined yet</p>
                    <p className="text-sm text-gray-400">Monitors are automatically created when importing traces, or add them manually.</p>
                </div>
            )}

            {/* Legend */}
            <div className="bg-gray-50 rounded-lg p-4">
                <h4 className="font-medium text-gray-700 mb-2">Tolerance Settings</h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm text-gray-600">
                    <div className="flex items-start gap-2">
                        <AlertTriangle size={16} className="text-red-500 mt-0.5" />
                        <div>
                            <span className="font-medium">Critical:</span> Tighter tolerances applied (±10% peak, ±10% volume)
                        </div>
                    </div>
                    <div className="flex items-start gap-2">
                        <Droplets size={16} className="text-blue-500 mt-0.5" />
                        <div>
                            <span className="font-medium">Surcharged:</span> Asymmetric depth tolerance (+0.5m / -0.1m)
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
