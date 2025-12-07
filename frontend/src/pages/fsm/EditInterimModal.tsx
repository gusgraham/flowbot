import React, { useState, useEffect } from 'react';
import { X, Calendar, Loader2 } from 'lucide-react';
import { useUpdateInterim } from '../../api/hooks';
import type { Interim } from '../../api/hooks';
import { useToast } from '../../contexts/ToastContext';

interface EditInterimModalProps {
    isOpen: boolean;
    onClose: () => void;
    interim: Interim;
}

const EditInterimModal: React.FC<EditInterimModalProps> = ({ isOpen, onClose, interim }) => {
    const [startDate, setStartDate] = useState('');
    const [endDate, setEndDate] = useState('');
    const { mutate: updateInterim, isPending } = useUpdateInterim();
    const { showToast } = useToast();

    useEffect(() => {
        if (interim) {
            // Convert ISO date to input format (YYYY-MM-DD)
            setStartDate(interim.start_date.split('T')[0]);
            setEndDate(interim.end_date.split('T')[0]);
        }
    }, [interim]);

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();

        if (!startDate || !endDate) {
            showToast('Please select both start and end dates', 'error');
            return;
        }

        if (new Date(endDate) < new Date(startDate)) {
            showToast('End date must be after start date', 'error');
            return;
        }

        updateInterim(
            { interimId: interim.id, start_date: startDate, end_date: endDate },
            {
                onSuccess: () => {
                    showToast('Interim updated successfully', 'success');
                    onClose();
                },
                onError: (err) => {
                    showToast(`Failed to update interim: ${err.message}`, 'error');
                },
            }
        );
    };

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
            <div className="bg-white rounded-xl shadow-xl w-full max-w-md mx-4">
                <div className="flex justify-between items-center p-6 border-b border-gray-100">
                    <h2 className="text-xl font-bold text-gray-900 flex items-center gap-2">
                        <Calendar size={20} className="text-purple-600" />
                        Edit Interim Period
                    </h2>
                    <button
                        onClick={onClose}
                        className="text-gray-400 hover:text-gray-600 transition-colors"
                    >
                        <X size={20} />
                    </button>
                </div>

                <form onSubmit={handleSubmit} className="p-6 space-y-4">
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                            Start Date
                        </label>
                        <input
                            type="date"
                            value={startDate}
                            onChange={(e) => setStartDate(e.target.value)}
                            className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-purple-500"
                            required
                        />
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                            End Date
                        </label>
                        <input
                            type="date"
                            value={endDate}
                            onChange={(e) => setEndDate(e.target.value)}
                            className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-purple-500"
                            required
                        />
                    </div>

                    <div className="flex justify-end gap-3 pt-4">
                        <button
                            type="button"
                            onClick={onClose}
                            className="px-4 py-2 text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
                        >
                            Cancel
                        </button>
                        <button
                            type="submit"
                            disabled={isPending}
                            className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 flex items-center gap-2 transition-colors"
                        >
                            {isPending && <Loader2 size={16} className="animate-spin" />}
                            Save Changes
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
};

export default EditInterimModal;
