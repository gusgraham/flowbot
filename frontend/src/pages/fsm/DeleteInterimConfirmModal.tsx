import React from 'react';
import { X, AlertTriangle, Loader2, Trash2 } from 'lucide-react';
import { useDeleteInterim } from '../../api/hooks';
import type { Interim } from '../../api/hooks';
import { useToast } from '../../contexts/ToastContext';

interface DeleteInterimModalProps {
    isOpen: boolean;
    onClose: () => void;
    interim: Interim;
}

const DeleteInterimModal: React.FC<DeleteInterimModalProps> = ({ isOpen, onClose, interim }) => {
    const { mutate: deleteInterim, isPending } = useDeleteInterim();
    const { showToast } = useToast();

    const handleDelete = () => {
        deleteInterim(interim.id, {
            onSuccess: () => {
                showToast('Interim deleted successfully', 'success');
                onClose();
            },
            onError: (err) => {
                showToast(`Failed to delete interim: ${err.message}`, 'error');
            },
        });
    };

    if (!isOpen) return null;

    const reviewCount = interim.review_count || 0;

    return (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
            <div className="bg-white rounded-xl shadow-xl w-full max-w-md mx-4">
                <div className="flex justify-between items-center p-6 border-b border-gray-100">
                    <h2 className="text-xl font-bold text-red-600 flex items-center gap-2">
                        <Trash2 size={20} />
                        Delete Interim
                    </h2>
                    <button
                        onClick={onClose}
                        className="text-gray-400 hover:text-gray-600 transition-colors"
                    >
                        <X size={20} />
                    </button>
                </div>

                <div className="p-6">
                    <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-4 flex gap-3">
                        <AlertTriangle className="text-red-500 shrink-0" size={24} />
                        <div>
                            <p className="font-medium text-red-800">Warning: This action cannot be undone</p>
                            <p className="text-sm text-red-600 mt-1">
                                Deleting this interim will permanently remove all associated reviews,
                                classifications, and annotations.
                            </p>
                        </div>
                    </div>

                    <div className="mb-4">
                        <p className="text-gray-700">
                            Are you sure you want to delete the interim period:
                        </p>
                        <p className="font-semibold text-gray-900 mt-2">
                            {new Date(interim.start_date).toLocaleDateString()} - {new Date(interim.end_date).toLocaleDateString()}
                        </p>
                        {reviewCount > 0 && (
                            <p className="text-sm text-gray-500 mt-2">
                                This will delete <span className="font-medium">{reviewCount} review(s)</span> and all associated data.
                            </p>
                        )}
                    </div>

                    <div className="flex justify-end gap-3">
                        <button
                            type="button"
                            onClick={onClose}
                            className="px-4 py-2 text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
                        >
                            Cancel
                        </button>
                        <button
                            onClick={handleDelete}
                            disabled={isPending}
                            className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50 flex items-center gap-2 transition-colors"
                        >
                            {isPending && <Loader2 size={16} className="animate-spin" />}
                            <Trash2 size={16} />
                            Delete Interim
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default DeleteInterimModal;
