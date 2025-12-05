import React, { useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { useUpdateProject } from '../../api/hooks';
import type { Project, ProjectCreate } from '../../api/hooks';
import { X, Loader2 } from 'lucide-react';

interface EditProjectModalProps {
    isOpen: boolean;
    onClose: () => void;
    project: Project;
}

const EditProjectModal: React.FC<EditProjectModalProps> = ({ isOpen, onClose, project }) => {
    const { register, handleSubmit, reset, formState: { errors } } = useForm<ProjectCreate>();
    const { mutate: updateProject, isPending } = useUpdateProject();

    useEffect(() => {
        if (project) {
            reset({
                job_number: project.job_number,
                name: project.name,
                client: project.client,
                client_job_ref: project.client_job_ref,
                survey_start_date: project.survey_start_date,
                survey_end_date: project.survey_end_date,
                default_download_path: project.default_download_path
            });
        }
    }, [project, reset, isOpen]);

    const onSubmit = (data: ProjectCreate) => {
        updateProject({ id: project.id, updates: data }, {
            onSuccess: () => {
                onClose();
            }
        });
    };

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

                <h2 className="text-xl font-bold text-gray-900 mb-6">Edit Project</h2>

                <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">Job Number</label>
                        <input
                            {...register('job_number', { required: 'Job Number is required' })}
                            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                        />
                        {errors.job_number && <p className="text-red-500 text-xs mt-1">{errors.job_number.message}</p>}
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">Job Name</label>
                        <input
                            {...register('name', { required: 'Job Name is required' })}
                            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                        />
                        {errors.name && <p className="text-red-500 text-xs mt-1">{errors.name.message}</p>}
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">Client</label>
                        <input
                            {...register('client', { required: 'Client is required' })}
                            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                        />
                        {errors.client && <p className="text-red-500 text-xs mt-1">{errors.client.message}</p>}
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">Client Job Ref</label>
                        <input
                            {...register('client_job_ref')}
                            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                        />
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">Default Ingestion Path</label>
                        <input
                            {...register('default_download_path')}
                            placeholder="e.g. C:\SurveyData\ProjectData"
                            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                        />
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">Start Date</label>
                            <input
                                type="date"
                                {...register('survey_start_date')}
                                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                            />
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">End Date</label>
                            <input
                                type="date"
                                {...register('survey_end_date')}
                                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
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
                            Save Changes
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
};

export default EditProjectModal;
