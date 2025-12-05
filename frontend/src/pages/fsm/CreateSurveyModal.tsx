import React, { useState } from 'react';
import { X, Loader2 } from 'lucide-react';
import { useCreateProject, type ProjectCreate } from '../../api/hooks';

interface CreateSurveyModalProps {
    isOpen: boolean;
    onClose: () => void;
}

const CreateSurveyModal: React.FC<CreateSurveyModalProps> = ({ isOpen, onClose }) => {
    const createProject = useCreateProject();
    const [formData, setFormData] = useState<ProjectCreate>({
        job_number: '',
        name: '',
        client: '',
        client_job_ref: '',
    });

    if (!isOpen) return null;

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        try {
            await createProject.mutateAsync(formData);
            onClose();
            // Reset form
            setFormData({
                job_number: '',
                name: '',
                client: '',
                client_job_ref: '',
            });
        } catch (error) {
            console.error('Failed to create survey:', error);
        }
    };

    const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const { name, value } = e.target;
        setFormData(prev => ({ ...prev, [name]: value }));
    };

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50 backdrop-blur-sm">
            <div className="bg-white rounded-xl shadow-xl w-full max-w-md overflow-hidden">
                <div className="flex justify-between items-center p-6 border-b border-gray-100">
                    <h2 className="text-xl font-bold text-gray-900">Create New Survey</h2>
                    <button
                        onClick={onClose}
                        className="text-gray-400 hover:text-gray-600 transition-colors"
                    >
                        <X size={24} />
                    </button>
                </div>

                <form onSubmit={handleSubmit} className="p-6 space-y-4">
                    <div>
                        <label htmlFor="job_number" className="block text-sm font-medium text-gray-700 mb-1">
                            Job Number *
                        </label>
                        <input
                            type="text"
                            id="job_number"
                            name="job_number"
                            required
                            value={formData.job_number}
                            onChange={handleChange}
                            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all"
                            placeholder="e.g. J12345"
                        />
                    </div>

                    <div>
                        <label htmlFor="name" className="block text-sm font-medium text-gray-700 mb-1">
                            Job Name *
                        </label>
                        <input
                            type="text"
                            id="name"
                            name="name"
                            required
                            value={formData.name}
                            onChange={handleChange}
                            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all"
                            placeholder="e.g. City Center Flow Survey"
                        />
                    </div>

                    <div>
                        <label htmlFor="client" className="block text-sm font-medium text-gray-700 mb-1">
                            Client *
                        </label>
                        <input
                            type="text"
                            id="client"
                            name="client"
                            required
                            value={formData.client}
                            onChange={handleChange}
                            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all"
                            placeholder="e.g. Water Co."
                        />
                    </div>

                    <div>
                        <label htmlFor="client_job_ref" className="block text-sm font-medium text-gray-700 mb-1">
                            Client Job Ref
                        </label>
                        <input
                            type="text"
                            id="client_job_ref"
                            name="client_job_ref"
                            value={formData.client_job_ref}
                            onChange={handleChange}
                            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all"
                            placeholder="Optional"
                        />
                    </div>

                    <div className="pt-4 flex justify-end gap-3">
                        <button
                            type="button"
                            onClick={onClose}
                            className="px-4 py-2 text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors font-medium"
                        >
                            Cancel
                        </button>
                        <button
                            type="submit"
                            disabled={createProject.isPending}
                            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium flex items-center gap-2 disabled:opacity-70 disabled:cursor-not-allowed"
                        >
                            {createProject.isPending && <Loader2 size={18} className="animate-spin" />}
                            Create Survey
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
};

export default CreateSurveyModal;
