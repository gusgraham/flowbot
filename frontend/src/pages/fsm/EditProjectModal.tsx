import React, { useEffect, useState } from 'react';
import { useForm } from 'react-hook-form';
import {
    useUpdateProject,
    useProjectCollaborators,
    useAddCollaborator,
    useRemoveCollaborator,
    useCurrentUser
} from '../../api/hooks';
import type { Project, ProjectCreate } from '../../api/hooks';
import { X, Loader2, Users, Settings, Trash2, Plus } from 'lucide-react';

interface EditProjectModalProps {
    isOpen: boolean;
    onClose: () => void;
    project: Project;
}

const EditProjectModal: React.FC<EditProjectModalProps> = ({ isOpen, onClose, project }) => {
    const { register, handleSubmit, reset, formState: { errors } } = useForm<ProjectCreate>();
    const { mutate: updateProject, isPending } = useUpdateProject();
    const { data: currentUser } = useCurrentUser();

    // Collaborative Hooks
    const { data: collaborators, isLoading: loadingCollabs } = useProjectCollaborators(project.id);
    const addCollaborator = useAddCollaborator();
    const removeCollaborator = useRemoveCollaborator();

    const [activeTab, setActiveTab] = useState<'general' | 'collaborators'>('general');
    const [newCollabEmail, setNewCollabEmail] = useState('');

    const isOwner = currentUser?.id === project.owner_id || currentUser?.is_superuser;

    useEffect(() => {
        if (project) {
            reset({
                job_number: project.job_number,
                name: project.name,
                client: project.client,
                client_job_ref: project.client_job_ref,
                survey_start_date: project.survey_start_date ? project.survey_start_date.toString().split('T')[0] : undefined,
                survey_end_date: project.survey_end_date ? project.survey_end_date.toString().split('T')[0] : undefined,
                default_download_path: project.default_download_path
            });
        }
    }, [project, reset, isOpen]);

    const onSubmit = (data: ProjectCreate) => {
        // Sanitize data: convert empty strings to null so they are cleared in backend
        const cleanedData = {
            ...data,
            survey_start_date: data.survey_start_date === '' ? null : data.survey_start_date,
            survey_end_date: data.survey_end_date === '' ? null : data.survey_end_date,
            client_job_ref: data.client_job_ref === '' ? null : data.client_job_ref,
            default_download_path: data.default_download_path === '' ? null : data.default_download_path
        };

        updateProject({ id: project.id, updates: cleanedData }, {
            onSuccess: () => {
                onClose();
            }
        });
    };

    const handleAddCollaborator = (e: React.FormEvent) => {
        e.preventDefault();
        if (!newCollabEmail) return;
        addCollaborator.mutate({ projectId: project.id, usernameOrEmail: newCollabEmail }, {
            onSuccess: () => {
                setNewCollabEmail('');
            },
            onError: () => {
                alert("Failed to add collaborator. User may not exist.");
            }
        });
    };

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
            <div className="bg-white rounded-xl shadow-xl w-full max-w-lg p-6 relative animate-in fade-in zoom-in duration-200 flex flex-col max-h-[90vh]">
                <button
                    onClick={onClose}
                    className="absolute top-4 right-4 text-gray-400 hover:text-gray-600"
                >
                    <X size={20} />
                </button>

                <h2 className="text-xl font-bold text-gray-900 mb-6 flex items-center gap-2">
                    Edit Project
                    <span className="text-sm font-normal text-gray-500 bg-gray-100 px-2 py-1 rounded">
                        {project.job_number}
                    </span>
                </h2>

                {/* Tabs */}
                {isOwner && (
                    <div className="flex border-b border-gray-200 mb-6">
                        <button
                            onClick={() => setActiveTab('general')}
                            className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors flex items-center gap-2 ${activeTab === 'general'
                                ? 'border-blue-600 text-blue-600'
                                : 'border-transparent text-gray-500 hover:text-gray-700'
                                }`}
                        >
                            <Settings size={16} />
                            General
                        </button>
                        <button
                            onClick={() => setActiveTab('collaborators')}
                            className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors flex items-center gap-2 ${activeTab === 'collaborators'
                                ? 'border-blue-600 text-blue-600'
                                : 'border-transparent text-gray-500 hover:text-gray-700'
                                }`}
                        >
                            <Users size={16} />
                            Collaborators
                        </button>
                    </div>
                )}

                <div className="flex-1 overflow-y-auto pr-2">
                    {activeTab === 'general' ? (
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

                            <div className="flex justify-end gap-3 pt-4">
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
                    ) : (
                        <div className="space-y-6">
                            <div className="bg-blue-50 p-4 rounded-lg flex items-start gap-3">
                                <Users className="text-blue-600 mt-1" size={20} />
                                <div>
                                    <h3 className="text-sm font-semibold text-blue-900">Manage Access</h3>
                                    <p className="text-sm text-blue-700">Collaborators can view and edit this project, but cannot delete it.</p>
                                </div>
                            </div>

                            {/* Add Collaborator */}
                            <form onSubmit={handleAddCollaborator} className="flex gap-2">
                                <input
                                    type="text"
                                    placeholder="Enter username or email"
                                    value={newCollabEmail}
                                    onChange={(e) => setNewCollabEmail(e.target.value)}
                                    className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                                />
                                <button
                                    type="submit"
                                    disabled={addCollaborator.isPending}
                                    className="px-4 py-2 bg-gray-900 text-white rounded-lg hover:bg-gray-800 transition-colors flex items-center gap-2 whitespace-nowrap"
                                >
                                    {addCollaborator.isPending ? <Loader2 size={16} className="animate-spin" /> : <Plus size={16} />}
                                    Add
                                </button>
                            </form>

                            {/* List */}
                            <div className="space-y-2">
                                <h3 className="text-sm font-medium text-gray-700">Current Collaborators</h3>
                                {loadingCollabs ? (
                                    <div className="text-center py-4 text-gray-500">Loading...</div>
                                ) : collaborators?.length === 0 ? (
                                    <div className="text-center py-8 text-gray-500 bg-gray-50 rounded-lg border border-dashed border-gray-300">
                                        No collaborators yet
                                    </div>
                                ) : (
                                    <div className="space-y-2">
                                        {collaborators?.map(user => (
                                            <div key={user.id} className="flex items-center justify-between p-3 bg-white border border-gray-200 rounded-lg shadow-sm">
                                                <div className="flex items-center gap-3">
                                                    <div className="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center text-blue-600 font-bold">
                                                        {user.username.substring(0, 2).toUpperCase()}
                                                    </div>
                                                    <div>
                                                        <div className="text-sm font-medium text-gray-900">{user.full_name || user.username}</div>
                                                        <div className="text-xs text-gray-500">{user.email || user.username}</div>
                                                    </div>
                                                </div>
                                                <button
                                                    onClick={() => removeCollaborator.mutate({ projectId: project.id, userId: user.id })}
                                                    className="p-2 text-gray-400 hover:text-red-500 transition-colors"
                                                    title="Remove Access"
                                                >
                                                    <Trash2 size={16} />
                                                </button>
                                            </div>
                                        ))}
                                    </div>
                                )}
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

export default EditProjectModal;
