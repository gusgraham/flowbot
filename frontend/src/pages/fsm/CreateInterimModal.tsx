import React, { useState } from 'react';
import { X, Calendar, Loader2 } from 'lucide-react';
import { useCreateInterim } from '../../api/hooks';
import { useToast } from '../../contexts/ToastContext';

interface CreateInterimModalProps {
    isOpen: boolean;
    onClose: () => void;
    projectId: number;
}

const CreateInterimModal: React.FC<CreateInterimModalProps> = ({ isOpen, onClose, projectId }) => {
    const [startDate, setStartDate] = useState('');
    const [endDate, setEndDate] = useState('');
    const { mutate: createInterim, isPending } = useCreateInterim();
    const { showToast } = useToast();

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

        createInterim(
            { projectId, startDate, endDate },
            {
                onSuccess: () => {
                    showToast('Interim created successfully', 'success');
                    onClose();
                    setStartDate('');
                    setEndDate('');
                },
                onError: (err) => {
                    showToast(`Failed to create interim: ${err.message}`, 'error');
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
                        <Calendar size={20} className="text-blue-600" />
                        Create New Interim
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
                            className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
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
                            className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                            required
                        />
                    </div>

                    <p className="text-sm text-gray-500">
                        An interim review will be created for each active install in this project.
                    </p>

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
                            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 flex items-center gap-2 transition-colors"
                        >
                            {isPending && <Loader2 size={16} className="animate-spin" />}
                            Create Interim
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
};

export default CreateInterimModal;
