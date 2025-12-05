import React, { useState } from 'react';
import { X, AlertTriangle, Trash2, Calendar } from 'lucide-react';
import type { Install } from '../../api/hooks';

interface DeleteInstallModalProps {
    isOpen: boolean;
    onClose: () => void;
    install: Install;
    onDelete: () => void;
    onUninstall: (removalDate: string) => void;
}

const DeleteInstallModal: React.FC<DeleteInstallModalProps> = ({
    isOpen,
    onClose,
    install,
    onDelete,
    onUninstall,
}) => {
    const [removalDate, setRemovalDate] = useState(new Date().toISOString().split('T')[0]);
    const [showUninstallForm, setShowUninstallForm] = useState(false);

    if (!isOpen) return null;

    const handleUninstall = () => {
        onUninstall(removalDate);
        onClose();
    };

    const handleDelete = () => {
        onDelete();
        onClose();
    };

    return (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
            <div className="bg-white rounded-xl shadow-xl w-full max-w-md p-6 relative animate-in fade-in zoom-in duration-200">
                <button
                    onClick={onClose}
                    className="absolute top-4 right-4 text-gray-400 hover:text-gray-600"
                >
                    <X size={20} />
                </button>

                <div className="flex items-start gap-3 mb-4">
                    <div className="p-2 bg-amber-100 rounded-lg">
                        <AlertTriangle className="text-amber-600" size={24} />
                    </div>
                    <div>
                        <h2 className="text-xl font-bold text-gray-900">Remove Install</h2>
                        <p className="text-sm text-gray-600 mt-1">
                            {install.install_id} - {install.install_type}
                        </p>
                    </div>
                </div>

                <div className="bg-amber-50 border border-amber-200 rounded-lg p-4 mb-6">
                    <p className="text-sm text-amber-900 font-medium mb-2">
                        ⚠️ Choose how to remove this install:
                    </p>
                    <ul className="text-sm text-amber-800 space-y-1 ml-4">
                        <li><strong>Uninstall:</strong> Mark as removed but keep historical data</li>
                        <li><strong>Delete:</strong> Permanently remove all data (cannot be undone)</li>
                    </ul>
                </div>

                {!showUninstallForm ? (
                    <div className="space-y-3">
                        <button
                            onClick={() => setShowUninstallForm(true)}
                            className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                        >
                            <Calendar size={18} />
                            Uninstall (Recommended)
                        </button>

                        <button
                            onClick={handleDelete}
                            className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
                        >
                            <Trash2 size={18} />
                            Delete Permanently
                        </button>

                        <button
                            onClick={onClose}
                            className="w-full px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
                        >
                            Cancel
                        </button>
                    </div>
                ) : (
                    <div className="space-y-4">
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-2">
                                Removal Date
                            </label>
                            <input
                                type="date"
                                value={removalDate}
                                onChange={(e) => setRemovalDate(e.target.value)}
                                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                            />
                            <p className="text-xs text-gray-500 mt-1">
                                This will set the removal date but preserve all historical data
                            </p>
                        </div>

                        <div className="flex gap-3">
                            <button
                                onClick={() => setShowUninstallForm(false)}
                                className="flex-1 px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
                            >
                                Back
                            </button>
                            <button
                                onClick={handleUninstall}
                                className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                            >
                                Confirm Uninstall
                            </button>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
};

export default DeleteInstallModal;
