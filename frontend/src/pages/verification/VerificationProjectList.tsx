import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
    useVerificationProjects, useUpdateVerificationProject, useDeleteVerificationProject,
    useVerificationProjectCollaborators, useAddVerificationCollaborator, useRemoveVerificationCollaborator,
    useCurrentUser
} from '../../api/hooks';
import { CheckCircle, ArrowRight, Loader2, Plus, Pencil, Trash2, X, Settings, Users } from 'lucide-react';
import CreateVerificationProjectModal from './CreateVerificationProjectModal';
import CollaboratorsPanel from '../../components/CollaboratorsPanel';

const VerificationProjectList: React.FC = () => {
    const { data: projects, isLoading, error } = useVerificationProjects();
    const updateProject = useUpdateVerificationProject();
    const deleteProject = useDeleteVerificationProject();
    const { data: currentUser } = useCurrentUser();

    const [isModalOpen, setIsModalOpen] = useState(false);
    const [editingProject, setEditingProject] = useState<any>(null);
    const [activeTab, setActiveTab] = useState<'general' | 'collaborators'>('general');

    // Form state for editing
    const [formData, setFormData] = useState({
        name: '',
        client: '',
        job_number: '',
        model_name: '',
        description: ''
    });

    // Collaborator hooks
    const { data: collaborators, isLoading: loadingCollabs } = useVerificationProjectCollaborators(editingProject?.id || 0);
    const addCollaborator = useAddVerificationCollaborator();
    const removeCollaborator = useRemoveVerificationCollaborator();

    const isOwner = currentUser?.is_superuser || currentUser?.role === 'Admin' ||
        editingProject?.owner_id === currentUser?.id;

    // Update form when editing project changes
    useEffect(() => {
        if (editingProject) {
            setFormData({
                name: editingProject.name || '',
                client: editingProject.client || '',
                job_number: editingProject.job_number || '',
                model_name: editingProject.model_name || '',
                description: editingProject.description || ''
            });
        }
    }, [editingProject]);

    const handleEditClick = (e: React.MouseEvent, project: any) => {
        e.preventDefault();
        e.stopPropagation();
        setEditingProject(project);
        setActiveTab('general');
    };

    const handleDelete = (e: React.MouseEvent, projectId: number, projectName: string) => {
        e.preventDefault();
        e.stopPropagation();
        if (confirm(`Delete project "${projectName}"? This will permanently delete all associated data.`)) {
            deleteProject.mutate(projectId);
        }
    };

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        if (!editingProject) return;

        updateProject.mutate({ id: editingProject.id, data: formData }, {
            onSuccess: () => {
                setEditingProject(null);
            }
        });
    };

    const handleAddCollaborator = async (username: string) => {
        if (!editingProject?.id) return;
        await addCollaborator.mutateAsync({ projectId: editingProject.id, username });
    };

    const handleRemoveCollaborator = (userId: number) => {
        if (!editingProject?.id) return;
        removeCollaborator.mutate({ projectId: editingProject.id, userId });
    };

    if (isLoading) {
        return (
            <div className="flex justify-center items-center h-64">
                <Loader2 className="animate-spin text-green-500" size={32} />
            </div>
        );
    }

    if (error) {
        return (
            <div className="bg-red-50 border border-red-200 text-red-600 p-4 rounded-lg">
                Error loading projects. Please try again.
            </div>
        );
    }

    return (
        <div>
            <div className="flex justify-between items-center mb-8">
                <div>
                    <h1 className="text-2xl font-bold text-gray-900">Verification Projects</h1>
                    <p className="text-gray-500 mt-1">Select a project to verify model results against observed data.</p>
                </div>
                <button
                    onClick={() => setIsModalOpen(true)}
                    className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 transition-colors flex items-center"
                >
                    <Plus size={20} className="mr-2" />
                    New Project
                </button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {projects?.map((project) => (
                    <Link
                        key={project.id}
                        to={`/verification/${project.id}`}
                        className="block bg-white border border-gray-200 rounded-xl p-6 hover:shadow-md transition-shadow group"
                    >
                        <div className="flex items-start justify-between mb-4">
                            <div className="p-3 bg-green-50 text-green-600 rounded-lg">
                                <CheckCircle size={24} />
                            </div>
                            <div className="flex items-center gap-2">
                                <span className="text-xs font-medium bg-gray-100 text-gray-600 px-2 py-1 rounded-full">
                                    {project.job_number}
                                </span>
                                <button
                                    onClick={(e) => handleEditClick(e, project)}
                                    className="p-1 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded transition"
                                    title="Edit project"
                                >
                                    <Pencil size={16} />
                                </button>
                                <button
                                    onClick={(e) => handleDelete(e, project.id, project.name)}
                                    disabled={deleteProject.isPending}
                                    className="p-1 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded transition"
                                    title="Delete project"
                                >
                                    <Trash2 size={16} />
                                </button>
                            </div>
                        </div>

                        <h3 className="text-lg font-bold text-gray-900 mb-1">{project.name}</h3>
                        <p className="text-sm text-gray-500 mb-4">{project.client}</p>

                        <div className="flex items-center text-green-600 text-sm font-medium">
                            Open Verification
                            <ArrowRight size={16} className="ml-1 group-hover:translate-x-1 transition-transform" />
                        </div>
                    </Link>
                ))}

                {projects?.length === 0 && (
                    <div className="col-span-full text-center py-12 bg-gray-50 rounded-xl border border-dashed border-gray-300">
                        <p className="text-gray-500 mb-4">No verification projects found.</p>
                        <button
                            onClick={() => setIsModalOpen(true)}
                            className="text-green-600 font-medium hover:text-green-700"
                        >
                            Create your first project
                        </button>
                    </div>
                )}
            </div>

            <CreateVerificationProjectModal
                isOpen={isModalOpen}
                onClose={() => setIsModalOpen(false)}
            />

            {/* Edit Project Modal with Settings + Collaborators tabs */}
            {editingProject && (
                <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
                    <div className="bg-white rounded-xl max-w-lg w-full p-6 shadow-xl max-h-[90vh] flex flex-col">
                        <div className="flex justify-between items-center mb-4">
                            <h2 className="text-xl font-bold text-gray-900">
                                Edit Project
                            </h2>
                            <button
                                onClick={() => setEditingProject(null)}
                                className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
                            >
                                <X size={20} className="text-gray-500" />
                            </button>
                        </div>

                        {/* Tabs */}
                        <div className="flex border-b border-gray-200 mb-6">
                            <button
                                onClick={() => setActiveTab('general')}
                                className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors flex items-center gap-2 ${activeTab === 'general'
                                        ? 'border-green-600 text-green-600'
                                        : 'border-transparent text-gray-500 hover:text-gray-700'
                                    }`}
                            >
                                <Settings size={16} />
                                General
                            </button>
                            <button
                                onClick={() => setActiveTab('collaborators')}
                                className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors flex items-center gap-2 ${activeTab === 'collaborators'
                                        ? 'border-green-600 text-green-600'
                                        : 'border-transparent text-gray-500 hover:text-gray-700'
                                    }`}
                            >
                                <Users size={16} />
                                Collaborators
                            </button>
                        </div>

                        <div className="flex-1 overflow-y-auto">
                            {activeTab === 'general' ? (
                                <form onSubmit={handleSubmit} className="space-y-4">
                                    <div>
                                        <label className="block text-sm font-medium text-gray-700 mb-1">Project Name</label>
                                        <input
                                            className="w-full border border-gray-300 rounded-lg p-2.5 focus:ring-2 focus:ring-green-500 focus:border-green-500 outline-none transition"
                                            value={formData.name}
                                            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                                            required
                                        />
                                    </div>
                                    <div>
                                        <label className="block text-sm font-medium text-gray-700 mb-1">Client</label>
                                        <input
                                            className="w-full border border-gray-300 rounded-lg p-2.5 focus:ring-2 focus:ring-green-500 focus:border-green-500 outline-none transition"
                                            value={formData.client}
                                            onChange={(e) => setFormData({ ...formData, client: e.target.value })}
                                            required
                                        />
                                    </div>
                                    <div>
                                        <label className="block text-sm font-medium text-gray-700 mb-1">Job Number</label>
                                        <input
                                            className="w-full border border-gray-300 rounded-lg p-2.5 focus:ring-2 focus:ring-green-500 focus:border-green-500 outline-none transition"
                                            value={formData.job_number}
                                            onChange={(e) => setFormData({ ...formData, job_number: e.target.value })}
                                            required
                                        />
                                    </div>
                                    <div>
                                        <label className="block text-sm font-medium text-gray-700 mb-1">Model Name (optional)</label>
                                        <input
                                            className="w-full border border-gray-300 rounded-lg p-2.5 focus:ring-2 focus:ring-green-500 focus:border-green-500 outline-none transition"
                                            value={formData.model_name}
                                            onChange={(e) => setFormData({ ...formData, model_name: e.target.value })}
                                        />
                                    </div>
                                    <div>
                                        <label className="block text-sm font-medium text-gray-700 mb-1">Description (optional)</label>
                                        <textarea
                                            className="w-full border border-gray-300 rounded-lg p-2.5 focus:ring-2 focus:ring-green-500 focus:border-green-500 outline-none transition"
                                            rows={3}
                                            value={formData.description}
                                            onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                                        />
                                    </div>
                                    <div className="flex justify-end gap-3 pt-4 border-t border-gray-100">
                                        <button
                                            type="button"
                                            onClick={() => setEditingProject(null)}
                                            className="px-4 py-2 text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
                                        >
                                            Cancel
                                        </button>
                                        <button
                                            type="submit"
                                            disabled={updateProject.isPending}
                                            className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors disabled:opacity-50 flex items-center"
                                        >
                                            {updateProject.isPending && <Loader2 className="animate-spin mr-2" size={16} />}
                                            Save Changes
                                        </button>
                                    </div>
                                </form>
                            ) : (
                                <CollaboratorsPanel
                                    collaborators={collaborators}
                                    isLoading={loadingCollabs}
                                    isOwner={isOwner ?? false}
                                    onAdd={handleAddCollaborator}
                                    onRemove={handleRemoveCollaborator}
                                    isAdding={addCollaborator.isPending}
                                    accentColor="green"
                                />
                            )}
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default VerificationProjectList;
