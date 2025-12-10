import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import {
    useWQProjects, useUpdateWQProject,
    useWqProjectCollaborators, useAddWqCollaborator, useRemoveWqCollaborator,
    useCurrentUser
} from '../../api/hooks';
import { ArrowLeft, Droplets, Loader2, Pencil, X, Settings, Users, FileSpreadsheet, Upload, BarChart2 } from 'lucide-react';
import CollaboratorsPanel from '../../components/CollaboratorsPanel';

interface WaterQualityProject {
    id: number;
    name: string;
    client: string;
    job_number: string;
    campaign_date?: string;
    description?: string;
    owner_id?: number;
}

const WQDashboard: React.FC = () => {
    const { projectId } = useParams<{ projectId: string }>();
    const id = parseInt(projectId || '0');

    const { data: projects, isLoading } = useWQProjects();
    const project = projects?.find((p: WaterQualityProject) => p.id === id);

    const updateProject = useUpdateWQProject();
    const { data: currentUser } = useCurrentUser();

    const [isEditModalOpen, setIsEditModalOpen] = useState(false);
    const [activeTab, setActiveTab] = useState<'general' | 'collaborators'>('general');

    // Form state for editing
    const [formData, setFormData] = useState({
        name: '',
        client: '',
        job_number: '',
        campaign_date: '',
        description: ''
    });

    // Collaborator hooks
    const { data: collaborators, isLoading: loadingCollabs } = useWqProjectCollaborators(id);
    const addCollaborator = useAddWqCollaborator();
    const removeCollaborator = useRemoveWqCollaborator();

    const isOwner = currentUser?.is_superuser || currentUser?.role === 'Admin';

    // Update form when project changes
    useEffect(() => {
        if (project) {
            setFormData({
                name: project.name || '',
                client: project.client || '',
                job_number: project.job_number || '',
                campaign_date: project.campaign_date ? project.campaign_date.split('T')[0] : '',
                description: project.description || ''
            });
        }
    }, [project]);

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        if (!project) return;

        updateProject.mutate({ id: project.id, data: formData }, {
            onSuccess: () => {
                setIsEditModalOpen(false);
            }
        });
    };

    const handleAddCollaborator = async (username: string) => {
        if (!id) return;
        await addCollaborator.mutateAsync({ projectId: id, username });
    };

    const handleRemoveCollaborator = (userId: number) => {
        if (!id) return;
        removeCollaborator.mutate({ projectId: id, userId });
    };

    if (isLoading) {
        return (
            <div className="flex justify-center items-center h-64">
                <Loader2 className="animate-spin text-cyan-500" size={32} />
            </div>
        );
    }

    if (!project) {
        return (
            <div className="p-8 text-center">
                <p className="text-gray-500">Project not found</p>
                <Link to="/wq" className="text-cyan-600 hover:underline mt-2 inline-block">
                    Back to Projects
                </Link>
            </div>
        );
    }

    return (
        <div className="max-w-6xl mx-auto">
            {/* Header */}
            <div className="mb-8">
                <Link to="/wq" className="inline-flex items-center text-sm text-gray-500 hover:text-gray-900 mb-4">
                    <ArrowLeft size={16} className="mr-1" /> Back to Projects
                </Link>

                <div className="flex justify-between items-start">
                    <div>
                        <div className="flex items-center gap-3 mb-2">
                            <div className="p-2 bg-cyan-50 text-cyan-600 rounded-lg">
                                <Droplets size={24} />
                            </div>
                            <h1 className="text-3xl font-bold text-gray-900">
                                {project.name}
                            </h1>
                            <span className="px-3 py-1 bg-cyan-100 text-cyan-800 text-sm font-medium rounded-full">
                                {project.job_number}
                            </span>
                        </div>
                        <p className="text-gray-500">{project.client}</p>
                        {project.campaign_date && (
                            <p className="text-sm text-gray-400 mt-1">
                                Campaign: {new Date(project.campaign_date).toLocaleDateString()}
                            </p>
                        )}
                    </div>

                    <button
                        onClick={() => setIsEditModalOpen(true)}
                        className="flex items-center gap-2 px-3 py-1.5 text-sm text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors"
                    >
                        <Pencil size={16} />
                        Edit Project
                    </button>
                </div>
            </div>

            {/* Placeholder Content */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Main Content */}
                <div className="lg:col-span-2 space-y-6">
                    <div className="bg-white border border-gray-200 rounded-xl p-6 shadow-sm">
                        <h2 className="text-xl font-bold text-gray-900 mb-4 flex items-center gap-2">
                            <Upload size={20} className="text-cyan-600" />
                            Data Import
                        </h2>
                        <div className="bg-gray-50 border border-dashed border-gray-300 rounded-lg p-8 text-center">
                            <FileSpreadsheet size={48} className="mx-auto text-gray-300 mb-4" />
                            <p className="text-gray-500 mb-2">Water Quality data import coming soon</p>
                            <p className="text-sm text-gray-400">Upload lab results and field measurements</p>
                        </div>
                    </div>

                    <div className="bg-white border border-gray-200 rounded-xl p-6 shadow-sm">
                        <h2 className="text-xl font-bold text-gray-900 mb-4 flex items-center gap-2">
                            <BarChart2 size={20} className="text-cyan-600" />
                            Analysis
                        </h2>
                        <div className="bg-gray-50 border border-dashed border-gray-300 rounded-lg p-8 text-center">
                            <BarChart2 size={48} className="mx-auto text-gray-300 mb-4" />
                            <p className="text-gray-500 mb-2">Water Quality analysis coming soon</p>
                            <p className="text-sm text-gray-400">View trends, correlations, and statistics</p>
                        </div>
                    </div>
                </div>

                {/* Sidebar */}
                <div className="space-y-6">
                    <div className="bg-white border border-gray-200 rounded-xl p-6 shadow-sm">
                        <h3 className="font-bold text-gray-900 mb-4">Project Details</h3>
                        <div className="space-y-3 text-sm">
                            <div className="flex justify-between">
                                <span className="text-gray-500">Client</span>
                                <span className="font-medium text-gray-900">{project.client}</span>
                            </div>
                            <div className="flex justify-between">
                                <span className="text-gray-500">Job Number</span>
                                <span className="font-medium text-gray-900">{project.job_number}</span>
                            </div>
                            {project.campaign_date && (
                                <div className="flex justify-between">
                                    <span className="text-gray-500">Campaign Date</span>
                                    <span className="font-medium text-gray-900">
                                        {new Date(project.campaign_date).toLocaleDateString()}
                                    </span>
                                </div>
                            )}
                            {project.description && (
                                <div className="pt-2 border-t border-gray-100">
                                    <span className="text-gray-500 block mb-1">Description</span>
                                    <p className="text-gray-700">{project.description}</p>
                                </div>
                            )}
                        </div>
                    </div>

                    <div className="bg-cyan-50 border border-cyan-200 rounded-xl p-6">
                        <h3 className="font-bold text-cyan-900 mb-2">Module Status</h3>
                        <p className="text-sm text-cyan-700">
                            The Water Quality module is under development. Core features will include:
                        </p>
                        <ul className="text-sm text-cyan-600 mt-2 space-y-1">
                            <li>• Lab result import (CSV/Excel)</li>
                            <li>• Parameter visualization</li>
                            <li>• Flow correlation analysis</li>
                            <li>• Export to report templates</li>
                        </ul>
                    </div>
                </div>
            </div>

            {/* Edit Project Modal */}
            {isEditModalOpen && (
                <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
                    <div className="bg-white rounded-xl max-w-lg w-full p-6 shadow-xl max-h-[90vh] flex flex-col">
                        <div className="flex justify-between items-center mb-4">
                            <h2 className="text-xl font-bold text-gray-900">
                                Edit Project
                            </h2>
                            <button
                                onClick={() => setIsEditModalOpen(false)}
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
                                    ? 'border-cyan-600 text-cyan-600'
                                    : 'border-transparent text-gray-500 hover:text-gray-700'
                                    }`}
                            >
                                <Settings size={16} />
                                General
                            </button>
                            <button
                                onClick={() => setActiveTab('collaborators')}
                                className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors flex items-center gap-2 ${activeTab === 'collaborators'
                                    ? 'border-cyan-600 text-cyan-600'
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
                                            className="w-full border border-gray-300 rounded-lg p-2.5 focus:ring-2 focus:ring-cyan-500 focus:border-cyan-500 outline-none transition"
                                            value={formData.name}
                                            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                                            required
                                        />
                                    </div>
                                    <div>
                                        <label className="block text-sm font-medium text-gray-700 mb-1">Client</label>
                                        <input
                                            className="w-full border border-gray-300 rounded-lg p-2.5 focus:ring-2 focus:ring-cyan-500 focus:border-cyan-500 outline-none transition"
                                            value={formData.client}
                                            onChange={(e) => setFormData({ ...formData, client: e.target.value })}
                                            required
                                        />
                                    </div>
                                    <div>
                                        <label className="block text-sm font-medium text-gray-700 mb-1">Job Number</label>
                                        <input
                                            className="w-full border border-gray-300 rounded-lg p-2.5 focus:ring-2 focus:ring-cyan-500 focus:border-cyan-500 outline-none transition"
                                            value={formData.job_number}
                                            onChange={(e) => setFormData({ ...formData, job_number: e.target.value })}
                                            required
                                        />
                                    </div>
                                    <div>
                                        <label className="block text-sm font-medium text-gray-700 mb-1">Campaign Date (optional)</label>
                                        <input
                                            type="date"
                                            className="w-full border border-gray-300 rounded-lg p-2.5 focus:ring-2 focus:ring-cyan-500 focus:border-cyan-500 outline-none transition"
                                            value={formData.campaign_date}
                                            onChange={(e) => setFormData({ ...formData, campaign_date: e.target.value })}
                                        />
                                    </div>
                                    <div>
                                        <label className="block text-sm font-medium text-gray-700 mb-1">Description (optional)</label>
                                        <textarea
                                            className="w-full border border-gray-300 rounded-lg p-2.5 focus:ring-2 focus:ring-cyan-500 focus:border-cyan-500 outline-none transition"
                                            rows={3}
                                            value={formData.description}
                                            onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                                        />
                                    </div>
                                    <div className="flex justify-end gap-3 pt-4 border-t border-gray-100">
                                        <button
                                            type="button"
                                            onClick={() => setIsEditModalOpen(false)}
                                            className="px-4 py-2 text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
                                        >
                                            Cancel
                                        </button>
                                        <button
                                            type="submit"
                                            disabled={updateProject.isPending}
                                            className="px-4 py-2 bg-cyan-600 text-white rounded-lg hover:bg-cyan-700 transition-colors disabled:opacity-50 flex items-center"
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
                                    accentColor="blue"
                                />
                            )}
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default WQDashboard;
