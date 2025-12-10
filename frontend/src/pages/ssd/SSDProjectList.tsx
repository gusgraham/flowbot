import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { useSSDProjects, useCreateSSDProject, useUpdateSSDProject, useDeleteSSDProject } from '../../api/hooks';
import { Container, ArrowRight, Loader2, Plus, X, Pencil, Trash2 } from 'lucide-react';

const SSDProjectList: React.FC = () => {
    const { data: projects, isLoading, error } = useSSDProjects();
    const createProject = useCreateSSDProject();
    const updateProject = useUpdateSSDProject();
    const deleteProject = useDeleteSSDProject();

    const [isModalOpen, setIsModalOpen] = useState(false);
    const [editingId, setEditingId] = useState<number | null>(null);

    // Form state
    const [formData, setFormData] = useState({
        name: '',
        client: '',
        job_number: '',
        description: ''
    });

    const handleCreateClick = () => {
        setEditingId(null);
        setFormData({ name: '', client: '', job_number: '', description: '' });
        setIsModalOpen(true);
    };

    const handleEditClick = (e: React.MouseEvent, project: any) => {
        e.preventDefault();
        setFormData({
            name: project.name,
            client: project.client,
            job_number: project.job_number,
            description: project.description || ''
        });
        setEditingId(project.id);
        setIsModalOpen(true);
    };

    const handleDeleteClick = async (e: React.MouseEvent, project: any) => {
        e.preventDefault();
        if (window.confirm(`Are you sure you want to delete "${project.name}"?\n\nWARNING: This will permanently delete all associated data and files. This action cannot be undone.`)) {
            try {
                await deleteProject.mutateAsync(project.id);
            } catch (err) {
                console.error("Failed to delete project:", err);
                alert("Failed to delete project. Please try again.");
            }
        }
    };

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();

        if (editingId) {
            // Update existing
            updateProject.mutate({ id: editingId, data: formData }, {
                onSuccess: () => {
                    setIsModalOpen(false);
                    setEditingId(null);
                    setFormData({ name: '', client: '', job_number: '', description: '' });
                }
            });
        } else {
            // Create new
            createProject.mutate(formData, {
                onSuccess: () => {
                    setIsModalOpen(false);
                    setFormData({ name: '', client: '', job_number: '', description: '' });
                }
            });
        }
    };

    const isSubmitting = createProject.isPending || updateProject.isPending;

    if (isLoading) {
        return (
            <div className="flex justify-center items-center h-64">
                <Loader2 className="animate-spin text-orange-500" size={32} />
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
                    <h1 className="text-2xl font-bold text-gray-900">Spill Storage Design</h1>
                    <p className="text-gray-500 mt-1">Calculate required tank volumes to meet spill frequency targets.</p>
                </div>
                <button
                    onClick={handleCreateClick}
                    className="bg-orange-600 text-white px-4 py-2 rounded-lg hover:bg-orange-700 transition-colors flex items-center"
                >
                    <Plus size={20} className="mr-2" />
                    New Project
                </button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {projects?.map((project) => (
                    <Link
                        key={project.id}
                        to={`/ssd/${project.id}`}
                        className="block bg-white border border-gray-200 rounded-xl p-6 hover:shadow-md transition-shadow group relative"
                    >
                        <div className="flex items-start justify-between mb-4">
                            <div className="p-3 bg-orange-50 text-orange-600 rounded-lg">
                                <Container size={24} />
                            </div>

                            <div className="flex items-center gap-2">
                                <span className="text-xs font-medium bg-gray-100 text-gray-600 px-2 py-1 rounded-full">
                                    {project.job_number}
                                </span>

                                <div className="flex gap-1">
                                    <button
                                        onClick={(e) => handleEditClick(e, project)}
                                        className="p-1 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded transition-colors"
                                        title="Edit Project"
                                    >
                                        <Pencil size={14} />
                                    </button>
                                    <button
                                        onClick={(e) => handleDeleteClick(e, project)}
                                        className="p-1 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded transition-colors"
                                        title="Delete Project"
                                    >
                                        {deleteProject.isPending && deleteProject.variables === project.id ? (
                                            <Loader2 size={14} className="animate-spin" />
                                        ) : (
                                            <Trash2 size={14} />
                                        )}
                                    </button>
                                </div>
                            </div>
                        </div>

                        <h3 className="text-lg font-bold text-gray-900 mb-1">{project.name}</h3>
                        <p className="text-sm text-gray-500 mb-4">{project.client}</p>

                        <div className="flex items-center text-orange-600 text-sm font-medium">
                            Open Dashboard
                            <ArrowRight size={16} className="ml-1 group-hover:translate-x-1 transition-transform" />
                        </div>
                    </Link>
                ))}

                {projects?.length === 0 && (
                    <div className="col-span-full text-center py-12 bg-gray-50 rounded-xl border border-dashed border-gray-300">
                        <p className="text-gray-500 mb-4">No SSD projects found.</p>
                        <button
                            onClick={handleCreateClick}
                            className="text-orange-600 font-medium hover:text-orange-700"
                        >
                            Create your first project
                        </button>
                    </div>
                )}
            </div>

            {/* Create/Edit Project Modal */}
            {isModalOpen && (
                <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
                    <div className="bg-white rounded-xl max-w-md w-full p-6 shadow-xl">
                        <div className="flex justify-between items-center mb-6">
                            <h2 className="text-xl font-bold text-gray-900">
                                {editingId ? 'Edit SSD Project' : 'New SSD Project'}
                            </h2>
                            <button
                                onClick={() => setIsModalOpen(false)}
                                className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
                            >
                                <X size={20} className="text-gray-500" />
                            </button>
                        </div>
                        <form onSubmit={handleSubmit} className="space-y-4">
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">Project Name</label>
                                <input
                                    className="w-full border border-gray-300 rounded-lg p-2.5 focus:ring-2 focus:ring-orange-500 focus:border-orange-500 outline-none transition"
                                    placeholder="e.g. Beech Ave CSO Analysis"
                                    value={formData.name}
                                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                                    required
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">Client</label>
                                <input
                                    className="w-full border border-gray-300 rounded-lg p-2.5 focus:ring-2 focus:ring-orange-500 focus:border-orange-500 outline-none transition"
                                    placeholder="e.g. Yorkshire Water"
                                    value={formData.client}
                                    onChange={(e) => setFormData({ ...formData, client: e.target.value })}
                                    required
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">Job Number</label>
                                <input
                                    className="w-full border border-gray-300 rounded-lg p-2.5 focus:ring-2 focus:ring-orange-500 focus:border-orange-500 outline-none transition"
                                    placeholder="e.g. J12345"
                                    value={formData.job_number}
                                    onChange={(e) => setFormData({ ...formData, job_number: e.target.value })}
                                    required
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">Description (optional)</label>
                                <textarea
                                    className="w-full border border-gray-300 rounded-lg p-2.5 focus:ring-2 focus:ring-orange-500 focus:border-orange-500 outline-none transition"
                                    placeholder="Brief description of the project..."
                                    rows={3}
                                    value={formData.description}
                                    onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                                />
                            </div>
                            <div className="flex justify-end gap-3 pt-4 border-t border-gray-100">
                                <button
                                    type="button"
                                    onClick={() => setIsModalOpen(false)}
                                    className="px-4 py-2 text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
                                >
                                    Cancel
                                </button>
                                <button
                                    type="submit"
                                    disabled={isSubmitting}
                                    className="px-4 py-2 bg-orange-600 text-white rounded-lg hover:bg-orange-700 transition-colors disabled:opacity-50 flex items-center"
                                >
                                    {isSubmitting && <Loader2 className="animate-spin mr-2" size={16} />}
                                    {editingId ? 'Save Changes' : 'Create Project'}
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </div>
    );
};

export default SSDProjectList;
